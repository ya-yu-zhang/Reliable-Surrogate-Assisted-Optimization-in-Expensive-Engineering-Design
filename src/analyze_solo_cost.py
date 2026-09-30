"""Audit a completed serial batch before descriptive cost reporting."""
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .analyze_gp_references import adapter_hash, audit_run

ROOT = Path(__file__).resolve().parents[1]


def main():
    source = ROOT/'results/solo_cost_v1'
    manifest = json.loads((source/'manifest.json').read_text('utf-8'))
    config = manifest['config']
    status = json.loads((source/'status.json').read_text('utf-8'))
    keys = set(itertools.product(config['functions'], config['dimensions'], config['instances'],
                                 range(config['repeats']), config['methods']))
    assert status['stage'] == 'complete' and status['failure'] is None
    assert status['completed'] == status['expected'] == len(keys)
    for name, digest in manifest['fingerprints'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest
    core = hashlib.sha256()
    for name in ['core.py', 'experiment.py']:
        core.update(name.encode()); core.update((ROOT/'src'/name).read_bytes())
    seen, rows, source_hashes = set(), [], {}
    for file in sorted(source.glob('*/measurement.json')):
        record = json.loads(file.read_text('utf-8'))
        key = tuple(record[k] for k in ['fid', 'dim', 'instance', 'rep', 'method'])
        assert key in keys and key not in seen; seen.add(key)
        assert record['fingerprints'] == manifest['fingerprints']
        assert record['wrapper_sha256'] == manifest['fingerprints']['src/solo_cost.py']
        assert record['pre_run_background_cpu_percent'] <= config['max_background_cpu_percent']
        summary_file = file.parent/'summary.json'
        summary = json.loads(summary_file.read_text('utf-8'))
        assert record['summary_sha256'] == hashlib.sha256(summary_file.read_bytes()).hexdigest()
        cost = json.loads((file.parent/'cost.json').read_text('utf-8'))
        assert all(record[k] == v for k,v in cost.items())
        budget, dim = record['budget'], record['dim']
        assert budget == 10*dim == summary['algorithm_evaluations']
        assert summary['diagnostic_evaluations'] == 0
        assert 0 <= summary['elapsed'] <= record['wrapper_execution_seconds'] <= record['end_to_end_seconds']
        assert record['process_peak_working_set_bytes'] > 0
        if record['method'] in ['gp_ei', 'turbo_1']:
            row, _, _ = audit_run(summary_file, adapter_hash())
            duplicates = row['exact_duplicate_calls']; objective_seconds = summary['objective_seconds']
            assert cost['preparation_seconds'] == summary['preparation_seconds']
            assert cost['post_initialization_index'] == 2*dim
        else:
            sig = summary['signature']; assert sig['code_hash'] == core.hexdigest()
            assert sig['capture'] == 'checkpoints'
            assert sig['seed'] == 100000*dim+1000*record['fid']+10*record['instance']+record['rep']
            assert all(sig[k] == record[k] for k in ['fid','dim','instance','rep','method','budget'])
            events = [json.loads(line) for line in (file.parent/'events.jsonl').read_text('utf-8').splitlines()]
            assert len(events) == 1+2*budget and events[0]['event'] == 'meta'
            assert all(events[0][k] == v for k,v in sig.items())
            points, best = [], np.inf
            for t,(pre,label) in enumerate(zip(events[1::2], events[2::2]), 1):
                assert pre['event'] == 'pre' and label['event'] == 'label'
                assert pre['t'] == label['t'] == t and pre['n_observed'] == t-1
                assert pre['best_before'] == (None if t == 1 else best)
                assert 'y' not in pre and 'best_after' not in pre
                u, x = np.asarray(pre['x_unit']), np.asarray(pre['x'])
                assert u.shape == x.shape == (dim,) and np.isfinite(x).all()
                assert np.all((u>=0)&(u<=1)) and np.allclose(x,-5+10*u,rtol=0,atol=1e-13)
                assert np.isfinite(label['y']); best = min(best, label['y'])
                assert label['best_after'] == best; points.append(x)
                if pre['mu'] is not None:
                    assert pre['scale'] > 0 and max(pre['train_indices']) < t-1
                    assert np.isclose(label['residual'], (label['y']-pre['mu'])/pre['scale'])
            assert best == summary['best']
            assert summary['error'] == max(best-summary['optimum'], 0.)
            duplicates = budget-len(np.unique(np.array(points),axis=0))
            objective_seconds = summary['timers']['objective']
            assert cost['post_initialization_index'] == 2*dim+20 == summary['n0']
        preparation = np.array(cost['preparation_seconds'])
        assert preparation.shape == (budget,) and np.isfinite(preparation).all() and np.all(preparation>=0)
        rows.append(dict(fid=record['fid'], dim=dim, rep=record['rep'], method=record['method'],
            algorithm_evaluations=budget, algorithm_seconds=summary['elapsed'],
            objective_seconds=objective_seconds, nonobjective_seconds=summary['elapsed']-objective_seconds,
            end_to_end_seconds=record['end_to_end_seconds'], exact_duplicate_calls=duplicates,
            peak_memory_gib=record['process_peak_working_set_bytes']/2**30,
            mean_post_initialization_preparation=float(np.mean(preparation[cost['post_initialization_index']:])),
            pre_run_background_cpu_percent=record['pre_run_background_cpu_percent']))
        for name in ['measurement.json','cost.json','summary.json','events.jsonl']:
            path = file.parent/name
            source_hashes[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        pool = file.parent/'candidate_pools.npz'
        if pool.exists(): source_hashes[str(pool.relative_to(ROOT))] = hashlib.sha256(pool.read_bytes()).hexdigest()
    assert seen == keys
    out = ROOT/'results/solo_cost_analysis_v1'; out.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows); frame.to_csv(out/'runs.csv', index=False)
    columns = ['algorithm_seconds','end_to_end_seconds','nonobjective_seconds',
               'peak_memory_gib','mean_post_initialization_preparation']
    table = frame.groupby(['dim','method'])[columns].agg(['median','min','max'])
    table.to_csv(out/'descriptive_costs.csv')
    scenarios = []
    for row in rows:
        for seconds in [0,.001,.01,.1,1,10,60]:
            scenarios.append(dict(dim=row['dim'],method=row['method'],rep=row['rep'],
                hypothetical_seconds_per_objective=seconds,
                modeled_algorithm_seconds=row['nonobjective_seconds']+row['algorithm_evaluations']*seconds))
    pd.DataFrame(scenarios).to_csv(out/'objective_cost_scenarios.csv',index=False)
    report = '# 独占成本测量报告\n\n54次预定独立进程运行及12,600次真实评价全部完成。下表为3重复的中位数与最小/最大值，不增加显著性检验。\n\n'
    report += table.round(4).to_markdown()+'\n\n准备时间按各方法自身初始化界限计算，含日志路径开销。真实评价成本情境是假设计算；相同预算不支持评价节省或应用加速声明。\n'
    (ROOT/'docs/独占成本实验报告.md').write_text(report,encoding='utf-8')
    audit = dict(runs=len(rows), algorithm_evaluations=int(frame.algorithm_evaluations.sum()),
                 exact_duplicate_calls=int(frame.exact_duplicate_calls.sum()),
                 complete_design=True, pre_information_verified=True, source_hashes_verified=True,
                 statistical_tests_added=0)
    (out/'integrity_audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    (out/'source_hashes.json').write_text(json.dumps(source_hashes,indent=2),encoding='utf-8')
    print(json.dumps(audit,indent=2))


if __name__ == '__main__':
    main()
