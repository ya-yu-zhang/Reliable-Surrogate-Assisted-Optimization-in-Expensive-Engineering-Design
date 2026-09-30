"""Six resource-only author evaluations; refuses all unfinished dependencies."""
import os
for key in ['OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ[key] = '1'
from collections import Counter
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
from time import perf_counter
import warnings

import numpy as np
from .application_precheck import array_hash
from .run_solo_cost import process_inventory
from .solo_cost import memory_peak

ROOT = Path(__file__).resolve().parents[1]
CONFIG = 'configs/application_high_precheck.json'


def prerequisite():
    alive = {p['ProcessId'] for p in process_inventory()}
    for name in ['reference_completion_v1', 'application_completion_v1', 'evidence_export_v1']:
        status = json.loads((ROOT / 'results' / name / 'status.json').read_text('utf-8'))
        allowed = ['complete'] if name != 'evidence_export_v1' else ['compiled_pending_visual_review', 'complete']
        assert status['stage'] in allowed and status['failure'] is None, name + ' prerequisite incomplete'
        assert status['pid'] not in alive, name + ' prerequisite still live'
    scientific = ['src.resume_interrupted_gp_batch', 'src.recover_interrupted_run', 'src.run_gp_batch',
                  'src.gp_references', 'src.run_solo_cost', 'src.solo_cost', 'src.run_application_batch',
                  'src.application_experiment', 'src.application_high_precheck', 'src.experiment',
                  'src.diagnostics', 'src.audit_budget_prefix']
    assert not any(p['ProcessId'] != os.getpid() and any('-m ' + m in (p['CommandLine'] or '')
                   for m in scientific) for p in process_inventory()), 'Scientific process still active'
    app_audit = json.loads((ROOT / 'results/application_analysis_v1/audit.json').read_text('utf-8'))
    assert app_audit['complete_design'] and app_audit['pre_information_verified']
    assert app_audit['runs'] == app_audit['post_completion_test_calls'] == 480
    assert app_audit['algorithm_evaluations'] == 240000 and app_audit['cv_fold_solves'] == 1200000
    cost_audit = json.loads((ROOT / 'results/solo_cost_analysis_v1/integrity_audit.json').read_text('utf-8'))
    assert cost_audit['complete_design'] and cost_audit['source_hashes_verified'] and cost_audit['runs'] == 54


def design():
    config = json.loads((ROOT / CONFIG).read_text('utf-8'))
    frozen = json.loads((ROOT / config['freeze_manifest']).read_text('utf-8'))
    assert CONFIG in frozen
    assert all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == value for name, value in frozen.items())
    assert config['dataset'] == 'synt_high' and config['dimension'] == 300 and config['data_seed'] == 90043
    assert config['points'] == [-1, -.5, 0, .5, 1, 0]
    assert config['n_splits'] == 5 and config['tol_level'] == 1e-4 and config['test_size'] == .15
    assert config['formal_budget_feasibility'] == 1000 >= 2 * config['dimension'] + 20
    runtime = json.loads((ROOT / config['runtime_manifest']).read_text('utf-8'))
    assert sys.version.split()[0] == runtime['python_version']
    assert all(importlib.metadata.version(name) == version for name, version in runtime['packages'].items())
    return config, frozen


def main():
    prerequisite()  # Must precede creating scientific files or constructing author data.
    config, frozen = design()
    out = ROOT / config['out']
    if out.exists():
        raise RuntimeError('Resource record already exists; refuse duplicate or incomplete overwrite')
    from LassoBench import SyntheticBenchmark
    values, seconds, warning_counts = [], [], Counter()
    out.mkdir(parents=True)
    with warnings.catch_warnings():
        warnings.simplefilter('always')
        def record(message, category, filename, lineno, file=None, line=None):
            warning_counts[category.__name__ + ': ' + str(message)[:200]] += 1
        warnings.showwarning = record
        start = perf_counter()
        benchmark = SyntheticBenchmark(pick_bench='synt_high', noise=False, seed=config['data_seed'],
                                       n_splits=5, tol_level=1e-4, test_size=.15)
        construction = perf_counter() - start
        assert benchmark.n_features == 300
        data_hashes = {name: array_hash(getattr(benchmark, name))
                       for name in ['X_train', 'y_train', 'X_test', 'y_test']}
        folds = [(a.tolist(), b.tolist()) for a, b in benchmark.kf.split(benchmark.X_train)]
        fold_hash = hashlib.sha256(json.dumps(folds).encode()).hexdigest()
        with (out / 'events.jsonl').open('w', encoding='utf-8') as stream:
            def write(item):
                stream.write(json.dumps(item, allow_nan=False) + '\n'); stream.flush()
            write(dict(event='meta', config=config, frozen_sources=frozen, data_hashes=data_hashes,
                       fold_hash=fold_hash, resource_only=True, optimum_known=False))
            for t, level in enumerate(config['points'], 1):
                assert len(values) < 6
                point = np.full(300, level, dtype=float)
                write(dict(event='pre', t=t, n_observed=len(values), x=point.tolist(), mode='preset_resource_point'))
                start = perf_counter()
                try:
                    value = float(benchmark.evaluate(point))
                except Exception as error:
                    write(dict(event='failed_paid_attempt', t=t, objective_call_attempted=True,
                               error_type=type(error).__name__, error=str(error)))
                    raise
                elapsed = perf_counter() - start
                if not np.isfinite(value) or value < 0:
                    write(dict(event='invalid_returned_label', t=t, objective_call_attempted=True,
                               returned_value_repr=repr(value)))
                    raise FloatingPointError('Invalid paid author validation loss; retain partial record')
                values.append(value); seconds.append(elapsed)
                write(dict(event='label', t=t, y=value, evaluation_seconds=elapsed))
        assert len(values) == 6 and values[2] == values[5], 'Resource repeated point not bitwise deterministic'
    summary = dict(config=config, frozen_sources=frozen, objective_calls=6, cv_fold_solves=30,
                   test_method_calls=0, resource_only=True, formal_application_result=False,
                   full_optimizer_resource_check_complete=False, deterministic_repeated_point=True,
                   construction_seconds=construction, evaluation_seconds=seconds,
                   subsequent_evaluation_seconds_median=float(np.median(seconds[1:])),
                   process_peak_working_set_bytes=memory_peak(), warning_counts=dict(warning_counts),
                   data_hashes=data_hashes, fold_hash=fold_hash,
                   shared_load_timing_not_exclusive=True)
    (out / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print('Six resource evaluations complete; no formal optimization or post-completion test.')


if __name__ == '__main__':
    main()
