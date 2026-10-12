"""Post-review descriptive replay of existing frozen records; zero physics calls.

No allocator, label, primary protocol or original result is changed. Alternative
orders and the always-tie check are retrospective sensitivity checks, not new
independent or preregistered evidence. All branch observations are charged as in
the original conservative request model, including exact-response cache reads.
"""
from __future__ import annotations
import csv, hashlib, itertools, json, math, struct
from collections import Counter, defaultdict
from pathlib import Path
from .budgeted_decision_audit import Observation, audit, classify

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'paper/engineering_optimization/review_revision'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def completion_capacity(classes, budget, horizon=5):
    """Completed nonbaseline comparisons in the declared full-branch contract.

Each of K exact branch classes costs H+1 requests; the shared baseline must also
finish. No partial certificate or free cross-branch trajectory inference is
allowed. This elementary capacity is NOT a bound on paid solves or other audits.
    """
    if any(not isinstance(x, int) or isinstance(x, bool) for x in [classes, budget, horizon]):
        raise ValueError('Integer class count, request budget and horizon required')
    if classes < 1 or budget < 0 or horizon < 0:
        raise ValueError('Invalid capacity contract')
    return min(classes - 1, max(0, budget // (horizon + 1) - 1))

def point_key(x):
    return struct.pack('<' + 'd' * len(x), *x).hex()

def replay(state, continuation, order, budget, margin, mode='fixed_depth'):
    baseline = state['mapping']['mean']
    if set(order) != set(state['classes']) or len(order) != len(state['classes']):
        raise ValueError('Order must contain every exact class once')
    curves = state['trajectories'][continuation]
    classes = {b: state['classes'][b] for b in order}
    exposed = {b: -1 for b in classes}
    def observe(branch, step):
        if step != exposed[branch] + 1:
            raise AssertionError('Non-prefix observation access')
        exposed[branch] = step
        r = curves[branch][step]
        return Observation(r['incumbent'], r['point_key'])
    result = audit(classes, baseline, observe, state['initial_best'], state['root_sd'],
                   budget=budget, margin=margin, mode=mode)
    initial = state['initial_best']
    truth = {b: classify((curves[baseline][5]['incumbent'] - curve[5]['incumbent']) / initial, margin)
             for b, curve in curves.items()}
    comparisons = []
    for b in classes:
        if b == baseline:
            continue
        name = classes[b][0]
        pred = result['labels'][name]
        endpoint = curves[b][5]['incumbent'] if pred == 'better' else curves[baseline][5]['incumbent']
        comparisons.append({'branch': b, 'representative': name, 'target': truth[b],
            'prediction': pred, 'classified': pred != 'abstain',
            'error': pred != 'abstain' and pred != truth[b],
            'missed_positive': pred == 'abstain' and truth[b] == 'better',
            'missed_worse': pred == 'abstain' and truth[b] == 'worse',
            'pairwise_regret_percent': 100 * (endpoint - min(curves[baseline][5]['incumbent'], curves[b][5]['incumbent'])) / initial})
    chosen = 'mean'
    best = margin
    # Keep the original declared control tie-break, independently of class order.
    for name in ['ei', 'pi', 'lcb']:
        if result['labels'][name] == 'better' and result['effects'][name] > best:
            chosen = name
            best = result['effects'][name]
    endpoint = curves[state['mapping'][chosen]][5]['incumbent']
    oracle = min(c[5]['incumbent'] for c in curves.values())
    observed = {t['point_key'].split(':', 1)[1] for t in result['trace']}
    training = {point_key(x) for x in state['X']}
    return {'result': result, 'comparisons': comparisons,
            'capacity': completion_capacity(len(classes), budget),
            'classified': sum(r['classified'] for r in comparisons),
            'new_to_training_points': len(observed - training),
            'selection_regret_percent': 100 * (endpoint - oracle) / initial}

def csv_write(name, rows):
    with (DEST / name).open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)

def main():
    cfg = json.loads((ROOT / 'configs/engineering_optimization_budget_audit.json').read_text())
    raw = ROOT / cfg['out']
    manifest = json.loads((raw / 'manifest.json').read_text())
    status = json.loads((raw / 'run_status.json').read_text())
    assert status['complete'] and status['completed_blocks'] == cfg['seed_blocks']
    sources = {str((raw / name).relative_to(ROOT)): sha((raw / name).read_bytes())
               for name in ['manifest.json', 'run_status.json']}
    for p, digest in manifest['frozen_files'].items():
        assert sha((ROOT / p).read_bytes()) == digest, p
        sources[p] = digest
    states = []
    for block in cfg['seed_blocks']:
        folder = raw / f'block_{block}'
        complete_path = folder / 'complete.json'
        complete = json.loads(complete_path.read_text())
        assert complete['complete'] and complete['block'] == block
        sources[str(complete_path.relative_to(ROOT))] = sha(complete_path.read_bytes())
        for name, digest in complete['files'].items():
            p = folder / name
            assert sha(p.read_bytes()) == digest, p
            sources[str(p.relative_to(ROOT))] = digest
        for name in complete['states']:
            state = json.loads((folder / (name + '_summary.json')).read_text())
            assert state['complete'] and state['block'] == block
            assert len(state['X']) == 100 and state['initial_best'] > 0
            states.append(state)
    assert len(states) == 30
    published = ROOT / 'paper/engineering_optimization/budget_audit/analysis.json'
    sources[str(published.relative_to(ROOT))] = sha(published.read_bytes())
    old = json.loads(published.read_text())
    order_rows, capacity_rows, block_rows, truth_rows = [], [], [], []
    aggregates = defaultdict(list)
    for state in states:
        baseline = state['mapping']['mean']
        others = [b for b in state['classes'] if b != baseline]
        permutations = list(itertools.permutations(others)) or [()]
        for continuation in cfg['continuations']:
            primary = replay(state, continuation, list(state['classes']), cfg['audit_budget'], cfg['relative_margin'])
            targets = Counter(r['target'] for r in primary['comparisons'])
            truth_rows.append({'block': state['block'], 'state': state['state'], 'source': state['source'],
                'continuation': continuation, 'classes': len(state['classes']),
                'nonbaseline_contrasts': len(others), 'better': targets['better'],
                'tie': targets['tie'], 'worse': targets['worse']})
            for budget in cfg['budget_sensitivity']:
                for margin in cfg['margin_sensitivity']:
                    original = replay(state, continuation, list(state['classes']), budget, margin)
                    reversed_order = [baseline] + list(reversed(others))
                    reverse = replay(state, continuation, reversed_order, budget, margin)
                    adaptive = replay(state, continuation, list(state['classes']), budget, margin, 'adaptive')
                    assert original['classified'] == original['capacity']
                    assert reverse['classified'] == original['capacity']
                    ensembles = [replay(state, continuation, [baseline] + list(order), budget, margin) for order in permutations]
                    common = {'block': state['block'], 'state': state['state'], 'continuation': continuation,
                        'budget': budget, 'margin': margin, 'classes': len(state['classes'])}
                    capacity_rows.append({**common, 'capacity': original['capacity'],
                        'fixed_depth_classified': original['classified'], 'adaptive_classified': adaptive['classified'],
                        'fixed_requests': original['result']['requests'], 'adaptive_requests': adaptive['result']['requests'],
                        'adaptive_uncompleted_requests': sum(t['branch'] != baseline and adaptive['result']['depth'][t['branch']] < 5
                                                           for t in adaptive['result']['trace'])})
                    original_labels = {x['branch']: x['prediction'] for x in original['comparisons']}
                    reversed_labels = {x['branch']: x['prediction'] for x in reverse['comparisons']}
                    order_rows.append({**common, 'all_alternative_orders': len(permutations),
                        'covered_branch_set_changed': {b for b, v in original_labels.items() if v != 'abstain'} !=
                                                       {b for b, v in reversed_labels.items() if v != 'abstain'},
                        'min_classified': min(e['classified'] for e in ensembles),
                        'max_classified': max(e['classified'] for e in ensembles),
                        'min_abstained_worse': min(sum(x['missed_worse'] for x in e['comparisons']) for e in ensembles),
                        'max_abstained_worse': max(sum(x['missed_worse'] for x in e['comparisons']) for e in ensembles),
                        'min_abstained_positive': min(sum(x['missed_positive'] for x in e['comparisons']) for e in ensembles),
                        'max_abstained_positive': max(sum(x['missed_positive'] for x in e['comparisons']) for e in ensembles),
                        'min_selection_regret_percent': min(e['selection_regret_percent'] for e in ensembles),
                        'max_selection_regret_percent': max(e['selection_regret_percent'] for e in ensembles)})
                    for mode, data in [('fixed_depth', original), ('fixed_depth_reversed', reverse), ('adaptive', adaptive)]:
                        aggregates[continuation, budget, margin, mode].append((state, data))
    summary = []
    for (continuation, budget, margin, mode), group in sorted(aggregates.items()):
        comparisons = [x for _, data in group for x in data['comparisons']]
        row = {'continuation': continuation, 'budget': budget, 'margin': margin, 'method': mode,
            'contrasts': len(comparisons), 'classified': sum(r['classified'] for r in comparisons),
            'coverage': sum(r['classified'] for r in comparisons) / len(comparisons),
            'errors': sum(r['error'] for r in comparisons),
            'abstained_positive': sum(r['missed_positive'] for r in comparisons),
            'abstained_worse': sum(r['missed_worse'] for r in comparisons),
            'requests': sum(data['result']['requests'] for _, data in group),
            'new_to_training_points': sum(data['new_to_training_points'] for _, data in group),
            'mean_state_selection_regret_percent': sum(data['selection_regret_percent'] for _, data in group) / 30,
            'completion_capacity': sum(data['capacity'] for _, data in group)}
        if mode != 'fixed_depth_reversed':
            previous = next(r for r in old['sensitivity'] if (r['continuation'], r['budget'], r['margin'], r['method']) ==
                            (continuation, budget, margin, mode))
            assert row['classified'] == previous['classified'] and row['requests'] == previous['total_audit_requests']
            assert row['new_to_training_points'] == previous['total_distinct_new_to_training_points']
            assert math.isclose(row['mean_state_selection_regret_percent'], previous['mean_selection_regret_percent'], abs_tol=1e-12)
        summary.append(row)
        if margin == cfg['relative_margin']:
            for block in cfg['seed_blocks']:
                subset = [(s, data) for s, data in group if s['block'] == block]
                comparisons = [x for _, data in subset for x in data['comparisons']]
                block_rows.append({'block': block, 'continuation': continuation, 'budget': budget,
                    'margin': margin, 'method': mode, 'dependent_states': len(subset),
                    'contrasts': len(comparisons), 'classified': sum(x['classified'] for x in comparisons),
                    'errors': sum(x['error'] for x in comparisons),
                    'requests': sum(d['result']['requests'] for _, d in subset),
                    'selection_regret_percent_mean': sum(d['selection_regret_percent'] for _, d in subset) / len(subset)})
    counts = {c: {key: sum(x[key] for x in truth_rows if x['continuation'] == c) for key in ['better', 'tie', 'worse']}
              for c in cfg['continuations']}
    assert counts == {'mean': {'better': 0, 'tie': 24, 'worse': 1}, 'ei': {'better': 0, 'tie': 23, 'worse': 2}}
    posthoc = [{'continuation': c, 'method': 'always_tie_posthoc_sanity_check', 'contrasts': 25,
                'correct': counts[c]['tie'], 'errors': 25 - counts[c]['tie'], 'requests': 0,
                'target_certified': False, 'preregistered': False} for c in cfg['continuations']]
    mesh_path = ROOT / 'paper/engineering_optimization/paired_mesh/paired_contrasts.csv'
    sources[str(mesh_path.relative_to(ROOT))] = sha(mesh_path.read_bytes())
    mesh = list(csv.DictReader(mesh_path.open()))
    grid_rows = []
    for case in sorted({r['case'] for r in mesh}):
        rr = [r for r in mesh if r['case'] == case and r['horizon'] == '5' and r['target'] == 'fixed_endpoint']
        assert len(rr) == 6
        values = [float(r['relative_advantage_percent']) for r in rr]
        grid_rows.append({'case': case, 'state': rr[0]['state'], 'control': rr[0]['control'],
            'group': rr[0]['group'], 'contexts': len(rr),
            'different_endpoints': rr[0]['mean_point'] != rr[0]['alternative_point'],
            'original_class': rr[0]['original_effect'], 'all_classes_stable': all(r['classification_changed'] == 'False' for r in rr),
            'min_relative_advantage_percent': min(values), 'max_relative_advantage_percent': max(values),
            'decision_margin_percent': 100 * float(rr[0]['margin'])})
    report = {'type': 'retrospective descriptive sensitivity, not new independent validation',
        'development_data_already_observed': True, 'new_physics_attempts': 0,
        'frozen_primary_code_or_labels_modified': False, 'confirmed_original_sensitivity_cells': 36,
        'seed_blocks': 10, 'dependent_states': 30,
        'blocks_with_nonbaseline_contrasts': sorted({s['block'] for s in states if len(s['classes']) > 1}),
        'class_count_distribution': dict(sorted(Counter(len(s['classes']) for s in states).items())),
        'primary_truth_counts': counts, 'posthoc_always_tie': posthoc,
        'capacity_contract': 'min(K-1,max(0,floor(B/(H+1))-1)); full baseline/alternative branches; all prefix/cache reads charged; no early certificate',
        'capacity_is_paid_solver_lower_bound': False, 'capacity_is_novel_theory': False,
        'summaries': summary, 'source_files_sha256': sources,
        'positive_diagnostic_efficacy_validated': False, 'adaptive_advantage_demonstrated': False,
        'engineering_margin_certified': False, 'author_scientific_review_pending': True}
    DEST.mkdir(parents=True, exist_ok=True)
    (DEST / 'analysis.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    for name, rows in [('order_sensitivity.csv', order_rows), ('completion_capacity.csv', capacity_rows),
                       ('budget_comparison.csv', summary), ('seed_block_results.csv', block_rows),
                       ('truth_composition.csv', truth_rows), ('paired_grid_ranges.csv', grid_rows)]:
        csv_write(name, rows)
    print(json.dumps({'states': len(states), 'class_distribution': report['class_count_distribution'],
                      'truth_counts': counts, 'output_files': 7, 'new_physics_attempts': 0}))

if __name__ == '__main__':
    main()
