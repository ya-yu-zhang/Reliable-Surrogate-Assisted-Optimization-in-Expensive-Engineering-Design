"""Strict-budget external GP references, isolated from PEM histories."""
import os
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:
    os.environ[key]='1'
import argparse
from collections import Counter
import ctypes
import hashlib
import importlib.metadata
import json
from pathlib import Path
import pickle
import sys
from time import perf_counter
import warnings
import numpy as np
import ioh
from scipy.optimize import minimize
from scipy.spatial.distance import cdist
from scipy.stats import norm, qmc
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern
import torch

ROOT=Path(__file__).resolve().parents[1]
AUTHOR=ROOT/'literature/source-code/TuRBO'
torch.set_num_threads(1)
torch.set_num_interop_threads(1)
torch.use_deterministic_algorithms(True)


def code_hash():
    h=hashlib.sha256(Path(__file__).read_bytes())
    for name in ['turbo_1.py','gp.py','utils.py','__init__.py']:
        file=AUTHOR/'turbo'/name
        h.update(name.encode());h.update(file.read_bytes())
    return h.hexdigest()


def memory_peak():
    if sys.platform=='win32':
        class Counters(ctypes.Structure):
            _fields_=[('cb',ctypes.c_uint32),('PageFaultCount',ctypes.c_uint32)]+[(name,ctypes.c_size_t) for name in
                      ['PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage',
                       'QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage']]
        counters=Counters();counters.cb=ctypes.sizeof(counters)
        get_handle=ctypes.windll.kernel32.GetCurrentProcess;get_handle.restype=ctypes.c_void_p
        get_memory=ctypes.windll.psapi.GetProcessMemoryInfo
        get_memory.argtypes=[ctypes.c_void_p,ctypes.POINTER(Counters),ctypes.c_uint32]
        assert get_memory(get_handle(),ctypes.byref(counters),counters.cb)
        return int(counters.PeakWorkingSetSize)
    return None


class BudgetExhausted(Exception):
    pass


class BudgetJournal:
    def __init__(self,objective,budget,lb,ub,journal):
        self.objective=objective;self.budget=budget;self.lb=np.asarray(lb);self.ub=np.asarray(ub)
        self.journal=journal;self.points=[];self.values=[];self.state=lambda:{}
        self.objective_seconds=0.;self.last_end=perf_counter();self.prepare_seconds=[]
    def write(self,item):
        self.journal.write(json.dumps(item,allow_nan=False)+'\n');self.journal.flush()
    def __call__(self,x):
        if len(self.values)>=self.budget:
            raise BudgetExhausted
        x=np.asarray(x,dtype=float)
        if not np.isfinite(x).all() or np.any(x<self.lb) or np.any(x>self.ub):
            raise FloatingPointError('Nonfinite or out-of-bounds proposal')
        t=len(self.values)+1
        prepare=perf_counter()-self.last_end;self.prepare_seconds.append(prepare)
        self.write(dict(event='pre',t=t,n_observed=t-1,x=x.tolist(),
                        x_unit=((x-self.lb)/(self.ub-self.lb)).tolist(),
                        best_before=min(self.values) if self.values else None,optimizer_state=self.state(),
                        numpy_rng_hash=hashlib.sha256(pickle.dumps(np.random.get_state())).hexdigest(),
                        torch_rng_hash=hashlib.sha256(torch.get_rng_state().numpy().tobytes()).hexdigest(),
                        preparation_seconds=prepare))
        start=perf_counter();value=float(self.objective(x.tolist()));self.objective_seconds+=perf_counter()-start
        if not np.isfinite(value):raise FloatingPointError('Nonfinite objective')
        self.points.append(x.copy());self.values.append(value)
        self.write(dict(event='label',t=t,y=value,best_after=min(self.values)))
        self.last_end=perf_counter()
        return value


def expected_improvement(mu,sd,best):
    mu,sd=np.asarray(mu),np.asarray(sd)
    improvement=best-mu
    z=np.divide(improvement,sd,out=np.zeros_like(improvement),where=sd>1e-15)
    return np.where(sd>1e-15,improvement*norm.cdf(z)+sd*norm.pdf(z),np.maximum(improvement,0))


def gp_ei(oracle,dim,seed):
    design=qmc.LatinHypercube(dim,seed=seed).random(2*dim)
    for k,point in enumerate(design):
        oracle.state=lambda k=k:dict(mode='initial_lhs',index=k)
        oracle(oracle.lb+(oracle.ub-oracle.lb)*point)
    kernel=ConstantKernel(1.,(.05,20))*Matern(np.full(dim,.2),(.005,2.),nu=2.5)
    while len(oracle.values)<oracle.budget:
        t=len(oracle.values)+1
        xx=(np.array(oracle.points)-oracle.lb)/(oracle.ub-oracle.lb);yy=np.array(oracle.values)
        model=GaussianProcessRegressor(kernel=kernel,alpha=1e-6,normalize_y=True,n_restarts_optimizer=0,random_state=seed)
        model.fit(xx,yy);kernel=model.kernel_
        sequence=qmc.Sobol(dim,scramble=True,seed=np.random.default_rng(np.random.SeedSequence([seed,721,t]))).random_base2(12)
        sequence=sequence[cdist(sequence,xx).min(axis=1)>=1e-10]
        if not len(sequence):raise RuntimeError('No distinct GP-EI candidates')
        mu,sd=model.predict(sequence,return_std=True);scores=expected_improvement(mu,sd,yy.min())
        candidates=list(sequence)
        def acquisition(point):
            m,s=model.predict(np.array([point]),return_std=True)
            return -float(expected_improvement(m,s,yy.min())[0])
        for index in np.argsort(-scores,kind='stable')[:8]:
            result=minimize(acquisition,sequence[index],method='L-BFGS-B',bounds=[(0,1)]*dim,options=dict(maxiter=50))
            if np.isfinite(result.x).all() and np.all((result.x>=0)&(result.x<=1)) and cdist(np.array([result.x]),xx).min()>=1e-10:
                candidates.append(result.x)
        candidates=np.array(candidates);mu,sd=model.predict(candidates,return_std=True)
        scores=expected_improvement(mu,sd,yy.min())
        fallback=bool(np.all(scores<=0));index=int(np.argmax(sd if fallback else scores))
        state=dict(mode='gp_ei' if not fallback else 'variance_fallback',mu=float(mu[index]),sd=float(sd[index]),
                   ei=float(scores[index]),kernel_theta=kernel.theta.tolist(),training_count=len(yy),
                   training_mean=float(yy.mean()),training_scale=float(yy.std()) if yy.std()>0 else 1.,
                   acquisition_candidates=len(candidates),continuous_starts=8)
        oracle.state=lambda state=state:state
        oracle(oracle.lb+(oracle.ub-oracle.lb)*candidates[index])


