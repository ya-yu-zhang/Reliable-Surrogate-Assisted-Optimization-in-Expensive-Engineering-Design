"""Independent validation integrity checks; no label generation or statistics."""
import os
for key in ['OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ[key] = '1'
from dataclasses import asdict
import hashlib
import itertools
import json
from pathlib import Path
import numpy as np
from .core import Settings
from .experiment import code_hash

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source = ROOT/'results/mechanism_validation_v1'
    diag = ROOT/'results/mechanism_validation_diagnostics_v1'
    status = json.loads((ROOT/'results/mechanism_validation_status.json').read_text('utf-8'))
    assert status['stage'] == 'complete', 'Wait for frozen pipeline completion before audit.'
    freeze = json.loads((ROOT/'docs/frozen_mechanism_validation_v1/sha256.json').read_text('utf-8'))
    assert all(digest(ROOT/row['Path']).upper() == row['SHA256'] for row in freeze)
    manifest = json.loads((source/'manifest.json').read_text('utf-8'))
    config = json.loads((ROOT/'configs/mechanism_validation.json').read_text('utf-8'))
    assert manifest['config'] == config and manifest['hash'] == code_hash()
    assert manifest['settings'] == asdict(Settings())
    expected = set(itertools.product(config['functions'], config['dimensions'], config['instances'],
                                    range(config['repeats']), config['methods']))
    files = sorted(source.glob('*/summary.json')); assert len(files) == len(expected) == 3888
    assert not json.loads((source/'failures.json').read_text('utf-8'))
    seen, hashes, initialization = set(), [], {}
    charged, extra, states, duplicate_calls, capped_fits = 0, 0, 0, 0, 0
    ordering_disagreements = []
    for index, file in enumerate(files, 1):
        summary = json.loads(file.read_text('utf-8')); sig = summary['signature']
        key = tuple(sig[k] for k in ['fid', 'dim', 'instance', 'rep', 'method'])
        assert key in expected and key not in seen; seen.add(key)
        dim, budget = sig['dim'], sig['budget']; n0, ntrain = 2*dim+20, dim+10
        seed = 100000*dim+1000*sig['fid']+10*sig['instance']+sig['rep']
        assert sig['seed'] == summary['seed'] == seed and budget == 10*dim
        assert sig['code_hash'] == manifest['hash'] and sig['settings'] == manifest['settings']
        assert sig['capture'] == 'checkpoints' and summary['n0'] == n0
        events_file = file.parent/'events.jsonl'
        events = [json.loads(v) for v in events_file.read_text('utf-8').splitlines()]
        assert len(events) == 1+2*budget
        meta, pre, labels = events[0], events[1::2], events[2::2]
        assert meta['event'] == 'meta' and all(meta[k] == v for k, v in sig.items())
        checkpoints = sorted(set(max(n0+1, int(np.ceil(budget*f))) for f in [.25, .5, .75, 1]))
        assert meta['checkpoints'] == checkpoints
        lb, ub = np.asarray(meta['lb']), np.asarray(meta['ub'])
        assert lb.shape == ub.shape == (dim,) and np.all(lb == -5) and np.all(ub == 5)
        best, stagnation, ys, xs = np.inf, 0, [], []
        for t, (a, b) in enumerate(zip(pre, labels), 1):
            assert a['event'] == 'pre' and b['event'] == 'label' and a['t'] == b['t'] == t
            assert a['n_observed'] == t-1 and 'y' not in a and 'best_after' not in a
            assert a['best_before'] == (None if t == 1 else best)
            x, u = np.asarray(a['x']), np.asarray(a['x_unit'])
            assert x.shape == u.shape == (dim,) and np.isfinite(x).all() and np.isfinite(u).all()
            assert np.all((u >= 0) & (u <= 1)) and np.allclose(x, lb+(ub-lb)*u, atol=1e-13, rtol=0)
            assert np.isfinite(b['y'])
            if t <= ntrain:
                assert a['mode'] == 'initial_train' and a['mu'] is None and a['H'] is None
                assert not a['declared'] and not a['monitoring_ready']
            else:
                assert np.isfinite([a['mu'], a['H'], a['scale'], a['margin'], a['neff']]).all()
                assert a['scale'] > 0 and a['margin'] >= 0 and a['neff'] >= 0
                assert a['H'] == a['mu']+a['scale']*a['margin']
                assert a['monitoring_ready'] == (t-1-ntrain >= 20)
                indices = a['train_indices']
                assert len(indices) == len(set(indices)) == min(t-1, 256)
                assert all(isinstance(j, int) and 0 <= j < t-1 for j in indices)
                capped_fits += t-1 > 256
                assert a['stagnation'] == stagnation
                assert b['residual'] == (b['y']-a['mu'])/a['scale']
                assert b['upper_failure'] == (b['y'] > a['H'])
                threshold = best-1e-6*a['scale']
                assert a['declared'] == bool(a['monitoring_ready'] and a['support'] and a['H'] < threshold)
                assert b['false_claim'] == bool(a['declared'] and b['y'] >= threshold)
                assert not b['false_claim'] or b['upper_failure']
                assert b['significant_improvement'] == (b['y'] < threshold)
                assert b['improvement'] == max(0, best-b['y'])
                stagnation = 0 if b['significant_improvement'] else stagnation+1
                assert (a['mode'] == 'startup') == (t <= n0)
                if t > n0:
                    assert a['mode'] in ['pool_random', 'explore', 'upper', 'mean']
                    assert 0 <= a['selection_index'] < 256 and 0 <= a['mode_uniform'] < 1
                    assert a['candidate_stream'] == [seed, 21, t] and a['sobol_stream'] == [seed, 22, t]
            best = min(best, b['y']); assert b['best_after'] == best
            ys.append(b['y']); xs.append(u)
        assert summary['algorithm_evaluations'] == budget and summary['diagnostic_evaluations'] == 0
        assert summary['best'] == best and summary['error'] == max(best-summary['optimum'], 0)
        init = max(min(ys[:n0])-summary['optimum'], 1e-12)
        assert summary['initial_error'] == init
        assert summary['log_relative_error'] == float(np.log10(max(summary['error']/init, 1e-12)))
        init_signature = [(a['x_unit'], b['y'], a['mu']) for a, b in zip(pre, labels)][:n0]
        problem = key[:-1]
        if problem in initialization: assert initialization[problem] == init_signature
        else: initialization[problem] = init_signature
        duplicate_calls += budget-len(np.unique(np.asarray(xs), axis=0))
        archive_file = file.parent/'candidate_pools.npz'
        with np.load(archive_file, allow_pickle=False) as archive:
            assert set(archive.files) == {f't{t}_{k}' for t in checkpoints for k in ['points', 'mu', 'H']}
            for t in checkpoints:
                a = pre[t-1]; k = a['selection_index']
                pool, mu, bound = (archive[f't{t}_{name}'] for name in ['points', 'mu', 'H'])
                assert pool.shape == (256, dim) and mu.shape == bound.shape == (256,)
                assert np.isfinite(pool).all() and np.isfinite(mu).all() and np.isfinite(bound).all()
                assert np.all((pool >= 0) & (pool <= 1)) and len(np.unique(pool, axis=0)) == 256
                assert np.array_equal(pool[k], a['x_unit']) and mu[k] == a['mu'] and bound[k] == a['H']
        h = {'runid': summary['runid'], 'journal': digest(events_file),
             'summary': digest(file), 'candidate_archive': digest(archive_file)}
        if sig['method'] in ['greedy', 'fixed03', 'pool_random']:
            directory = diag/file.parent.name
            count = json.loads((directory/'count.json').read_text('utf-8'))
            assert count['manifest']['source_hash'] == h['journal'] and count['manifest']['fixed'] == .3
            assert count['algorithm_evaluations'] == budget and count['diagnostic_evaluations'] == 1024 and count['states'] == 4
            decisions = [json.loads(v) for v in (directory/'decisions_before_diagnostic_labels.jsonl').read_text('utf-8').splitlines()]
            assert [v['t'] for v in decisions] == checkpoints and all(v['n_observed'] == v['t']-1 for v in decisions)
            with np.load(directory/'hidden_labels.npz', allow_pickle=False) as hidden:
                assert set(hidden.files) == {f't{t}_y' for t in checkpoints}
                for record in decisions:
                    values = hidden[f't{record["t"]}_y']
                    assert values.shape == (256,) and np.isfinite(values).all()
                    assert set(record['decisions']) == {'G', 'T', 'S', 'ST'}
                    for variant, rules in record['decisions'].items():
                        assert set(rules) == {'mean', 'fixed', 'upper', 'feedback', 'max_distance'}
                        assert all(0 <= rule['k'] < 256 for rule in rules.values())
                        if variant in ['G', 'T'] and rules['mean']['k'] != rules['upper']['k']:
                            ordering_disagreements.append(dict(runid=summary['runid'], t=record['t'],
                                variant=variant, mean=rules['mean']['k'], upper=rules['upper']['k']))
            h['diagnostic_archive'] = digest(directory/'hidden_labels.npz')
            h['diagnostic_pre'] = digest(directory/'decisions_before_diagnostic_labels.jsonl')
            extra += 1024; states += 4
        charged += budget; hashes.append(h)
        if index % 200 == 0: print(f'Integrity audit {index}/3888', flush=True)
    assert seen == expected and charged == 907200 and extra == 1990656 and states == 7776
    out = ROOT/'results/mechanism_validation_analysis_v1'
    (out/'full_integrity_audit.json').write_text(json.dumps(dict(runs=len(seen),
        algorithm_evaluations=charged, diagnostic_evaluations=extra, states=states,
        exact_duplicate_calls=duplicate_calls, fits_with_training_truncation=capped_fits,
        complete_cartesian_design=True, frozen_sources_unchanged=True,
        original_signed_residuals_verified=True, paid_prefix_and_pre_information_verified=True,
        candidates_and_predictions_match_selection=True,
        diagnostic_G_T_upper_mean_equal=not ordering_disagreements,
        diagnostic_G_T_ordering_disagreements=ordering_disagreements), indent=2), encoding='utf-8')
    (out/'full_source_hashes.json').write_text(json.dumps(hashes, indent=2), encoding='utf-8')
    print('Full independent integrity audit passed.', flush=True)


if __name__ == '__main__':
    main()
