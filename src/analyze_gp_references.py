"""Full raw-journal audit of a completed, frozen GP reference batch.

This module deliberately does not import the optimization adapter or Torch.
Auditing cannot generate objective labels, and is valid in the core environment.
External comparisons are descriptive and do not extend the nine-test family.
"""
import argparse
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = {'numpy': '2.2.6', 'scipy': '1.15.3', 'ioh': '0.3.22',
            'torch': '2.5.1+cpu', 'gpytorch': '1.13', 'scikit-learn': '1.7.2'}


def adapter_hash():
    digest = hashlib.sha256((ROOT/'src/gp_references.py').read_bytes())
    for name in ['turbo_1.py', 'gp.py', 'utils.py', '__init__.py']:
        digest.update(name.encode())
        digest.update((ROOT/'literature/source-code/TuRBO/turbo'/name).read_bytes())
    return digest.hexdigest()


def audit_run(file, expected_hash):
    summary = json.loads(file.read_text('utf-8'))
    sig = summary['signature']
    assert sig['code_hash'] == expected_hash and sig['packages'] == PACKAGES
    budget, dim = sig['budget'], sig['dim']
    assert budget == 10*dim
    assert sig['seed'] == 100000*dim+1000*sig['fid']+10*sig['instance']+sig['rep']
    events_file = file.parent/'events.jsonl'
    events = [json.loads(line) for line in events_file.read_text('utf-8').splitlines()]
    assert len(events) == 1+2*budget and events[0]['event'] == 'meta'
    assert all(events[0][key] == value for key, value in sig.items())
    assert events[0]['schema'] == 1
    if sig['method'] == 'turbo_1':
        assert events[0]['author_commit'] == 'de0db39f481d9505bb3610b7b7aa0ebf7702e4a5'
    else:
        assert sig['method'] == 'gp_ei' and events[0]['author_commit'] is None
    best, points, preparation = np.inf, [], []
    for t, (pre, label) in enumerate(zip(events[1::2], events[2::2]), 1):
        assert pre['event'] == 'pre' and label['event'] == 'label'
        assert pre['t'] == label['t'] == t and pre['n_observed'] == t-1
        assert 'y' not in pre and 'best_after' not in pre
        assert pre['best_before'] == (None if t == 1 else best)
        x, u = np.asarray(pre['x']), np.asarray(pre['x_unit'])
        assert x.shape == u.shape == (dim,)
        assert np.isfinite(x).all() and np.isfinite(u).all()
        assert np.all((u >= 0) & (u <= 1)) and np.all((x >= -5) & (x <= 5))
        assert np.allclose(x, -5+10*u, rtol=0, atol=1e-13)
        for name in ['numpy_rng_hash', 'torch_rng_hash']:
            assert len(pre[name]) == 64 and int(pre[name], 16) >= 0
        assert np.isfinite(pre['preparation_seconds']) and pre['preparation_seconds'] >= 0
        state = pre['optimizer_state']
        if sig['method'] == 'gp_ei':
            if t <= 2*dim:
                assert state['mode'] == 'initial_lhs' and state['index'] == t-1
            else:
                assert state['mode'] in ['gp_ei', 'variance_fallback']
                assert state['training_count'] == t-1
                assert len(state['kernel_theta']) == dim+1
                assert state['acquisition_candidates'] >= 1 and state['continuous_starts'] == 8
                assert np.isfinite([state[k] for k in ['mu', 'sd', 'ei', 'training_mean', 'training_scale']]).all()
                assert state['sd'] >= 0 and state['ei'] >= 0 and state['training_scale'] > 0
        else:
            assert state['mode'] == 'turbo_author' and state['n_init'] == 2*dim
            assert state['candidate_count'] == min(100*dim, 5000)
            assert 0 <= state['optimizer_evaluations'] <= t-1
            assert 0 <= state['trust_region_observed'] <= state['optimizer_evaluations']
            assert np.isfinite(state['trust_region_length']) and state['trust_region_length'] > 0
        assert np.isfinite(label['y'])
        best = min(best, label['y'])
        assert label['best_after'] == best
        points.append(x); preparation.append(pre['preparation_seconds'])
    assert summary['algorithm_evaluations'] == budget and summary['diagnostic_evaluations'] == 0
    assert summary['best'] == best and summary['preparation_seconds'] == preparation
    assert np.isfinite(summary['error']) and summary['error'] >= 0
    assert np.isclose(summary['log_absolute_error'], np.log10(max(summary['error'], 1e-12)), atol=1e-12)
    duplicates = budget-len(np.unique(np.asarray(points), axis=0))
    assert summary['exact_duplicate_calls'] == duplicates
    assert 0 <= summary['objective_seconds'] <= summary['elapsed']
    assert summary['process_peak_working_set_bytes'] > 0
    if sig['method'] == 'turbo_1':
        assert summary['external_archive_labels'] == budget
        assert summary['author_archive_labels'] == summary['author_internal_evaluations'] <= budget
        missing = budget-summary['author_archive_labels']
        assert (0 < missing < 2*dim) if summary['budget_guard_triggered'] else missing == 0
    else:
        missing = 0
    row = {key: sig[key] for key in ['fid', 'dim', 'instance', 'rep', 'method', 'seed']}
    row.update({key: summary[key] for key in ['error', 'log_absolute_error', 'elapsed', 'objective_seconds',
                'exact_duplicate_calls', 'process_peak_working_set_bytes', 'algorithm_evaluations']})
    row.update(partial_restart_paid_labels=missing,
               mean_post_initialization_preparation=float(np.mean(preparation[2*dim:])),
               warning_count=sum(summary['warning_counts'].values()))
    return row, summary['warning_counts'], {'runid': summary['runid'],
            'journal_sha256': hashlib.sha256(events_file.read_bytes()).hexdigest(),
            'summary_sha256': hashlib.sha256(file.read_bytes()).hexdigest()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', required=True); ap.add_argument('--out', required=True)
    args = ap.parse_args(); source, out = ROOT/args.source, ROOT/args.out
    manifest = json.loads((source/'manifest.json').read_text('utf-8'))
    config = manifest['config']; status = json.loads((source/'status.json').read_text('utf-8'))
    expected_keys = set(itertools.product(config['functions'], config['dimensions'], config['instances'],
                                         range(config['repeats']), config['methods']))
    expected = len(expected_keys)
    assert status['stage'] == 'complete' and status['completed'] == status['expected'] == expected
    assert status['failed'] == 0 and not json.loads((source/'failures.json').read_text('utf-8'))
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == sha
               for name, sha in manifest['fingerprints'].items())
    files = sorted(source.glob('*/summary.json')); assert len(files) == expected
    rows, hashes, warnings = [], [], Counter()
    expected_hash = adapter_hash()
    for file in files:
        row, counts, digest = audit_run(file, expected_hash)
        rows.append(row); hashes.append(digest); warnings.update(counts)
    frame = pd.DataFrame(rows)
    keys = ['fid', 'dim', 'instance', 'rep', 'method']
    assert not frame.duplicated(keys).any() and set(frame[keys].itertuples(index=False, name=None)) == expected_keys
    charged = int(frame.algorithm_evaluations.sum())
    assert charged == sum(10*key[1] for key in expected_keys)
    out.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out/'runs.csv', index=False)
    instance = frame.groupby(['dim', 'fid', 'instance', 'method']).log_absolute_error.median()
    instance.groupby(['dim', 'fid', 'method']).mean().to_csv(out/'function_log_absolute_errors.csv')
    frame.groupby(['dim', 'fid', 'method']).error.agg(median='median', q25=lambda s:s.quantile(.25),
        q75=lambda s:s.quantile(.75)).to_csv(out/'raw_error_iqr.csv')
    frame.groupby(['dim', 'method']).agg(runs=('fid', 'size'), evaluations=('algorithm_evaluations', 'sum'),
        duplicate_calls=('exact_duplicate_calls', 'sum'), partial_restart_paid_labels=('partial_restart_paid_labels', 'sum'),
        shared_elapsed_median=('elapsed', 'median'), peak_working_set_max=('process_peak_working_set_bytes', 'max'),
        warnings=('warning_count', 'sum')).to_csv(out/'resource_counts.csv')
    audit = dict(audited_runs=expected, algorithm_evaluations=charged, failures=0,
        all_calls_charged=True, no_future_labels_in_pre=True, all_points_in_bounds=True,
        current_source_matches_manifest=True, environment_versions_match=True,
        exact_duplicate_calls=int(frame.exact_duplicate_calls.sum()),
        partial_restart_paid_labels=int(frame.partial_restart_paid_labels.sum()),
        descriptive_only=True, shared_load_timing_not_solo_cost=True,
        adapter_hash=expected_hash, methods=config['methods'])
    (out/'audit.json').write_text(json.dumps(audit, indent=2), encoding='utf-8')
    (out/'source_journal_hashes.json').write_text(json.dumps(hashes, indent=2), encoding='utf-8')
    (out/'warnings.json').write_text(json.dumps(dict(warnings), indent=2), encoding='utf-8')
    print(json.dumps(audit, indent=2))


if __name__ == '__main__':
    main()
