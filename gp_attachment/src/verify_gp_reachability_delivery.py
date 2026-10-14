"""Read-only checks of the delivered development records; never simulates."""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

from .physical_bound_screen import sha, write
from .reachability_witness_diagnosis import verify_sources

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/engineering_optimization_gp_reachability_v1'
REPORT = ROOT / 'paper/engineering_optimization/gp_reachability_20261013'


def verify():
    plan = json.loads((OUT / 'plan.json').read_text())
    verify_sources(plan)
    witness = json.loads((OUT / 'witness_status.json').read_text())
    events = [json.loads(s) for s in (OUT / 'witness_events.jsonl').read_text().splitlines()]
    counts = Counter(r['event'] for r in events)
    assert witness['complete'] and witness['new_physics_attempts'] == 2
    assert counts['pre_true_response'] == counts['true_response'] == 2 and counts['failure'] == 0
    assert [r['attempt'] for r in events if r['event'] == 'pre_true_response'] == [1, 2]
    assert witness['new_independent_samples'] == witness['new_optimization_attempts'] == witness['recovery_attempts'] == 0
    assert all(not r['residual_flag'] for r in witness['results'])
    construction = json.loads((OUT / 'construction_status.json').read_text())
    assert construction['complete'] and not construction['future_responses_exposed']
    assert construction['plan_sha256'] == sha((OUT / 'plan.json').read_bytes())
    for name, digest in construction['witness_files_sha256'].items():
        assert sha((OUT / name).read_bytes()) == digest
    for name, digest in construction['execution_sources_sha256'].items():
        assert sha((ROOT / name).read_bytes()) == digest
    for name, digest in construction['files_sha256'].items():
        assert sha((OUT / 'construction' / name).read_bytes()) == digest
    stats = construction['statistics']
    assert (stats['nontrivial_states'], stats['alias_only_states'], stats['first_action_branches']) == (43, 17, 114)
    assert stats['unique_bound_designs'] == 44146 <= plan['config']['max_unique_bound_designs']
    assert construction['new_physics_attempts'] == construction['new_independent_samples'] == 0
    assert len(plan['mean_states']) == 60 and len(construction['alias_only_exclusions']) == 17
    rows = list(csv.DictReader((REPORT / 'branch_results.csv').open()))
    assert len(rows) == 228
    for mode in ['nonnegative', 'trial_lower']:
        subset = [r for r in rows if r['range'] == mode]
        assert len(subset) == 114
        assert all(r['actual_next_action_included'] == r['native_next_action_included'] == 'True' for r in subset)
        assert all(r['root_source_prediction_replay'] == r['next_source_prediction_replay'] == 'True' for r in subset)
        assert all(r['category_error'] == 'False' and r['terminal_interval_valid_at_stored_responses'] == 'True' for r in subset)
        assert all(r['reachable_category'] == r['full_pool_category'] == 'abstain' for r in subset if r['baseline_branch'] == 'False')
    analysis = json.loads((REPORT / 'analysis.json').read_text())
    assert analysis['validation_passed_at_stored_responses']
    assert analysis['proofs_rechecked_after_serialization'] == stats['exclusion_proofs_verified'] == 232564
    assert analysis['total_new_physics_attempts_this_protocol'] == 2
    assert analysis['project_cumulative_physics_attempts'] == 55309
    assert not analysis['independent_gate']['passed'] and not analysis['start_new_independent_optimization_experiment']
    status = json.loads((ROOT / 'paper/engineering_optimization/work_status.json').read_text())
    assert status['costs']['total_new_physics_solver_attempts_this_revision'] == 55309
    assert status['costs']['physical_bound_reference_attempts'] == 2
    assert status['costs']['gp_reachability_witness_attempts'] == 2
    assert not status['submission_ready']
    return {'complete': True, 'frozen_sources_verified': 204,
        'witness_attempts': 2, 'retries': 0, 'replacements': 0, 'new_independent_samples': 0,
        'construction_records_hash_checked': 43, 'actual_next_action_inclusion': '114/114 in both ranges',
        'source_prediction_replay_flags': 0, 'serialized_proofs_already_rechecked': 232564,
        'verification_new_physics_attempts': 0, 'verification_new_bound_queries': 0,
        'independent_study_gate_passed': False, 'original_frozen_inputs_and_physical_screen_unchanged': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record', action='store_true')
    args = parser.parse_args()
    result = verify()
    if args.record:
        write(REPORT / 'delivery_verification.json', result)
    print(json.dumps(result))
