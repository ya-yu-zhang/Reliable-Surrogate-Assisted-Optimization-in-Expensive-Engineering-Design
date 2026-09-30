"""Strictly labelled resource-only calls to unchanged author benchmarks."""
import os
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:
    os.environ[key] = '1'
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from time import perf_counter
import warnings

import numpy as np
from .solo_cost import memory_peak

ROOT = Path(__file__).resolve().parents[1]


def array_hash(value):
    if hasattr(value,'tocsr'):
        matrix = value.tocsr()
        return hashlib.sha256(str(matrix.shape).encode()+matrix.data.tobytes()+matrix.indices.tobytes()+matrix.indptr.tobytes()).hexdigest()
    array = np.ascontiguousarray(value)
    return hashlib.sha256(str((array.shape,str(array.dtype))).encode()+array.tobytes()).hexdigest()


def run(dataset):
    config = json.loads((ROOT/'configs/application_precheck.json').read_text('utf-8'))
    assert dataset in config['datasets']
    frozen = json.loads((ROOT/'docs/frozen_application_precheck_v1/sha256.json').read_text('utf-8'))
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest for name,digest in frozen.items())
    directory = ROOT/config['out']/dataset;directory.mkdir(parents=True,exist_ok=True)
    summary_file = directory/'summary.json'
    if summary_file.exists():
        summary = json.loads(summary_file.read_text('utf-8'))
        assert summary['frozen_sources']==frozen; return summary
    from LassoBench import SyntheticBenchmark, RealBenchmark
    kwargs = dict(seed=config['data_seed'],n_splits=config['n_splits'],
                  tol_level=config['tol_level'],test_size=config['test_size'])
    warning_counts = Counter(); values = []; durations = []
    def count_warning(message,category,filename,lineno,file=None,line=None):
        warning_counts[category.__name__+': '+str(message)[:200]] += 1
    with warnings.catch_warnings():
        warnings.simplefilter('always');warnings.showwarning = count_warning
        tick = perf_counter()
        benchmark = RealBenchmark(pick_data='DNA',**kwargs) if dataset=='DNA' else SyntheticBenchmark(pick_bench=dataset,noise=False,**kwargs)
        construction = perf_counter()-tick; dim = benchmark.n_features
        assert dim==config['dimensions'][dataset] and 2*dim+20<=config['formal_budget_feasibility']
        data_hashes = {name:array_hash(getattr(benchmark,name)) for name in ['X_train','y_train','X_test','y_test']}
        folds = [(train.tolist(),validation.tolist()) for train,validation in benchmark.kf.split(benchmark.X_train)]
        fold_hash = hashlib.sha256(json.dumps(folds).encode()).hexdigest()
        with (directory/'events.jsonl').open('w',encoding='utf-8') as journal:
            def write(item):
                journal.write(json.dumps(item,allow_nan=False)+'\n');journal.flush()
            write(dict(event='meta',dataset=dataset,dimension=dim,data_seed=config['data_seed'],
                       config=config,frozen_sources=frozen,data_hashes=data_hashes,fold_hash=fold_hash))
            for level in config['points']:
                if len(values)>=6: raise RuntimeError('Resource objective budget exhausted')
                point = np.full(dim,level);t=len(values)+1
                write(dict(event='pre',t=t,n_observed=len(values),x=point.tolist(),mode='preset_resource_point'))
                tick = perf_counter();value = float(benchmark.evaluate(point));seconds=perf_counter()-tick
                if not np.isfinite(value): raise FloatingPointError('Nonfinite official application objective')
                values.append(value);durations.append(seconds)
                write(dict(event='label',t=t,y=value,evaluation_seconds=seconds))
    assert len(values)==6
    deterministic = values[2]==values[5]
    if not deterministic: raise AssertionError('Repeated official application objective is not deterministic')
    summary = dict(dataset=dataset,dimension=dim,data_seed=config['data_seed'],objective_calls=6,
        cv_fold_solves=6*config['n_splits'],test_method_calls=0,construction_seconds=construction,
        evaluation_seconds=durations,first_evaluation_seconds=durations[0],
        subsequent_evaluation_seconds_median=float(np.median(durations[1:])),
        deterministic_repeated_point=deterministic,process_peak_working_set_bytes=memory_peak(),
        warning_counts=dict(warning_counts),frozen_sources=frozen,data_hashes=data_hashes,fold_hash=fold_hash,
        shared_load_timing_not_exclusive=True,formal_application_result=False)
    summary_file.write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps({k:summary[k] for k in ['dataset','dimension','objective_calls',
        'deterministic_repeated_point','subsequent_evaluation_seconds_median','process_peak_working_set_bytes']},indent=2),flush=True)
    return summary


def main():
    ap = argparse.ArgumentParser();ap.add_argument('--dataset',choices=['synt_simple','synt_medium','DNA'],required=True)
    args = ap.parse_args();run(args.dataset)


if __name__=='__main__':main()
