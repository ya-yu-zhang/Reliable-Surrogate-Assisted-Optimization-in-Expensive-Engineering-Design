"""Verify frozen GP proofs and benchmark only the coefficient-to-set operator.

No physical engine, GP hyperparameter fit or physical-bound evaluator is called.
This is post hoc computational development, not independent optimization data.
"""
from __future__ import annotations
import argparse
import csv
from fractions import Fraction
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import statistics
import time

import numpy as np
from scipy.stats import qmc
from sklearn.gaussian_process.kernels import ConstantKernel, Matern

from .certified_affine_envelope import (exact_outer_actions, coefficient_bands,
                                       check_exclusion)
from .gp_action_reachability import outer_actions, coefficient_enclosures

COMMIT = '58f539c2d0738b20c7d0d4889fe8d808a03a3019'


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def locate(root, name):
    for folder in ('baseline', 'restored', 'gp_attachment', 'baseline_more'):
        path = root/folder/name
        if path.is_file():
            return path
    raise FileNotFoundError(name)


def future_pool(meta, cfg, step=1):
    if meta['dataset'] == 'previous_holdout':
        namespace = [cfg['master_seed'], meta['block'], cfg['source_controls'].index(meta['source']), 5, step]
    else:
        namespace = [cfg['master_seed'], cfg['source_methods'].index(meta['source']), meta['block'], step]
    seed = int(np.random.SeedSequence(namespace).generate_state(1)[0])
    return qmc.Sobol(19, scramble=True, seed=seed).random_base2(cfg['pool_power']), seed


def exact_json(value):
    if isinstance(value, Fraction):
        return [str(value.numerator), str(value.denominator)]
    if isinstance(value, dict):
        return {str(k): exact_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [exact_json(v) for v in value]
    return value


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, allow_nan=False)+'\n')


