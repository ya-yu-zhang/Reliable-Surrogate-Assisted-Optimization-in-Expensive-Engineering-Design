"""Objective-free audit of callable optimization records and PEM feedback."""
from dataclasses import asdict
import json
import numpy as np
from .core import Settings, METHODS, bounds, management


def audit_journal(directory, summary):
    sig = summary['signature']; dim, budget, method = sig['dim'], sig['budget'], sig['method']
    cfg = Settings()
    events = [json.loads(v) for v in (directory / 'events.jsonl').read_text('utf-8').splitlines()]
    assert len(events) == 1 + 2 * budget and events[0]['event'] == 'meta'
    assert all(events[0][k] == v for k, v in sig.items())
    assert events[0]['optimum_known'] is False and summary['optimum_known'] is False
    assert 'error' not in summary and 'optimum' not in summary
    assert events[0]['data_hashes'] == summary['data_hashes'] and events[0]['fold_hash'] == summary['fold_hash']
    points, labels, residuals, monitors = [], [], [], []
    stagnation = 0
    for t, (pre, label) in enumerate(zip(events[1::2], events[2::2]), 1):
        assert pre['event'] == 'pre' and label['event'] == 'label' and pre['t'] == label['t'] == t
        assert pre['n_observed'] == t-1 and 'y' not in pre and 'test_metrics' not in pre
        assert pre['best_before'] == (min(labels) if labels else None)
        u, x = np.asarray(pre['x_unit']), np.asarray(pre['x'])
        assert u.shape == x.shape == (dim,) and np.isfinite(x).all() and np.isfinite(u).all()
        assert np.all((u >= 0) & (u <= 1)) and np.allclose(x, -1 + 2*u, rtol=0, atol=1e-13)
        y = label['y']; assert np.isfinite(y) and y >= 0
        if method in METHODS:
            if t <= dim+10:
                assert pre['mode'] == 'initial_train'
            else:
                assert pre['mode'] != 'initial_train'
            if pre['mu'] is not None:
                assert np.isfinite(pre['mu']) and pre['scale'] > 0
                assert max(pre['train_indices']) < t-1 and len(pre['train_indices']) <= 256
                variant, manager, _, fixed = METHODS[method]
                bound = bounds(np.array([pre['mu']]), pre['scale'], u[None, :], residuals, t, variant, cfg)
                for field, column in [('H','H'), ('margin','q'), ('neff','neff')]:
                    assert np.isclose(pre[field], bound[column][0], rtol=1e-12, atol=1e-12)
                assert pre['calibrator'] == bound['used'][0] and pre['support'] == bool(bound['support'][0])
                state = management(monitors, stagnation, manager, fixed, cfg)
                assert all(pre[name] == value for name, value in state.items()) and pre['stagnation'] == stagnation
                before = min(labels)
                declared = bool(state['monitoring_ready'] and bound['support'][0] and pre['H'] < before-cfg.tau_factor*pre['scale'])
                assert pre['declared'] == declared
                r = (y-pre['mu'])/pre['scale']; failure = y > pre['H']
                false = bool(declared and y >= before-cfg.tau_factor*pre['scale'])
                significant = y < before-cfg.tau_factor*pre['scale']
                assert label['residual'] == r and label['upper_failure'] == failure and label['false_claim'] == false
                assert label['significant_improvement'] == significant and (not false or failure)
                residuals.append((t, u.copy(), r)); monitors.append((float(failure), pre['margin']))
                stagnation = 0 if significant else stagnation+1
            else:
                assert t <= dim+10
        if method in ['gp_ei','turbo_1']:
            for field in ['numpy_rng_hash','torch_rng_hash']:
                assert len(pre[field]) == 64 and int(pre[field], 16) >= 0
            assert np.isfinite(pre['preparation_seconds']) and pre['preparation_seconds'] >= 0
            state = pre['optimizer_state']
            if method == 'gp_ei':
                if t <= 2*dim:
                    assert state['mode'] == 'initial_lhs' and state['index'] == t-1
                else:
                    assert state['mode'] in ['gp_ei','variance_fallback'] and state['training_count'] == t-1
                    assert len(state['kernel_theta']) == dim+1 and state['continuous_starts'] == 8
                    assert 1 <= state['acquisition_candidates'] <= 4096
            else:
                assert state['mode'] == 'turbo_author' and state['n_init'] == 2*dim
                assert state['candidate_count'] == min(100*dim, 5000)
                assert 0 <= state['trust_region_observed'] <= state['optimizer_evaluations'] <= t-1
        points.append(x); labels.append(y); assert label['best_after'] == min(labels)
    index = int(np.argmin(labels))
    assert summary['algorithm_evaluations'] == budget and summary['cv_fold_solves'] == 5*budget
    assert summary['best_evaluation'] == index+1 and summary['best_validation_loss'] == labels[index]
    assert summary['best_config'] == points[index].tolist()
    assert summary['exact_duplicate_calls'] == budget-len(np.unique(np.array(points), axis=0))
    if method in METHODS:
        assert summary['settings'] == asdict(cfg) and summary['n0'] == 2*dim+20
    with np.load(directory / 'candidate_pools.npz') as pools:
        if method in METHODS:
            checkpoints = summary['checkpoints']
            assert checkpoints == sorted(set(max(2*dim+21, int(np.ceil(budget*f))) for f in [.25,.5,.75,1]))
            assert set(pools.files) == {f't{t}_{v}' for t in checkpoints for v in ['points','mu','H']}
            for t in checkpoints:
                pre = events[2*t-1]; pool = pools[f't{t}_points']; k = pre['selection_index']
                assert pool.shape == (256, dim) and np.isfinite(pool).all() and np.all((pool >= 0) & (pool <= 1))
                np.testing.assert_array_equal(pool[k], pre['x_unit'])
                assert pools[f't{t}_mu'][k] == pre['mu'] and pools[f't{t}_H'][k] == pre['H']
        else:
            assert not pools.files
    return events
