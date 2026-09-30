import json

import ioh
import numpy as np
import pytest

pytest.importorskip('torch', reason='Application GP transfer requires the isolated application environment')
from src.application_methods import PaidObjective, execute
from src.gp_references import run_one


@pytest.mark.parametrize('method', ['gp_ei', 'turbo_1'])
def test_callable_preserves_original_gp_search_and_prelabel_state(tmp_path, method):
    original = run_one(1, 2, 4, 0, method, 8, tmp_path/'original')
    original_events = [json.loads(v) for v in
        (tmp_path/'original'/original['runid']/'events.jsonl').read_text().splitlines()][1:]
    objective = ioh.get_problem(1, dimension=2, instance=4, problem_class=ioh.ProblemClass.BBOB)
    path = tmp_path/'callable.jsonl'
    observed = []

    def opaque(point):
        # The real evaluation can only occur after its proposal has been flushed.
        events = [json.loads(v) for v in path.read_text().splitlines()]
        assert events[-1]['event'] == 'pre'
        assert events[-1]['n_observed'] == len(observed)
        assert 'y' not in events[-1]
        observed.append(point.copy())
        return objective(point)

    oracle = PaidObjective(opaque, objective.bounds.lb, objective.bounds.ub, 8)
    with path.open('w', encoding='utf-8') as journal:
        execute(oracle, 2, 201040, method, journal)
    events = [json.loads(v) for v in path.read_text().splitlines()]
    assert oracle.calls == objective.state.evaluations == len(observed) == 8
    assert len(events) == 16
    # Wall time is not a random state or a search input; all other entries match.
    for original_event, callable_event in zip(original_events, events):
        original_event.pop('preparation_seconds', None)
        callable_event.pop('preparation_seconds', None)
        assert original_event == callable_event
    np.testing.assert_array_equal(oracle.points, observed)
    assert min(oracle.values) == original['best']
