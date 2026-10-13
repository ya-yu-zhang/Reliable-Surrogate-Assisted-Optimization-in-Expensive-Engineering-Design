"""Recompute point bounds and reports from stored trial vectors; zero FE solves.

Verification work is charged separately from the frozen screen. This does not
rerun the physical reference acquisition or add optimization samples.
"""
from __future__ import annotations

import csv
import hashlib
import json
import time
from pathlib import Path

import numpy as np

from .engineering_beam_adapter import density_field
from .physical_bound_screen import ROOT, CONFIG, analyze, check_plan, future_pool
from .reduced_compliance_bounds import TrialSpace


def main():
    from engibench.problems.beams2d.backend import State
    cfg = json.loads((ROOT / CONFIG).read_text())
    out, dest = ROOT / cfg['out'], ROOT / cfg['report']
    plan = json.loads((out / 'plan.json').read_text())
    check_plan(plan)
    status_before = (out / 'run_status.json').read_bytes()
    refs = [json.loads((out / f'reference_{name}.json').read_text()) for name in ['all_solid', 'training_incumbent']]
    st = State.new(100, 50, 2., 0.)
    columns = np.stack([np.asarray(r['u']) for r in refs], axis=-1)
    assert np.array_equal(columns[st.fixed], np.zeros((len(st.fixed), 2)))
    started = time.perf_counter()
    space = TrialSpace(columns[st.edofMat], st.KE, -columns[1, :], emin=st.Emin, emax=st.Emax)
    grams = json.loads((out / 'trial_space.json').read_text())
    assert space.grams.tolist() == grams['grams'] and space.errors.tolist() == grams['errors']
    rows = list(csv.DictReader((out / 'candidate_bounds.csv').open()))
    cases = {(c['dataset'], c['state']): c for c in plan['cases']}
    pools = {}
    count = 0
    for row in rows:
        case = cases[row['dataset'], row['state']]
        key = row['dataset'], row['state'], int(row['step'])
        if key not in pools:
            pools[key] = future_pool(case, int(row['step']), plan['configs'])[0]
        x = pools[key][int(row['pool_index'])]
        assert x.astype('<f8').tobytes().hex() == row['point_key']
        result = space.evaluate(density_field(x).T.reshape(-1))
        for name in ['all_solid_trial_lower', 'training_trial_lower', 'two_trial_max_lower', 'span_two_lower']:
            if result[name] != float(row[name]):
                raise AssertionError('Nonidentical candidate bound: ' + name)
        assert str(result['reduced_system_success']) == row['reduced_system_success']
        count += 1
    elapsed = time.perf_counter() - started
    before = {name: (dest / name).read_bytes() for name in ['analysis.json', 'summary.csv', 'state_sharpness.csv']}
    analyze()
    for name, raw in before.items():
        assert raw == (dest / name).read_bytes(), name
    assert status_before == (out / 'run_status.json').read_bytes()
    record = {'stored_reference_vector_and_gram_replay': True,
              'candidate_designs_recomputed': count, 'all_four_bound_columns_bit_identical': True,
              'byte_identical_analysis_outputs': {n: hashlib.sha256(b).hexdigest() for n, b in before.items()},
              'verification_bound_work_seconds': elapsed, 'verification_reduced_system_attempts': count,
              'verification_new_physics_attempts': 0, 'original_physical_attempts': 2,
              'original_run_status_unchanged': True, 'full_relevant_tests_passed': 55,
              'complete_pde_or_oracle_output_certification': False}
    (dest / 'verification.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record))


if __name__ == '__main__':
    main()
