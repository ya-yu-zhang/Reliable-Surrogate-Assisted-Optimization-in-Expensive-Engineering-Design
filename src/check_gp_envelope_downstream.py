"""Read-only H1 grading of the new exact intervals using already stored bounds."""
from fractions import Fraction
from pathlib import Path
import csv
import json


def run(root):
    output = root/'results/gp_envelope_acceleration_20261014'
    old = root/'gp_attachment/results/engineering_optimization_gp_reachability_v1/construction'
    report = root/'gp_attachment/paper/engineering_optimization/gp_reachability_20261013'
    original = list(csv.DictReader((report/'branch_results.csv').open()))
    lookup = {(r['dataset'], r['state'], r['branch'], r['range']): r for r in original}
    f = lambda x: Fraction.from_float(float(x))
    rows, state_bounds = [], {}
    for path in sorted((output/'certificates').glob('*.json')):
        data = json.loads(path.read_text()); prior = json.loads((old/path.name).read_text())
        meta = data['metadata']
        for branch, modes in data['branches'].items():
            rec = prior['branches'][branch]
            for mode, result in modes.items():
                previous = lookup[meta['dataset'], meta['state'], branch, mode]
                low = f(meta['initial'])
                for i in result['indices']:
                    encoded = result['exact_intervals'][str(i)][0]
                    response_low = Fraction(int(encoded[0]), int(encoded[1]))
                    point_low = f(prior['raw_pool_lowers'][rec['eligible_pool_indices'][i]])
                    low = min(low, max(f(rec['pending_lower']), response_low), point_low)
                base, initial, margin = (f(previous[k]) for k in ('completed_H1_baseline', 'initial', 'margin'))
                effect_low, effect_high = base-initial, base-low
                eps = margin*initial
                category = ('better' if effect_low > eps else 'worse' if effect_high < -eps else
                            'tie' if effect_low >= -eps and effect_high <= eps else 'abstain')
                assert category == previous['reachable_category']
                state_bounds.setdefault((meta['dataset'], meta['state'], mode), []).append(
                    (previous['baseline_branch'] == 'True', low, base, eps))
                rows.append({'dataset': meta['dataset'], 'state': meta['state'], 'branch': branch,
                             'range': mode, 'exact_joint_lower_float': float(low), 'category': category,
                             'original_category': previous['reachable_category'],
                             'nonbaseline': previous['baseline_branch'] == 'False'})
    certified = sum(all(base <= low+eps for baseline, low, base, eps in values if not baseline)
                    for values in state_bounds.values())
    nonbase = [r for r in rows if r['nonbaseline']]
    assert len(rows) == 228 and len(nonbase) == 142
    assert all(r['category'] == 'abstain' for r in nonbase) and certified == 0
    with (output/'H1_recheck.csv').open('w', newline='') as stream:
        w = csv.DictWriter(stream, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    result = {'branch_range_cases': len(rows), 'nonbaseline_contrasts_per_range': 71,
              'new_categories': 0, 'new_selection_certificates': 0,
              'all_categories_equal_original': True, 'new_physics_attempts': 0,
              'new_bound_queries': 0, 'H5_extension': False}
    (output/'H1_recheck.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    print(json.dumps(run(Path(__file__).resolve().parents[1]), indent=2))