def turbo(oracle,dim,seed):
    sys.path.insert(0,str(AUTHOR))
    from turbo import Turbo1
    optimizer=Turbo1(f=oracle,lb=oracle.lb,ub=oracle.ub,n_init=2*dim,max_evals=oracle.budget,
                     batch_size=1,verbose=False,use_ard=True,n_training_steps=50,
                     max_cholesky_size=2000,min_cuda=1024,device='cpu',dtype='float64')
    oracle.state=lambda:dict(mode='turbo_author',optimizer_evaluations=optimizer.n_evals,
                             trust_region_length=float(optimizer.length),
                             trust_region_observed=len(optimizer._fX),n_init=optimizer.n_init,
                             candidate_count=optimizer.n_cand)
    stopped=False
    try:optimizer.optimize()
    except BudgetExhausted:stopped=True
    return dict(budget_guard_triggered=stopped,author_internal_evaluations=optimizer.n_evals,
                author_archive_labels=len(optimizer.fX),external_archive_labels=len(oracle.values))


def run_one(fid,dim,instance,rep,method,budget,out):
    seed=100000*dim+1000*fid+10*instance+rep
    runid=f'{method}_f{fid:02}_d{dim}_i{instance}_r{rep}_b{budget}'
    directory=Path(out)/runid;directory.mkdir(parents=True,exist_ok=True)
    signature=dict(fid=fid,dim=dim,instance=instance,rep=rep,method=method,budget=budget,seed=seed,code_hash=code_hash(),
                   packages={p:importlib.metadata.version(p) for p in ['numpy','scipy','ioh','torch','gpytorch','scikit-learn']})
    path=directory/'summary.json'
    if path.exists():
        result=json.loads(path.read_text('utf-8'));assert result['signature']==signature;return result
    objective=ioh.get_problem(fid,dimension=dim,instance=instance,problem_class=ioh.ProblemClass.BBOB)
    np.random.seed(seed);torch.manual_seed(seed)
    warning_counts=Counter();original_show=warnings.showwarning
    start=perf_counter()
    with (directory/'events.jsonl').open('w',encoding='utf-8') as journal,warnings.catch_warnings():
        warnings.simplefilter('always')
        def count_warning(message,category,filename,lineno,file=None,line=None):
            warning_counts[category.__name__+': '+str(message)[:180]]+=1
        warnings.showwarning=count_warning
        oracle=BudgetJournal(objective,budget,objective.bounds.lb,objective.bounds.ub,journal)
        oracle.write(dict(event='meta',**signature,schema=1,author_commit='de0db39f481d9505bb3610b7b7aa0ebf7702e4a5' if method=='turbo_1' else None))
        try:
            extra=turbo(oracle,dim,seed) if method=='turbo_1' else gp_ei(oracle,dim,seed) or {}
        finally:warnings.showwarning=original_show
    assert objective.state.evaluations==len(oracle.values)==budget
    optimum=float(objective.optimum.y);error=max(min(oracle.values)-optimum,0.)
    result=dict(signature=signature,runid=runid,algorithm_evaluations=budget,diagnostic_evaluations=0,
                best=min(oracle.values),error=error,log_absolute_error=float(np.log10(max(error,1e-12))),
                elapsed=perf_counter()-start,objective_seconds=oracle.objective_seconds,
                preparation_seconds=oracle.prepare_seconds,process_peak_working_set_bytes=memory_peak(),
                exact_duplicate_calls=budget-len(np.unique(np.array(oracle.points),axis=0)),
                warning_counts=dict(warning_counts),**extra)
    path.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['runid','algorithm_evaluations','elapsed','process_peak_working_set_bytes']},indent=2),flush=True)
    return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--method',choices=['gp_ei','turbo_1'],required=True)
    ap.add_argument('--fid',type=int,default=1);ap.add_argument('--dim',type=int,required=True)
    ap.add_argument('--instance',type=int,default=4);ap.add_argument('--rep',type=int,default=0)
    ap.add_argument('--budget',type=int);ap.add_argument('--out',required=True);args=ap.parse_args()
    run_one(args.fid,args.dim,args.instance,args.rep,args.method,args.budget or 10*args.dim,args.out)


if __name__=='__main__':main()
