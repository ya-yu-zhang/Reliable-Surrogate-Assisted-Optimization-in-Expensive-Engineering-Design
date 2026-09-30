from src.recover_interrupted_application_run_v3 import equivalent


def event(mean, generation=3, label=0.5):
    return {"event": "pre", "t": 58, "n_observed": 57, "x": [0.2], "x_unit": [0.6],
            "optimizer_state": {"generation": generation, "mean": [mean], "sigma": 0.3,
                                "population_size": 19, "individual": 0},
            "best_before": label}


def test_state_roundoff_is_accepted():
    assert equivalent(event(0.25), event(0.25 + 9e-16))


def test_material_state_or_nonstate_change_is_rejected():
    assert not equivalent(event(0.25), event(0.25000001))
    assert not equivalent(event(0.25, generation=3), event(0.25, generation=4))
    assert not equivalent(event(0.25, label=0.5), event(0.25, label=0.500000000000001))
