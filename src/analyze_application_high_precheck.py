"""Read-only audit of six high-dimensional resource calls, not optimization."""
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main():
    config = json.loads((ROOT / 'configs/application_high_precheck.json').read_text('utf-8'))
    source = ROOT / config['out']
    summary = json.loads((source / 'summary.json').read_text('utf-8'))
    frozen = json.loads((ROOT / config['freeze_manifest']).read_text('utf-8'))
    assert summary['config'] == config and summary['frozen_sources'] == frozen
    assert all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == value for name, value in frozen.items())
    assert summary['objective_calls'] == 6 and summary['cv_fold_solves'] == 30 and summary['test_method_calls'] == 0
    assert summary['resource_only'] and not summary['formal_application_result']
    assert not summary['full_optimizer_resource_check_complete']
    events = [json.loads(v) for v in (source / 'events.jsonl').read_text('utf-8').splitlines()]
    assert len(events) == 13 and events[0]['event'] == 'meta'
    assert events[0]['config'] == config and events[0]['frozen_sources'] == frozen
    assert events[0]['data_hashes'] == summary['data_hashes'] and events[0]['fold_hash'] == summary['fold_hash']
    assert set(summary['data_hashes']) == {'X_train', 'y_train', 'X_test', 'y_test'}
    assert all(len(v) == 64 and int(v, 16) >= 0 for v in [summary['fold_hash'], *summary['data_hashes'].values()])
    labels = []
    for t, (pre, label, level) in enumerate(zip(events[1::2], events[2::2], config['points']), 1):
        assert pre['event'] == 'pre' and label['event'] == 'label' and pre['t'] == label['t'] == t
        assert pre['n_observed'] == t - 1 and 'y' not in pre
        np.testing.assert_array_equal(pre['x'], np.full(300, level))
        assert np.isfinite(label['y']) and label['y'] >= 0
        assert np.isfinite(label['evaluation_seconds']) and label['evaluation_seconds'] >= 0
        assert label['evaluation_seconds'] == summary['evaluation_seconds'][t-1]
        labels.append(label['y'])
    assert labels[2] == labels[5] and summary['deterministic_repeated_point']
    assert summary['process_peak_working_set_bytes'] > 0
    assert np.isclose(summary['subsequent_evaluation_seconds_median'], np.median(summary['evaluation_seconds'][1:]))
    out = ROOT / 'results/application_high_precheck_analysis_v1'; out.mkdir(parents=True, exist_ok=True)
    result = dict(objective_calls=6, cv_fold_solves=30, test_method_calls=0, complete_resource_point_design=True,
                  full_optimizer_resource_check_complete=False, formal_application_result=False,
                  source_hashes_verified=True, raw_file_sha256={name: hashlib.sha256((source / name).read_bytes()).hexdigest()
                                                               for name in ['events.jsonl', 'summary.json']})
    (out / 'audit.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('Six-call resource audit passed. Full optimizer resource checks and 160 formal runs remain incomplete.')


if __name__ == '__main__':
    main()
