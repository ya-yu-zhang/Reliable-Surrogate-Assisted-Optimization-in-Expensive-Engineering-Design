"""Frozen 300-dimensional application worker; one test call only after all labels."""
import os
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:
    os.environ[key]='1'
import argparse
from collections import Counter
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
from time import perf_counter
import warnings
import zipfile
import numpy as np
from .application_methods import PaidObjective,execute
from .application_precheck import array_hash
from .experiment import json_line
from .solo_cost import memory_peak

ROOT=Path(__file__).resolve().parents[1]
CONFIG='configs/application_high_formal.json'


def run_one(rep,method):
    config=json.loads((ROOT/CONFIG).read_text('utf-8'))
    frozen=json.loads((ROOT/config['freeze_manifest']).read_text('utf-8'))
    assert CONFIG in frozen and all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==v for n,v in frozen.items())
    runtime=json.loads((ROOT/config['runtime_manifest']).read_text('utf-8'))
    assert sys.version.split()[0]==runtime['python_version']
    assert all(importlib.metadata.version(n)==v for n,v in runtime['packages'].items())
    assert method in config['methods'] and 0<=rep<config['repeats']
    dataset='synt_high';dim=300;budget=1000;data_seed=42
    assert config['datasets']==[dataset] and config['dimensions'][dataset]==dim and config['budgets'][dataset]==budget
    assert budget>=2*dim+20 and config['statistical_tests']==0
    seed=100000*dim+1000*config['dataset_ids'][dataset]+10*data_seed+rep
    runid=f'{method}_{dataset}_r{rep:02}_b{budget}';out=ROOT/config['out']/runid
    signature=dict(dataset=dataset,dim=dim,rep=rep,method=method,budget=budget,data_seed=data_seed,
                   seed=seed,packages=runtime['packages'],frozen_sources=frozen)
    if (out/'summary.json').exists():
        summary=json.loads((out/'summary.json').read_text('utf-8'));assert summary['signature']==signature;return summary
    if out.exists():raise RuntimeError('Incomplete high-dimensional formal run retained; refuse overwrite')
    from LassoBench import SyntheticBenchmark
    out.mkdir(parents=True)
    warning_counts=Counter()
    with warnings.catch_warnings():
        warnings.simplefilter('always')
        def record(message,category,filename,lineno,file=None,line=None):
            warning_counts[category.__name__+': '+str(message)[:200]]+=1
        warnings.showwarning=record
        tick=perf_counter();benchmark=SyntheticBenchmark(pick_bench=dataset,noise=False,seed=data_seed,
            n_splits=5,tol_level=1e-4,test_size=.15);construction=perf_counter()-tick
        assert benchmark.n_features==dim
        data={n:array_hash(getattr(benchmark,n)) for n in ['X_train','y_train','X_test','y_test']}
        folds=[(a.tolist(),b.tolist()) for a,b in benchmark.kf.split(benchmark.X_train)]
        fold_hash=hashlib.sha256(json.dumps(folds).encode()).hexdigest()
        def evaluate(point):
            try:
                value=float(benchmark.evaluate(point))
                if not np.isfinite(value) or value<0:raise FloatingPointError('Invalid validation loss: '+repr(value))
                return value
            except Exception as error:
                (out/'failed_paid_attempt.json').write_text(json.dumps(dict(physical_call_attempted=True,
                    charged_attempt=oracle.calls,x=np.asarray(point).tolist(),error_type=type(error).__name__,
                    error=str(error)),indent=2),encoding='utf-8');raise
        oracle=PaidObjective(evaluate,np.full(dim,-1.),np.full(dim,1.),budget)
        tick=perf_counter()
        with (out/'events.jsonl').open('w',encoding='utf-8') as journal,zipfile.ZipFile(out/'candidate_pools.npz','w',
                compression=zipfile.ZIP_DEFLATED,compresslevel=1) as archive:
            json_line(journal,dict(event='meta',schema=1,**signature,data_hashes=data,fold_hash=fold_hash,
                lb=oracle.lb.tolist(),ub=oracle.ub.tolist(),optimum_known=False,formal_high_extension=True))
            extra=execute(oracle,dim,seed,method,journal,archive,config['capture'])
        optimization=perf_counter()-tick
        assert oracle.calls==len(oracle.values)==budget and np.isfinite(oracle.values).all()
        index=int(np.argmin(oracle.values));best=oracle.points[index]
        tick=perf_counter();metrics={n:float(v) for n,v in benchmark.test(best.copy()).items()};test_seconds=perf_counter()-tick
        assert all(np.isfinite(v) for v in metrics.values())
        post=dict(event='post_completion_test',algorithm_evaluations=budget,selected_evaluation=index+1,
                  selected_config=best.tolist(),best_validation_loss=oracle.values[index],test_method_calls=1,
                  metrics=metrics,optimization_labels_sha256=hashlib.sha256((out/'events.jsonl').read_bytes()).hexdigest())
        (out/'post_completion_test.json').write_text(json.dumps(post,indent=2,allow_nan=False),encoding='utf-8')
    summary=dict(signature=signature,runid=runid,algorithm_evaluations=budget,diagnostic_evaluations=0,
        cv_fold_solves=budget*5,test_method_calls=1,post_completion_test_fits=1,
        best_validation_loss=oracle.values[index],best_evaluation=index+1,best_config=best.tolist(),optimum_known=False,
        test_metrics=metrics,data_hashes=data,fold_hash=fold_hash,benchmark_construction_seconds=construction,
        optimization_seconds=optimization,objective_seconds=oracle.objective_seconds,
        post_completion_test_seconds=test_seconds,process_peak_working_set_bytes=memory_peak(),
        warning_counts=dict(warning_counts),exact_duplicate_calls=budget-len(np.unique(np.asarray(oracle.points),axis=0)),**extra)
    assert 'error' not in summary and 'optimum' not in summary
    (out/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps(dict(runid=runid,algorithm_evaluations=budget,test_method_calls=1),indent=2),flush=True)
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--rep',type=int,required=True);p.add_argument('--method',required=True)
    a=p.parse_args();run_one(a.rep,a.method)
