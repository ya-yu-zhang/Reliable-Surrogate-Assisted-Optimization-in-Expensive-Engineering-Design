"""Read-only pointwise audit of the fifth interrupted GP-EI recovery."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .audit_third_recovery import audit_run, digest


ROOT = Path(__file__).resolve().parents[1]


def audit(root: Path = ROOT, *, write: bool = True) -> dict[str, Any]:
    archive = root / "results/interruption_20260921_v5"
    manifest = json.loads((archive / "recovery_manifest.json").read_text("utf-8"))
    assert manifest["objective_calls_by_archiver"] == 0
    assert manifest["all_pre_label_pairs_complete"] and manifest["no_pending_physical_return"]
    assert manifest["unchanged_budgets_and_scope"]
    assert len(manifest["partial_runs"]) == 4
    assert manifest["old_paid_calls"] == 1319 and manifest["expected_new_physical_calls"] == 281
    assert manifest["complete_runs_before_interruption"] == {"gp_ei_reference_v1": 639}
    assert all(digest(root / name) == expected for name, expected in manifest["recovery_sources"].items())
    prior_ids: set[str] = set()
    for relative in [
        "results/interruption_20260918_v1/recovery_manifest.json",
        "results/interruption_20260919_v2/recovery_manifest.json",
        "results/interruption_20260920_v3/recovery_manifest.json",
        "results/interruption_20260920_v4/recovery_manifest.json",
    ]:
        prior = json.loads((root / relative).read_text("utf-8"))
        prior_ids.update(row["runid"] for row in prior["partial_runs"])
    rows = [audit_run(root, row, prior_ids) for row in manifest["partial_runs"]]
    assert sum(row["canonical_algorithm_evaluations"] for row in rows) == 1600
    assert sum(row["new_physical_calls"] for row in rows) == 281
    assert not prior_ids.intersection(row["runid"] for row in rows)
    for source in ["gp_ei_reference_v1", "turbo_reference_v1"]:
        status = json.loads((root / "results" / source / "status.json").read_text("utf-8"))
        assert status["stage"] == "complete" and status["completed"] == status["expected"] == 648
        assert status["failed"] == 0
    result = {
        "schema": "fifth_recovery_audit_v1", "objective_calls_by_this_auditor": 0,
        "recovered_runs": 4, "canonical_algorithm_evaluations": 1600,
        "fifth_generation_saved_labels": 1319, "fifth_generation_new_physical_calls": 281,
        "redundant_recovery_validation_calls": 0,
        "all_archived_prefixes_exactly_equal": True, "all_physical_suffixes_exactly_equal": True,
        "all_canonical_trajectories_complete": True,
        "recovery_elapsed_excluded_from_exclusive_cost_analysis": True, "runs": rows,
    }
    if write:
        (archive / "fifth_recovery_audit.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> None:
    result = audit()
    print(json.dumps({key: value for key, value in result.items() if key != "runs"}, indent=2))


if __name__ == "__main__":
    main()
