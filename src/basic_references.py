"""Audited Sobol and pycma budget runs; no access to surrogate labels."""
import os
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:
    os.environ[key]='1'
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import importlib.metadata
import json
from pathlib import Path
from time import perf_counter
import traceback
import cma
import ioh
import numpy as np
from scipy.stats import qmc

ROOT=Path(__file__).resolve().parents[1]


def fingerprint():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def run_one(job):
    fid,dim,instance,rep,method,out=job
    budget=10*dim;seed=100000*dim+1000*fid+10*instance+rep
    runid=f'{method}_f{fid:02}_d{dim}_i{instance}_r{rep}_b{budget}'
    directory=Path(out)/runid;directory.mkdir(parents=True,exist_ok=True)
    signature=dict(fid=fid,dim=dim,instance=instance,rep=rep,method=method,budget=budget,seed=seed,
                   code_hash=fingerprint(),numpy=importlib.metadata.version('numpy'),
                   scipy=importlib.metadata.version('scipy'),cma=importlib.metadata.version('cma'),ioh=importlib.metadata.version('ioh'))
    path=directory/'summary.json'
    if path.exists():
        result=json.loads(path.read_text('utf-8'))
        assert result['signature']==signature
        return result
    oracle=ioh.get_problem(fid,dimension=dim,instance=instance,problem_class=ioh.ProblemClass.BBOB)
    lb,ub=np.array(oracle.bounds.lb),np.array(oracle.bounds.ub)
    points=[];values=[];start=perf_counter()
    with (directory/'events.jsonl').open('w',encoding='utf-8') as journal:
        def write(item):
            journal.write(json.dumps(item,allow_nan=False)+'\n');journal.flush()
        write(dict(event='meta',**signature,lb=lb.tolist(),ub=ub.tolist(),schema=1))
        def evaluate(point,state):
            point=np.asarray(point)
            assert len(values)<budget
            assert np.isfinite(point).all() and np.all(point>=0) and np.all(point<=1)
            x=lb+(ub-lb)*point;t=len(values)+1
            write(dict(event='pre',t=t,n_observed=t-1,x_unit=point.tolist(),x=x.tolist(),
                       best_before=min(values) if values else None,optimizer_state=state))
            value=float(oracle(x.tolist()))
            assert np.isfinite(value)
            points.append(point.copy());values.append(value)
            write(dict(event='label',t=t,y=value,best_after=min(values)))
            return value
        if method=='sobol':
            sequence=qmc.Sobol(dim,scramble=True,seed=seed).random_base2(int(np.ceil(np.log2(budget))))
            for k,point in enumerate(sequence[:budget]):
                evaluate(point,dict(sequence_index=k,scrambled=True))
            settings=dict(scrambled=True,sequence_length=len(sequence))
        elif method=='cma_es':
            options=dict(bounds=[0,1],seed=seed,verbose=-9,verb_disp=0,verb_log=0)
            optimizer=cma.CMAEvolutionStrategy(np.full(dim,.5),.3,options)
            generation=0;partial=0
            while len(values)<budget:
                population=optimizer.ask();available=budget-len(values);evaluations=[]
                state=dict(generation=generation,mean=optimizer.mean.tolist(),sigma=float(optimizer.sigma),
                           population_size=len(population))
                for j,point in enumerate(population[:available]):
                    evaluations.append(evaluate(point,dict(**state,individual=j)))
                if len(evaluations)==len(population):
                    optimizer.tell(population,evaluations)
                else:
                    partial=len(evaluations)
                generation+=1
            settings=dict(initial_mean=.5,initial_sigma=.3,bounds=[0,1],default_population=optimizer.popsize,
                          ignore_convergence_stop=True,partial_final_generation_evaluations=partial,
                          original_default_updates=True)
        else:
            raise ValueError(method)
    assert oracle.state.evaluations==len(values)==budget
    optimum=float(oracle.optimum.y);error=max(min(values)-optimum,0.)
    result=dict(signature=signature,runid=runid,settings=settings,best=min(values),error=error,
                log_absolute_error=float(np.log10(max(error,1e-12))),algorithm_evaluations=budget,
                diagnostic_evaluations=0,elapsed=perf_counter()-start,
                exact_duplicate_calls=len(points)-len(np.unique(np.array(points),axis=0)))
    path.write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',required=True);args=ap.parse_args()
    config=json.loads(Path(args.config).read_text('utf-8'))
    out=ROOT/config['out'];out.mkdir(parents=True,exist_ok=True)
    manifest=dict(config=config,code_hash=fingerprint())
    path=out/'manifest.json'
    if path.exists():assert json.loads(path.read_text('utf-8'))==manifest
    path.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    jobs=[(f,d,i,r,m,str(out)) for f in config['functions'] for d in config['dimensions']
          for i in config['instances'] for r in range(config['repeats']) for m in config['methods']]
    failed=[];count=0
    with ProcessPoolExecutor(max_workers=config['workers']) as executor:
        futures={executor.submit(run_one,j):j for j in jobs}
        for future in as_completed(futures):
            count+=1
            try:future.result()
            except Exception:failed.append(dict(job=futures[future],traceback=traceback.format_exc()))
            if count%100==0 or count==len(jobs):print(f'{count}/{len(jobs)} basic references; failed={len(failed)}',flush=True)
    (out/'failures.json').write_text(json.dumps(failed,indent=2),encoding='utf-8')
    if failed:raise SystemExit(1)


if __name__=='__main__':main()
