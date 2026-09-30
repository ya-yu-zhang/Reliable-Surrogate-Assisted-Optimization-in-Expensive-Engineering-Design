import pytest

from src.audit_gp_ei_terminal_checkpoint import expected_design, validate_terminal_status


def test_expected_gp_ei_design_has_all_648_unique_cells():
    config = {
        "functions": list(range(1, 25)),
        "dimensions": [10, 20, 40],
        "instances": [11, 12, 13],
        "repeats": 3,
        "methods": ["gp_ei"],
    }
    design = expected_design(config)
    assert len(design) == 648
    assert (1, 10, 11, 0, "gp_ei") in design
    assert (24, 40, 13, 2, "gp_ei") in design


def test_terminal_status_rejects_live_or_incomplete_parent():
    complete = {"stage": "complete", "completed": 648, "expected": 648, "failed": 0, "pid": 42}
    validate_terminal_status(complete, set())
    with pytest.raises(AssertionError):
        validate_terminal_status(complete, {42})
    incomplete = dict(complete, stage="running", completed=647)
    with pytest.raises(AssertionError):
        validate_terminal_status(incomplete, set())
