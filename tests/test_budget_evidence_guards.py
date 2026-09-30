import json

import pytest

from src import build_budget_sensitivity_revision as builder
from src import finish_budget_evidence_export as exporter


def test_incomplete_budget_audit_creates_no_paper(tmp_path):
    path = tmp_path / "results/budget_performance_sensitivity_analysis_v1"
    path.mkdir(parents=True)
    (path / "audit.json").write_text(
        json.dumps(
            dict(
                complete_design=False,
                runs=2700,
                algorithm_evaluations=270000,
                diagnostic_evaluations=0,
                raw_file_hashes=7020,
                pre_information_verified=True,
                internal_bounds_and_management_replayed=True,
                internal_budget_prefix_invariant_runs=540,
                external_prefix_equal_runs=0,
                statistical_tests_added=0,
                not_used_for_parameter_selection=True,
                source_hashes_verified=True,
            )
        ),
        encoding="utf-8",
    )
    with pytest.raises(AssertionError):
        builder.require_complete(tmp_path)
    assert not (tmp_path / "paper").exists()


def test_existing_budget_export_record_refuses_duplicate(tmp_path, monkeypatch):
    monkeypatch.setattr(exporter, "ROOT", tmp_path)
    monkeypatch.setattr(exporter, "OUT", tmp_path / "results/budget_evidence_export_v1")
    exporter.OUT.mkdir(parents=True)
    with pytest.raises(AssertionError, match="duplicate"):
        exporter.main()
