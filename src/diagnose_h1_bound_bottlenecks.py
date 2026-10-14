"""Read-only threshold decomposition of the already recorded H1 certificate.

No solver, physical-bound evaluator, GP fit or future-response reader is used.
This is descriptive development on the frozen relaxed action sets. It is not
a new decision policy, a new engineering trial or an impossibility theorem
for tighter sets or different physical information.
"""
from collections import Counter
import csv
from fractions import Fraction
import hashlib
import json
from pathlib import Path
from statistics import median


def binary(value):
    return Fraction.from_float(float(value))


def threshold_certificate(initial, threshold, pending_lowers, next_lowers):
    """The stored lower-bound certificate passes iff all three terms pass."""
    if not pending_lowers or len(pending_lowers) != len(next_lowers):
        raise ValueError('Expected nonempty matched action terms')
    joint = min(initial, *(min(p, q) for p, q in
                           zip(pending_lowers, next_lowers, strict=True)))
    pending_failed = sum(p < threshold for p in pending_lowers)
    next_failed = sum(q < threshold for q in next_lowers)
    sufficient = initial >= threshold and pending_failed == next_failed == 0
    assert sufficient == (joint >= threshold)
    return joint, pending_failed, next_failed, sufficient


def encode(value):
    return [str(value.numerator), str(value.denominator)]


def run(root):
    root = Path(root)
    folder = root/'results/h1_bound_bottlenecks_20261014'
    folder.mkdir(parents=True, exist_ok=True)
    new = root/'results/gp_envelope_acceleration_20261014/certificates'
    old = root/'gp_attachment/results/engineering_optimization_gp_reachability_v1/construction'
    record = root/'gp_attachment/paper/engineering_optimization/gp_reachability_20261013/branch_results.csv'
    checked = root/'results/gp_envelope_acceleration_20261014/H1_recheck.csv'
    inputs = [record, checked]
    with record.open() as stream:
        source = list(csv.DictReader(stream))
    lookup = {(r['dataset'], r['state'], r['branch'], r['range']): r
              for r in source}
    with checked.open() as stream:
        exact_lookup = {(r['dataset'], r['state'], r['branch'], r['range']): r
                        for r in csv.DictReader(stream)}
    assert len(lookup) == len(source) == 228
    branches, actions, counts, ratios = [], [], Counter(), []
    for path in sorted(new.glob('*.json')):
        prior_path = old/path.name
        inputs += [path, prior_path]
        data = json.loads(path.read_text())
        prior = json.loads(prior_path.read_text())
        assert not data['algorithm_inputs_include_future_response']
        assert not prior['future_responses_exposed']
        meta = data['metadata']
        for branch, modes in data['branches'].items():
            original = prior['branches'][branch]
            assert not original['first_response_exposed']
            for mode, result in modes.items():
                r = lookup[meta['dataset'], meta['state'], branch, mode]
                if r['baseline_branch'] == 'True':
                    continue
                initial = binary(r['initial'])
                threshold = binary(r['completed_H1_baseline'])-binary(r['margin'])*initial
                pending, next_values = [], []
                for i in result['indices']:
                    v = result['exact_intervals'][str(i)][0]
                    lower = Fraction(int(v[0]), int(v[1]))
                    pending_value = max(binary(original['pending_lower']), lower)
                    next_value = binary(prior['raw_pool_lowers'][original['eligible_pool_indices'][i]])
                    pending.append(pending_value)
                    next_values.append(next_value)
                    actions.append({'dataset': meta['dataset'], 'state': meta['state'],
                                    'branch': branch, 'range': mode, 'action': i,
                                    'threshold': str(encode(threshold)),
                                    'pending_term': str(encode(pending_value)),
                                    'next_term': str(encode(next_value)),
                                    'pending_fails': pending_value < threshold,
                                    'next_fails': next_value < threshold})
                joint, pf, nf, sufficient = threshold_certificate(initial, threshold, pending, next_values)
                exact_record = exact_lookup[meta['dataset'], meta['state'], branch, mode]
                assert float(joint) == float(exact_record['exact_joint_lower_float'])
                assert exact_record['category'] == 'abstain' and not sufficient
                counts[mode, 'contrasts'] += 1
                counts[mode, 'pending_blocked'] += pf > 0
                counts[mode, 'next_blocked'] += nf > 0
                counts[mode, 'both_blocked'] += pf > 0 and nf > 0
                counts[mode, 'retained_action_terms'] += len(pending)
                counts[mode, 'pending_terms_below_threshold'] += pf
                counts[mode, 'next_terms_below_threshold'] += nf
                counts[mode, 'no_better_certificates'] += sufficient
                ratio = float(min(next_values)/threshold)
                ratios.append(ratio)
                branches.append({'dataset': meta['dataset'], 'state': meta['state'],
                                 'branch': branch, 'range': mode,
                                 'retained': len(pending), 'pending_failed': pf,
                                 'next_failed': nf, 'no_better_certified': sufficient,
                                 'joint_lower': str(encode(joint)),
                                 'threshold': str(encode(threshold)),
                                 'min_next_over_threshold': ratio})
    assert len(branches) == 142
    for name, rows in [('branch_thresholds.csv', branches), ('action_thresholds.csv', actions)]:
        with (folder/name).open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    summary = {'scientific_baseline': '58f539c2d0738b20c7d0d4889fe8d808a03a3019',
               'analysis_type': 'posthoc decomposition of a fixed relaxed H1 certificate',
               'domains': {mode: {k: v for (m, k), v in counts.items() if m == mode}
                           for mode in ['nonnegative', 'trial_lower']},
               'median_min_next_lower_over_threshold': median(ratios),
               'scope': 'Only the existing fixed action-set lower-bound certificate. Failure is not an inferior true action and not impossibility under stronger sets, coupled coefficients or new physical information.',
               'new_physical_evaluations': 0, 'new_bound_queries': 0,
               'new_independent_optimization_samples': 0, 'remaining_witness_attempts': 0,
               'independent_positive_efficacy_established': False,
               'inputs': [{'path': p.relative_to(root).as_posix(),
                           'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                          for p in inputs]}
    (folder/'analysis.json').write_text(json.dumps(summary, indent=2)+'\n')
    return summary


if __name__ == '__main__':
    result = run(Path(__file__).resolve().parents[1])
    print(json.dumps({k: v for k, v in result.items() if k != 'inputs'}, indent=2))
