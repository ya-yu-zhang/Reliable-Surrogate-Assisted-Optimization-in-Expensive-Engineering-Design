import pytest
from src.application_high_journal_audit_safe import validate_gp_candidate_accounting

def events(count):
    return [{"event":"meta"},{"event":"pre","optimizer_state":{"mode":"gp_ei","continuous_starts":8,"acquisition_candidates":count}},{"event":"label"}]
def test_accepts_frozen_4096_plus_eight_design():
    assert validate_gp_candidate_accounting(events(4104))==1
def test_rejects_more_than_eight_continuous_additions():
    with pytest.raises(AssertionError):validate_gp_candidate_accounting(events(4105))
