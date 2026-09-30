"""Full resource-only raw audit and costs; no interim performance comparison."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from .application_journal_audit import audit_journal

ROOT = Path(__file__).resolve().parents[1]


def main():
    config = json.loads((ROOT/'configs/application_high_method_resource.json').read_text('utf-8'))
    source = ROOT/config['out']; status = json.loads((source/'status.json').read_text('utf-8'))
    assert status['stage'] == 'complete' and status['completed'] == status['expected'] == 8
    assert status['failed'] == 0 and status['failure'] is None
    frozen = json.loads((ROOT/config['freeze_manifest']).read_text('utf-8'))
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == value for name,value in frozen.items())
    assert json.loads((source/'manifest.json').read_text('utf-8'))['frozen_sources'] == frozen
    runtime = json.loads((ROOT/config['runtime_manifest']).read_text('utf-8'))
    phase_one = json.loads((ROOT/'results/application_high_precheck_v1/summary.json').read_text('utf-8'))
    assert {f.parent.name for f in source.glob('*/summary.json')} == set(config['methods'])
    rows, hashes = [], {}
    for method in config['methods']:
        directory = source/method; summary = json.loads((directory/'summary.json').read_text('utf-8'))
        sig = summary['signature']
        assert sig == dict(dataset='synt_high',dim=300,rep=0,method=method,budget=1000,
                          data_seed=90043,seed=100000*300+1000*4+10*90043,
                          packages=runtime['packages'],frozen_sources=frozen)
        assert summary['resource_only'] and not summary['formal_application_result'] and summary['test_method_calls'] == 0
        assert not (directory/'post_completion_test.json').exists() and 'test_metrics' not in summary
        assert summary['data_hashes'] == phase_one['data_hashes'] and summary['fold_hash'] == phase_one['fold_hash']
        audit_journal(directory,summary)
        timing = [json.loads(v) for v in (directory/'timing.jsonl').read_text('utf-8').splitlines()]
        assert len(timing) == 1000
        seconds = []
        for t,item in enumerate(timing,1):
            assert item['event'] == 'completed_paid_evaluation' and item['t'] == t
            assert np.isfinite(item['cumulative_seconds']) and item['cumulative_seconds'] >= 0
            seconds.append(item['cumulative_seconds'])
        assert np.all(np.diff(seconds) >= 0) and seconds[-1] <= summary['optimization_seconds']
        assert 0 <= summary['objective_seconds'] <= summary['optimization_seconds']
        assert summary['process_peak_working_set_bytes'] > 0
        row = dict(method=method,algorithm_evaluations=1000,cv_fold_solves=5000,test_method_calls=0,
                   optimization_seconds=summary['optimization_seconds'],objective_seconds=summary['objective_seconds'],
                   peak_memory_gib=summary['process_peak_working_set_bytes']/2**30,
                   warning_count=sum(summary['warning_counts'].values()),
                   exact_duplicate_calls=summary['exact_duplicate_calls'])
        for t in config['cost_checkpoints']:
            row[f'cumulative_seconds_at_{t}'] = seconds[t-1]
        rows.append(row)
        for name in ['summary.json','events.jsonl','candidate_pools.npz','timing.jsonl']:
            path = directory/name; hashes[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    out = ROOT/'results/application_high_method_resource_analysis_v1'; out.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(rows).to_csv(out/'resource_costs.csv',index=False)
    audit = dict(runs=8,algorithm_evaluations=8000,cv_fold_solves=40000,test_method_calls=0,
                 complete_design=True,pre_information_verified=True,bounds_and_management_replayed=True,
                 raw_file_hashes=len(hashes),source_hashes_verified=True,formal_application_result=False,
                 statistical_tests_added=0,shared_load_timing_not_exclusive=True)
    (out/'audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    (out/'source_hashes.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
    print(json.dumps(audit,indent=2))


if __name__ == '__main__':
    main()
