"""One independently budgeted internal/basic/GP run for performance sensitivity."""
import argparse,hashlib,importlib.metadata,json
from pathlib import Path
from time import perf_counter
import numpy as np
import ioh
from scipy.stats import qmc

ROOT=Path(__file__).resolve().parents[1];CONFIG='configs/budget_performance_sensitivity.json'


def basic(fid,dim,instance,rep,method,budget,out):
    import cma
    from .basic_references import fingerprint
    seed=100000*dim+1000*fid+10*instance+rep;runid=f'{method}_f{fid:02}_d{dim}_i{instance}_r{rep}_b{budget}'
    directory=out/runid;directory.mkdir(parents=True,exist_ok=True)
    signature=dict(fid=fid,dim=dim,instance=instance,rep=rep,method=method,budget=budget,seed=seed,
        code_hash=fingerprint(),numpy=importlib.metadata.version('numpy'),scipy=importlib.metadata.version('scipy'),
        cma=importlib.metadata.version('cma'),ioh=importlib.metadata.version('ioh'))
    path=directory/'summary.json'
    if path.exists():
        result=json.loads(path.read_text('utf-8'));assert result['signature']==signature;return result
    objective=ioh.get_problem(fid,dimension=dim,instance=instance,problem_class=ioh.ProblemClass.BBOB)
    lb,ub=np.asarray(objective.bounds.lb),np.asarray(objective.bounds.ub);points=[];values=[];start=perf_counter()
    with (directory/'events.jsonl').open('w',encoding='utf-8') as journal:
        def write(item):journal.write(json.dumps(item,allow_nan=False)+'\n');journal.flush()
        write(dict(event='meta',**signature,lb=lb.tolist(),ub=ub.tolist(),schema=1))
        def evaluate(point,state):
            point=np.asarray(point);assert len(values)<budget and point.shape==(dim,) and np.isfinite(point).all() and np.all((point>=0)&(point<=1))
            x=lb+(ub-lb)*point;t=len(values)+1
            write(dict(event='pre',t=t,n_observed=t-1,x_unit=point.tolist(),x=x.tolist(),best_before=min(values) if values else None,optimizer_state=state))
            value=float(objective(x.tolist()));assert np.isfinite(value);points.append(point.copy());values.append(value)
            write(dict(event='label',t=t,y=value,best_after=min(values)));return value
        if method=='sobol':
            sequence=qmc.Sobol(dim,scramble=True,seed=seed).random_base2(int(np.ceil(np.log2(budget))))
            for k,point in enumerate(sequence[:budget]):evaluate(point,dict(sequence_index=k,scrambled=True))
            settings=dict(scrambled=True,sequence_length=len(sequence))
        else:
            assert method=='cma_es';optimizer=cma.CMAEvolutionStrategy(np.full(dim,.5),.3,dict(bounds=[0,1],seed=seed,verbose=-9,verb_disp=0,verb_log=0));generation=0;partial=0
            while len(values)<budget:
                population=optimizer.ask();available=budget-len(values);ys=[]
                state=dict(generation=generation,mean=optimizer.mean.tolist(),sigma=float(optimizer.sigma),population_size=len(population))
                for j,point in enumerate(population[:available]):ys.append(evaluate(point,dict(**state,individual=j)))
                if len(ys)==len(population):optimizer.tell(population,ys)
                else:partial=len(ys)
                generation+=1
            settings=dict(initial_mean=.5,initial_sigma=.3,bounds=[0,1],default_population=optimizer.popsize,
                ignore_convergence_stop=True,partial_final_generation_evaluations=partial,original_default_updates=True)
    assert objective.state.evaluations==len(values)==budget
    optimum=float(objective.optimum.y);error=max(min(values)-optimum,0.)
    result=dict(signature=signature,runid=runid,settings=settings,best=min(values),error=error,
        log_absolute_error=float(np.log10(max(error,1e-12))),algorithm_evaluations=budget,diagnostic_evaluations=0,
        elapsed=perf_counter()-start,exact_duplicate_calls=len(points)-len(np.unique(np.asarray(points),axis=0)))
    path.write_text(json.dumps(result,indent=2),encoding='utf-8');return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--method',required=True);p.add_argument('--fid',type=int,required=True)
    p.add_argument('--dim',type=int,required=True);p.add_argument('--instance',type=int,required=True);p.add_argument('--rep',type=int,required=True);p.add_argument('--multiplier',type=int,required=True)
    a=p.parse_args();config=json.loads((ROOT/CONFIG).read_text('utf-8'));frozen=json.loads((ROOT/config['freeze_manifest']).read_text('utf-8'))
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==v for n,v in frozen.items())
    assert a.method in config['methods'] and a.fid in config['functions'] and a.dim in config['dimensions']
    assert a.instance in config['instances'] and 0<=a.rep<3 and a.multiplier in [5,10,15]
    budget=a.multiplier*a.dim;out=ROOT/config['out']/f'budget_{a.multiplier}D'/a.method
    if a.method in ['sobol','cma_es']:summary=basic(a.fid,a.dim,a.instance,a.rep,a.method,budget,out)
    elif a.method in ['gp_ei','turbo_1']:
        from .gp_references import run_one;summary=run_one(a.fid,a.dim,a.instance,a.rep,a.method,budget,out)
    else:
        from .experiment import run_one;summary=run_one((a.fid,a.dim,a.instance,a.rep,a.method,budget,str(out),config['capture']))
    assert summary['algorithm_evaluations']==budget
    print(json.dumps(dict(runid=summary['runid'],method=a.method,budget=budget)))


if __name__=='__main__':main()
