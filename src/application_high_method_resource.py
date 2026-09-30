"""Full 1000-call high-dimensional resource run; no test-set metric call."""
import os
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:
    os.environ[key] = '1'
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
from .application_methods import PaidObjective, execute
from .application_precheck import array_hash
from .experiment import json_line
from .solo_cost import memory_peak
from .application_high_precheck import prerequisite
from .run_solo_cost import process_inventory

ROOT = Path(__file__).resolve().parents[1]
CONFIG = 'configs/application_high_method_resource.json'


def design():
    config = json.loads((ROOT / CONFIG).read_text('utf-8'))
    frozen = json.loads((ROOT / config['freeze_manifest']).read_text('utf-8'))
    assert CONFIG in frozen
    assert all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == value for name, value in frozen.items())
    runtime = json.loads((ROOT / config['runtime_manifest']).read_text('utf-8'))
    assert sys.version.split()[0] == runtime['python_version']
    assert all(importlib.metadata.version(name) == value for name, value in runtime['packages'].items())
    assert config['dataset'] == 'synt_high' and config['dimension'] == 300
    assert config['budget'] == 1000 and config['data_seed'] == 90043 and config['rep'] == 0
    assert config['methods'] == ['greedy','fixed01','PEM_T','PEM_ST','sobol','cma_es','gp_ei','turbo_1']
    assert config['n_splits'] == 5 and config['tol_level'] == 1e-4 and config['test_size'] == .15
    assert config['test_method_calls'] == 0 and config['formal_application_result'] is False
    return config, frozen, runtime


def phase_one_complete():
    audit = json.loads((ROOT / 'results/application_high_precheck_analysis_v1/audit.json').read_text('utf-8'))
    assert audit['complete_resource_point_design'] and audit['source_hashes_verified']
    assert audit['objective_calls'] == 6 and audit['test_method_calls'] == 0
    source = ROOT / 'results/application_high_precheck_v1'
    for name, value in audit['raw_file_sha256'].items():
        assert hashlib.sha256((source / name).read_bytes()).hexdigest() == value
    return json.loads((source / 'summary.json').read_text('utf-8'))


class TimedJournal:
    def __init__(self, stream, timing, start):
        self.stream, self.timing, self.start = stream, timing, start
    def write(self, text):
        result = self.stream.write(text)
        event = json.loads(text)
        if event['event'] == 'label':
            json_line(self.timing, dict(event='completed_paid_evaluation', t=event['t'],
                                       cumulative_seconds=perf_counter()-self.start))
        return result
    def flush(self):
        self.stream.flush()


def run(method):
    phase_one = phase_one_complete()  # No source directory or constructor before this gate.
    prerequisite()
    assert not any(p['ProcessId'] not in [os.getpid(), os.getppid()] and
                   '-m src.application_high_method_resource' in (p['CommandLine'] or '')
                   for p in process_inventory()), 'Another resource worker is active; serial design required'
    config, frozen, runtime = design()
    assert method in config['methods']
    dim, budget = config['dimension'], config['budget']
    seed = 100000*dim + 1000*config['dataset_id'] + 10*config['data_seed']
    directory = ROOT / config['out'] / method
    if directory.exists():
        raise RuntimeError('Resource run exists; driver must audit cache, never overwrite or replay it')
    from LassoBench import SyntheticBenchmark
    directory.mkdir(parents=True)
    warning_counts = Counter()
    with warnings.catch_warnings():
        warnings.simplefilter('always')
        def record(message, category, filename, lineno, file=None, line=None):
            warning_counts[category.__name__ + ': ' + str(message)[:200]] += 1
        warnings.showwarning = record
        start = perf_counter()
        benchmark = SyntheticBenchmark(pick_bench='synt_high', noise=False, seed=config['data_seed'],
                                       n_splits=5, tol_level=1e-4, test_size=.15)
        construction = perf_counter()-start
        assert benchmark.n_features == dim
        data = {name: array_hash(getattr(benchmark, name)) for name in ['X_train','y_train','X_test','y_test']}
        folds = [(a.tolist(), b.tolist()) for a, b in benchmark.kf.split(benchmark.X_train)]
        fold_hash = hashlib.sha256(json.dumps(folds).encode()).hexdigest()
        assert data == phase_one['data_hashes'] and fold_hash == phase_one['fold_hash']
        def evaluate(point):
            try:
                value = float(benchmark.evaluate(point))
                if not np.isfinite(value) or value < 0:
                    raise FloatingPointError('Invalid paid author validation loss: '+repr(value))
                return value
            except Exception as error:
                (directory/'failed_paid_attempt.json').write_text(json.dumps(dict(
                    physical_call_attempted=True,charged_attempt=oracle.calls,x=np.asarray(point).tolist(),
                    error_type=type(error).__name__,error=str(error)),indent=2),encoding='utf-8')
                raise
        oracle = PaidObjective(evaluate, np.full(dim,-1.), np.full(dim,1.), budget)
        signature = dict(dataset='synt_high', dim=dim, rep=0, method=method, budget=budget,
                         data_seed=config['data_seed'], seed=seed, packages=runtime['packages'], frozen_sources=frozen)
        start = perf_counter()
        with (directory / 'events.jsonl').open('w',encoding='utf-8') as stream, (directory / 'timing.jsonl').open(
                'w',encoding='utf-8') as timing, zipfile.ZipFile(directory / 'candidate_pools.npz','w',
                compression=zipfile.ZIP_DEFLATED,compresslevel=1) as archive:
            journal = TimedJournal(stream, timing, start)
            json_line(journal,dict(event='meta',schema=1,**signature,data_hashes=data,fold_hash=fold_hash,
                                  optimum_known=False,resource_only=True))
            extra = execute(oracle,dim,seed,method,journal,archive,config['capture'])
        optimization = perf_counter()-start
        assert oracle.calls == len(oracle.values) == len(oracle.points) == budget
        assert np.isfinite(oracle.values).all() and np.all(np.asarray(oracle.values) >= 0)
        index = int(np.argmin(oracle.values))
    summary = dict(signature=signature, algorithm_evaluations=budget, cv_fold_solves=5*budget,
                   diagnostic_evaluations=0,test_method_calls=0,formal_application_result=False,resource_only=True,
                   optimum_known=False,best_validation_loss=oracle.values[index],best_evaluation=index+1,
                   best_config=oracle.points[index].tolist(),data_hashes=data,fold_hash=fold_hash,
                   benchmark_construction_seconds=construction,optimization_seconds=optimization,
                   objective_seconds=oracle.objective_seconds,process_peak_working_set_bytes=memory_peak(),
                   warning_counts=dict(warning_counts),shared_load_timing_not_exclusive=True,
                   exact_duplicate_calls=budget-len(np.unique(np.asarray(oracle.points),axis=0)),**extra)
    (directory / 'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False),encoding='utf-8')
    print(method + ': 1000 paid resource evaluations complete; test calls 0',flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--method',required=True)
    run(parser.parse_args().method)
