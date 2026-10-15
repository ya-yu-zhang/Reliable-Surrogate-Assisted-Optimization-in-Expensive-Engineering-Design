"""Read only already paid two-step outcomes after verifying frozen decisions.

No new solver evaluations or model fits.  This is descriptive development
replay, not an independent experiment or an efficacy certificate.
"""
from pathlib import Path
from fractions import Fraction
import csv
import hashlib
import json
import math
import numpy as np
from .verify_and_benchmark_gp_envelope import locate, future_pool

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/direct_rollout_reference_20261015'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run():
    frozen = json.loads((OUT/'decisions_frozen.json').read_text())
    for name, expected in frozen['output_sha256'].items():
        assert digest(OUT/name) == expected
    for name, expected in frozen['inputs_sha256'].items():
        assert digest(ROOT/name) == expected
    assert digest(ROOT/'src/compute_direct_rollout.py') == frozen['source_sha256']
    decisions = json.loads((OUT/'state_decisions.json').read_text())
    models = json.loads((OUT/'conditional_models.json').read_text())
    gp = ROOT/'gp_attachment/results/engineering_optimization_gp_reachability_v1'
    plan = json.loads((gp/'plan.json').read_text())
    status = json.loads((gp/'construction_status.json').read_text())
    constructions = {}
    for name in status['files_sha256']:
        item = json.loads((gp/'construction'/name).read_text())
        constructions[item['metadata']['dataset'], item['metadata']['state']] = item
    inputs = {}
    path = locate(ROOT, 'results/engineering_optimization_common_continuation_v1/events.jsonl')
    inputs[str(path.relative_to(ROOT))] = digest(path)
    common, pending = {}, None
    context = None
    for line in path.open():
        row = json.loads(line)
        if row['event'] == 'meta':
            context = row.get('objective_context')
        elif row['event'] == 'pre':
            pending = row
        elif row['event'] == 'label':
            assert pending is not None
            if row['step'] in (0, 1):
                assert (row['state'], row['branch'], row['step']) == (pending['state'], pending['branch'], pending['step'])
                common[row['state'], row['branch'], row['step']] = {**pending, 'y':row['y']}
            pending = None
    assert context and '100x50' in context
    holdout, pools, initials = {}, {}, {}
    actual = {}
    for model in models:
        dataset, state, branch = (model[k] for k in ('dataset', 'state', 'branch'))
        item = constructions[dataset, state]; meta = item['metadata']
        if (dataset, state) not in pools:
            pool, seed = future_pool(meta, plan['pool_configs'][dataset])
            assert seed == item['pool_seed']
            assert hashlib.sha256(pool.tobytes()).hexdigest() == item['raw_pool_sha256']
            pools[dataset, state] = pool
            source = ('results/engineering_optimization_common_continuation_v1/plans/'+state+'.json'
                      if dataset == 'archived_common_mean' else
                      f"results/engineering_optimization_budget_audit_v1/block_{meta['block']}/{state}_plan.json")
            initials[dataset, state] = json.loads(locate(ROOT, source).read_text())
        initial = initials[dataset, state]
        if dataset == 'archived_common_mean':
            first, second = (common[state, branch, step] for step in (0, 1))
            assert first['observations_before'] == len(initial['y'])
            assert second['observations_before'] == len(initial['y'])+1
        else:
            if state not in holdout:
                path = locate(ROOT, f"results/engineering_optimization_budget_audit_v1/block_{meta['block']}/{state}_summary.json")
                inputs[str(path.relative_to(ROOT))] = digest(path)
                summary = json.loads(path.read_text())
                assert all(np.array_equal(np.array(initial[k]), np.array(summary[k])) for k in ('X','y','theta'))
                assert summary['actions'] == initial['actions']
                holdout[state] = summary
            first, second = holdout[state]['trajectories']['mean'][branch][:2]
            assert first['training_count'] == len(initial['y'])
            assert second['training_count'] == len(initial['y'])+1
            assert first['point_key'].startswith('default100x50:')
            assert second['point_key'].startswith('default100x50:')
            assert second['control'] == 'mean'
        assert first['step'] == 0 and second['step'] == 1
        assert all(math.isfinite(float(r['y'])) and r['y'] > 0 for r in (first, second))
        assert np.array_equal(np.array(first['x']), np.array(initial['actions'][branch]))
        rec = item['branches'][branch]
        candidates = pools[dataset, state][np.array(rec['eligible_pool_indices'])]
        assert second['pool_sha256'] == hashlib.sha256(candidates.tobytes()).hexdigest()
        indices = np.flatnonzero(np.all(candidates == np.array(second['x']), axis=1))
        assert len(indices) == 1
        native_index = int(indices[0]); z = Fraction.from_float(float(first['y']))
        eligible = [cell['index'] for cell in model['nominal_cells']
                    if (cell['lower'] is None or Fraction(cell['lower']) <= z)
                    and (cell['upper'] is None or z <= Fraction(cell['upper']))]
        assert eligible
        nominal_index = min(eligible)
        # Retain mismatches explicitly; no replacement or corrective evaluation.
        actual[dataset, state, branch] = dict(first_response=first['y'], second_response=second['y'],
            nominal_index=nominal_index, actual_next_index=native_index,
            same_selector=nominal_index == native_index,
            terminal=min(meta['initial'], first['y'], second['y']))
    rows = []
    counts = {control:dict(better=0, tie=0, worse=0) for control in ('mean','ei')}
    for decision in decisions:
        key = decision['dataset'], decision['state']; meta = constructions[key]['metadata']
        branches = {control:next(branch for branch, controls in meta['classes'].items() if control in controls)
                    for control in ('mean','ei')}
        assert branches['mean'] == decision['baseline_branch']
        selected = actual[*key, decision['chosen_branch']]
        row = dict(dataset=key[0], state=key[1], chosen_branch=decision['chosen_branch'],
            mean_branch=branches['mean'], ei_branch=branches['ei'], initial=decision['initial'],
            selected_terminal=selected['terminal'],
            selected_first_response=selected['first_response'], selected_second_response=selected['second_response'],
            selected_selector_matches=selected['same_selector'])
        for control, branch in branches.items():
            comparison = actual[*key, branch]
            paired = selected['terminal']-comparison['terminal']
            classification = 'better' if paired < -decision['delta'] else 'worse' if paired > decision['delta'] else 'tie'
            row[control+'_terminal'] = comparison['terminal']
            row['difference_vs_'+control] = paired
            row['relative_difference_vs_'+control] = paired/decision['initial']
            row['category_vs_'+control] = classification
            row[control+'_selector_matches'] = comparison['same_selector']
            counts[control][classification] += 1
        rows.append(row)
    assert len(rows) == 43 and len(actual) == 114
    record = dict(scope='already seen development trajectories, descriptive paired replay only',
        decisions_frozen_sha256=digest(OUT/'decisions_frozen.json'),
        source_sha256=digest(Path(__file__)), inputs_sha256=inputs,
        all_114_first_actions_match=True, all_114_next_pools_match=True,
        all_114_training_counts_match=True, context='default Beams2D 100x50',
        nominal_vs_native_next_action_matches=sum(r['same_selector'] for r in actual.values()),
        comparison='two total physical evaluations per branch, already paid; incumbent included',
        tie_tolerance='1e-6 times each initial incumbent, frozen in DESIGN before replay',
        counts=counts,
        terminal_below_initial_states=sum(r['selected_terminal'] < r['initial']-r['initial']*1e-6 for r in rows),
        selected_mean_relative_change_vs_mean=float(np.mean([r['relative_difference_vs_mean'] for r in rows])),
        selected_median_relative_change_vs_mean=float(np.median([r['relative_difference_vs_mean'] for r in rows])),
        selected_mean_relative_change_vs_ei=float(np.mean([r['relative_difference_vs_ei'] for r in rows])),
        selected_median_relative_change_vs_ei=float(np.median([r['relative_difference_vs_ei'] for r in rows])),
        independent_policy_validation=False, inferential_p_values_computed=False,
        new_physical_evaluations=0, new_bound_queries=0, new_GP_systems=0,
        new_hyperparameter_fits=0, new_independent_samples=0)
    for name, obj in (('paid_replay.json',record), ('paid_replay_states.json',rows)):
        (OUT/name).write_text(json.dumps(obj, indent=2, allow_nan=False)+'\n')
    with (OUT/'paid_replay_states.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    print(json.dumps({k:v for k,v in record.items() if k != 'inputs_sha256'}, indent=2))


if __name__ == '__main__':
    run()