def run(root, out, repeats):
    gp = root/'gp_attachment'
    protocol = gp/'results/engineering_optimization_gp_reachability_v1'
    manifest = json.loads((gp/'DELIVERY_MANIFEST.json').read_text())
    assert manifest['baseline_commit'] == COMMIT
    for item in manifest['files']:
        path = gp/item['path']
        assert path.stat().st_size == item['bytes'] and digest(path) == item['sha256']
    plan = json.loads((protocol/'plan.json').read_text())
    frozen = {**plan['source_hashes'], **plan['witness_frozen_hashes']}
    for name, expected in frozen.items():
        assert digest(locate(root, name)) == expected, name
    assert digest(protocol/'plan.json') == manifest['frozen_plan_sha256']
    status = json.loads((protocol/'construction_status.json').read_text())
    assert status['complete'] and not status['future_responses_exposed']
    for name, expected in status['files_sha256'].items():
        assert digest(protocol/'construction'/name) == expected
    for name, expected in status['execution_sources_sha256'].items():
        assert digest(locate(root, name)) == expected
    witness = json.loads((protocol/'witness_status.json').read_text())
    events = [json.loads(x) for x in (protocol/'witness_events.jsonl').read_text().splitlines()]
    pres = [x for x in events if x['event'] == 'pre_true_response']
    responses = [x for x in events if x['event'] == 'true_response']
    assert witness['complete'] and witness['new_physics_attempts'] == 2
    assert len(pres) == len(responses) == 2
    assert [x['attempt'] for x in pres] == [1, 2]
    assert not any(x['event'] == 'failure' for x in events)
    for expected, actual in zip(plan['witnesses'], witness['results'], strict=True):
        assert all(actual[k] == v for k, v in expected.items())
        assert not actual['residual_flag']
    rows, staged = [], []
    old_count = new_count = matrix_checks = coefficient_checks = 0
    old_check_seconds = new_check_seconds = matrix_seconds = 0.
    out.mkdir(parents=True, exist_ok=True)
    # Phase 1 does not load future-response journals or grading CSVs.
    for file_index, name in enumerate(sorted(status['files_sha256'])):
        item = json.loads((protocol/'construction'/name).read_text())
        meta = item['metadata']; cfg = plan['pool_configs'][meta['dataset']]
        pool, seed = future_pool(meta, cfg)
        assert seed == item['pool_seed']
        assert hashlib.sha256(pool.tobytes()).hexdigest() == item['raw_pool_sha256']
        source_name = ('results/engineering_optimization_common_continuation_v1/plans/'+meta['state']+'.json'
                       if meta['dataset'] == 'archived_common_mean' else
                       f"results/engineering_optimization_budget_audit_v1/block_{meta['block']}/{meta['state']}_plan.json")
        initial = json.loads(locate(root, source_name).read_text())
        assert not {'trajectories', 'control_curves', 'branch_records', 'calibration'}.intersection(initial)
        saved = {'metadata': meta, 'algorithm_inputs_include_future_response': False, 'branches': {}}
        for branch, rec in item['branches'].items():
            coeff = rec['coefficients']; assert coeff is not None
            args = (coeff['slope'], coeff['intercept'])
            kwargs = {'slope_error': coeff['slope_error'], 'intercept_error': coeff['intercept_error']}
            bands = coefficient_bands(*args, **kwargs)
            begin = time.perf_counter()
            x = np.array(initial['actions'][branch]); X = np.vstack((np.array(initial['X']), x))
            kernel = (ConstantKernel(1., (.05, 20))*Matern(np.full(19, .2), (.005, 2.), nu=2.5)).clone_with_theta(np.array(initial['theta']))
            matrix = kernel(X); matrix[np.diag_indices_from(matrix)] += cfg['alpha']
            cross = kernel(pool[np.array(rec['eligible_pool_indices'])], X)
            assert hashlib.sha256(matrix.tobytes()).hexdigest() == rec['matrix_sha256']
            assert hashlib.sha256(cross.tobytes()).hexdigest() == rec['cross_sha256']
            recalculated = coefficient_enclosures(matrix, cross, np.array(initial['y']))
            for key in ('slope', 'intercept', 'slope_error', 'intercept_error'):
                assert np.array_equal(recalculated[key], np.array(coeff[key])), (name, branch, key)
            matrix_checks += 1; coefficient_checks += 1
            matrix_seconds += time.perf_counter()-begin
            saved['branches'][branch] = {}
            for mode in ('nonnegative', 'trial_lower'):
                domain = 0. if mode == 'nonnegative' else rec['pending_lower']
                old = rec['sets'][mode]
                assert len(old['indices'])+len(old['excluded_proofs']) == len(args[0])
                for key, values in zip(('coefficient_band_lower_slope', 'coefficient_band_lower_intercept',
                                        'coefficient_band_upper_slope', 'coefficient_band_upper_intercept'), bands, strict=True):
                    assert values == old[key]
                begin = time.perf_counter()
                assert all(check_exclusion(*bands, proof, domain) for proof in old['excluded_proofs'])
                old_check_seconds += time.perf_counter()-begin
                old_count += len(old['excluded_proofs'])
                timings = {'pairwise': [], 'envelope': []}
                result = None
                for repeat in range(repeats):
                    order = ['pairwise', 'envelope'] if (file_index+repeat) % 2 == 0 else ['envelope', 'pairwise']
                    for algorithm in order:
                        function = outer_actions if algorithm == 'pairwise' else exact_outer_actions
                        begin = time.perf_counter()
                        current = function(*args, **kwargs, response_lower=domain)
                        timings[algorithm].append(time.perf_counter()-begin)
                        if algorithm == 'envelope':
                            result = current
                        else:
                            assert list(current['indices']) == old['indices']
                assert result['indices'] == old['indices'], (name, branch, mode)
                begin = time.perf_counter()
                assert all(check_exclusion(*bands, proof, domain) for proof in result['excluded_proofs'])
                new_check_seconds += time.perf_counter()-begin
                new_count += len(result['excluded_proofs'])
                for i, low, high in zip(old['indices'], old['response_lower'], old['response_upper'], strict=True):
                    exact_lo, exact_hi = result['exact_intervals'][i]
                    assert Fraction.from_float(float(low)) <= exact_lo
                    assert high is None or (exact_hi is not None and exact_hi <= Fraction.from_float(float(high)))
                a = statistics.median(timings['pairwise']); b = statistics.median(timings['envelope'])
                row = {'dataset': meta['dataset'], 'state': meta['state'], 'block': meta['block'],
                       'branch': branch, 'range': mode, 'eligible': len(args[0]),
                       'kept': len(result['indices']), 'hull_segments': len(result['upper_envelope_indices']),
                       'proofs': len(result['excluded_proofs']), 'same_indices': True,
                       'pairwise_seconds': a, 'envelope_seconds': b, 'speed_ratio': a/b,
                       'repeat_count': repeats}
                rows.append(row)
                saved['branches'][branch][mode] = exact_json(result)
                staged.append((meta, pool, branch, rec, mode, result))
        write(out/'certificates'/name, saved)
        print(json.dumps({'verified_states': file_index+1, 'proofs': old_count,
                          'new_physics_attempts': 0}), flush=True)
    assert old_count == new_count == 232564
    # Phase 2 checks already paid coordinates/responses only after all sets exist.
    common = {}; pending = None
    path = locate(root, 'results/engineering_optimization_common_continuation_v1/events.jsonl')
    for line in path.read_text().splitlines():
        record = json.loads(line)
        if record['event'] == 'pre':
            pending = record
        elif record['event'] == 'label':
            assert pending is not None
            if record['step'] <= 1:
                common[record['state'], record['branch'], record['step']] = {**pending, 'y': record['y']}
            pending = None
    old_rows = list(csv.DictReader((gp/'paper/engineering_optimization/gp_reachability_20261013/branch_results.csv').open()))
    grading = {(r['dataset'], r['state'], r['branch'], r['range']): r for r in old_rows}
    inclusion = errors = 0
    for meta, pool, branch, rec, mode, result in staged:
        if meta['dataset'] == 'archived_common_mean':
            first, second = (common[meta['state'], branch, h] for h in (0, 1))
        else:
            source = locate(root, f"results/engineering_optimization_budget_audit_v1/block_{meta['block']}/{meta['state']}_summary.json")
            history = json.loads(source.read_text())['trajectories']['mean'][branch]
            first, second = history[:2]
        eligible = rec['eligible_pool_indices']; candidates = pool[np.array(eligible)]
        indices = np.flatnonzero(np.all(candidates == np.array(second['x']), axis=1))
        assert len(indices) == 1
        chosen = int(indices[0]); assert chosen in result['indices']
        interval = result['exact_intervals'][chosen]; z = Fraction.from_float(float(first['y']))
        assert interval[0] <= z and (interval[1] is None or z <= interval[1])
        inclusion += 1
        original = grading[meta['dataset'], meta['state'], branch, mode]
        assert original['actual_next_action_included'] == 'True'
        assert original['reachable_category'] in ('abstain', 'tie')
        assert original['category_error'] == 'False'
    summary = {
        'baseline_commit': COMMIT, 'analysis_type': 'posthoc computational development on existing coefficient bands',
        'gp_attachment_sha256': digest(root/'upload/01-gp_reachability_20261013_results.zip'),
        'attachment_members_hash_verified': len(manifest['files']), 'frozen_source_hashes_verified': len(frozen),
        'kernel_matrix_and_cross_hashes_reconstructed': matrix_checks,
        'coefficient_enclosures_byte_identical': coefficient_checks,
        'old_exclusion_proofs_exactly_rechecked': old_count,
        'new_exclusion_proofs_exactly_checked': new_count,
        'branch_range_cases': len(rows), 'states': 43, 'original_metadata_states_retained': 60,
        'actual_paid_action_inclusion': f'{inclusion}/228 branch-range checks, 114/114 per range',
        'all_action_sets_equal_frozen_pairwise_reader': True,
        'new_intervals_subset_of_old_outward_intervals': True,
        'maximum_rival_indices_per_exclusion': max(len(p)-1 for *_, result in staged for p in result['excluded_proofs']),
        'cost_scope': 'Coefficient-to-action-set construction only. Shared GP coefficient work, physical bounds and paid baseline are excluded from both paired timers; independent certificate checking is reported separately.',
        'paired_timing_design': f'{repeats} repeats per branch-range, alternating algorithm order; median within each case, summed across cases. Repeats/ranges/branches are dependent, not independent samples.',
        'pairwise_pruner_seconds': sum(r['pairwise_seconds'] for r in rows),
        'envelope_pruner_seconds': sum(r['envelope_seconds'] for r in rows),
        'old_independent_proof_check_seconds': old_check_seconds,
        'new_independent_proof_check_seconds': new_check_seconds,
        'matrix_and_coefficient_verification_seconds': matrix_seconds,
        'hull_segments_min': min(r['hull_segments'] for r in rows),
        'hull_segments_max': max(r['hull_segments'] for r in rows),
        'new_physics_attempts': 0, 'new_physical_bound_queries': 0,
        'new_gp_hyperparameter_fits': 0, 'new_independent_optimization_samples': 0,
        'new_confirmatory_families': 0, 'prior_witness_attempts': 2, 'remaining_witness_attempts': 0,
        'complete_deployment_cost_benefit_demonstrated': False,
        'new_H1_category_or_selection_certificates': 0,
        'H5_reachable_history_extension': False, 'independent_study_gate': False,
        'runtime_versions': {n: importlib.metadata.version(n) for n in ('numpy', 'scipy', 'scikit-learn')},
        'operator_source_sha256': digest(root/'src/certified_affine_envelope.py'),
        'benchmark_source_sha256': digest(Path(__file__)),
    }
    summary['pruner_stage_speed_ratio'] = summary['pairwise_pruner_seconds']/summary['envelope_pruner_seconds']
    summary['pruner_plus_external_proof_check_speed_ratio'] = (
        (summary['pairwise_pruner_seconds']+old_check_seconds)/
        (summary['envelope_pruner_seconds']+new_check_seconds))
    with (out/'paired_timing.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    write(out/'analysis.json', summary)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=Path('results/gp_envelope_acceleration_20261014'))
    parser.add_argument('--repeats', type=int, default=3)
    args = parser.parse_args()
    assert args.repeats >= 1
    root = Path(__file__).resolve().parents[1]
    run(root, args.out, args.repeats)
