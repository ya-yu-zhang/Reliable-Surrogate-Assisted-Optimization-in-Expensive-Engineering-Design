from src.recover_interrupted_application_run_v2 import equivalent


def event(x, state=1):
    return {"event": "pre", "t": 1, "n_observed": 0, "x": [x], "x_unit": [(x + 1) / 2],
            "optimizer_state": {"generation": state}, "best_before": None}


def test_roundoff_equivalent_candidate_is_accepted():
    assert equivalent(event(0.25), event(0.25 + 8e-16))


def test_material_candidate_or_state_change_is_rejected():
    assert not equivalent(event(0.25), event(0.25000001))
    assert not equivalent(event(0.25), event(0.25, state=2))
