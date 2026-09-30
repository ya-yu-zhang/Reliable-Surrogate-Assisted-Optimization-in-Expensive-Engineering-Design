"""Full-budget application worker; raw validation loss, unknown optimum."""
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
os.environ['LIBSVMDATA_HOME']=str(ROOT/'literature/downloads/libsvm-cache')


def run_one(config_path,dataset,rep,method):
    config_file=(ROOT/config_path).resolve()
    config=json.loads(config_file.read_text('utf-8'))
    frozen=json.loads((ROOT/'docs/frozen_application_formal_v1/sha256.json').read_text('utf-8'))
    assert config_file.relative_to(ROOT).as_posix() in frozen
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest for name,digest in frozen.items())
    runtime=json.loads((ROOT/config['runtime_manifest']).read_text('utf-8'))
    assert sys.version.split()[0]==runtime['python_version']
    assert all(importlib.metadata.version(name)==version for name,version in runtime['packages'].items())
    assert dataset in config['datasets'] and method in config['methods'] and 0<=rep<config['repeats']
    dim=config['dimensions'][dataset];budget=config['budgets'][dataset]
    data_seed=config['data_seed'];seed=100000*dim+1000*config['dataset_ids'][dataset]+10*data_seed+rep
    runid=f'{method}_{dataset}_r{rep:02}_b{budget}'
    out=ROOT/config['out']/runid;out.mkdir(parents=True,exist_ok=True)
    packages=runtime['packages']
    signature=dict(dataset=dataset,dim=dim,rep=rep,method=method,budget=budget,data_seed=data_seed,
                   seed=seed,packages=packages,frozen_sources=frozen)
    summary_file=out/'summary.json'
    if summary_file.exists():
        summary=json.loads(summary_file.read_text('utf-8'));assert summary['signature']==signature;return summary
    if (out/'events.jsonl').exists() or (out/'post_completion_test.json').exists():
        raise RuntimeError('Incomplete scientific run preserved; refuse automatic overwrite or rerun')
    from LassoBench import SyntheticBenchmark,RealBenchmark
    kwargs=dict(seed=data_seed,n_splits=config['n_splits'],tol_level=config['tol_level'],test_size=config['test_size'])
    warnings_count=Counter();tick=perf_counter()
    with warnings.catch_warnings():
        warnings.simplefilter('always')
        def record_warning(message,category,filename,lineno,file=None,line=None):
            warnings_count[category.__name__+': '+str(message)[:200]]+=1
        warnings.showwarning=record_warning
        benchmark=RealBenchmark(pick_data='DNA',**kwargs) if dataset=='DNA' else SyntheticBenchmark(pick_bench=dataset,noise=False,**kwargs)
        construction_seconds=perf_counter()-tick
        assert benchmark.n_features==dim and budget>=2*dim+20
        data_hashes={name:array_hash(getattr(benchmark,name)) for name in ['X_train','y_train','X_test','y_test']}
        folds=[(train.tolist(),validation.tolist()) for train,validation in benchmark.kf.split(benchmark.X_train)]
        fold_hash=hashlib.sha256(json.dumps(folds).encode()).hexdigest()
        oracle=PaidObjective(benchmark.evaluate,np.full(dim,-1.),np.full(dim,1.),budget)
        start=perf_counter()
        with (out/'events.jsonl').open('w',encoding='utf-8') as journal,zipfile.ZipFile(
                out/'candidate_pools.npz','w',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as archive:
            json_line(journal,dict(event='meta',schema=1,**signature,data_hashes=data_hashes,fold_hash=fold_hash,
                lb=oracle.lb.tolist(),ub=oracle.ub.tolist(),optimum_known=False,
                alpha_min=float(benchmark.alpha_min),alpha_max=float(benchmark.alpha_max)))
            extra=execute(oracle,dim,seed,method,journal,archive,config['capture'])
        optimization_seconds=perf_counter()-start
        assert oracle.calls==len(oracle.points)==len(oracle.values)==budget and np.all(np.array(oracle.values)>=0)
        best_index=int(np.argmin(oracle.values));best_config=oracle.points[best_index]
        # One post-completion test only; neither feedback nor hyperparameters can use it.
        test_start=perf_counter();test_metrics=benchmark.test(best_config.copy());test_seconds=perf_counter()-test_start
        test_metrics={name:float(value) for name,value in test_metrics.items()}
        if not all(np.isfinite(value) for value in test_metrics.values()):raise FloatingPointError('Nonfinite post-completion test metric')
        test_record=dict(event='post_completion_test',algorithm_evaluations=oracle.calls,
            selected_evaluation=best_index+1,selected_config=best_config.tolist(),
            best_validation_loss=min(oracle.values),test_method_calls=1,metrics=test_metrics,
            optimization_labels_sha256=hashlib.sha256((out/'events.jsonl').read_bytes()).hexdigest())
        (out/'post_completion_test.json').write_text(json.dumps(test_record,indent=2,allow_nan=False),encoding='utf-8')
    summary=dict(signature=signature,runid=runid,algorithm_evaluations=budget,diagnostic_evaluations=0,
        cv_fold_solves=budget*config['n_splits'],test_method_calls=1,post_completion_test_fits=1,
        best_validation_loss=min(oracle.values),best_evaluation=best_index+1,best_config=best_config.tolist(),
        optimum_known=False,test_metrics=test_metrics,data_hashes=data_hashes,fold_hash=fold_hash,
        benchmark_construction_seconds=construction_seconds,optimization_seconds=optimization_seconds,
        objective_seconds=oracle.objective_seconds,post_completion_test_seconds=test_seconds,
        process_peak_working_set_bytes=memory_peak(),warning_counts=dict(warnings_count),
        exact_duplicate_calls=budget-len(np.unique(np.array(oracle.points),axis=0)),**extra)
    assert 'error' not in summary and 'optimum' not in summary
    summary_file.write_text(json.dumps(summary,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps(dict(runid=runid,algorithm_evaluations=budget,test_method_calls=1,
        optimization_seconds=optimization_seconds),indent=2),flush=True)
    return summary


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',required=True);ap.add_argument('--dataset',required=True)
    ap.add_argument('--rep',type=int,required=True);ap.add_argument('--method',required=True)
    args=ap.parse_args();run_one(args.config,args.dataset,args.rep,args.method)


if __name__=='__main__':main()
