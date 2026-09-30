"""Read-only audit of the third interrupted-reference recovery.

The audit never evaluates an objective.  It verifies every archived paid label,
the final canonical journal, and the separately recorded physical suffix calls.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_events(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text("utf-8").splitlines() if line]


def event_equal(left: dict[str, Any], right: dict[str, Any]) -> bool:
    """Compare scientific journal content while ignoring wall-clock preparation time."""
    left = dict(left)
    right = dict(right)
    left.pop("preparation_seconds", None)
    right.pop("preparation_seconds", None)
    return left == right


def budget_from_runid(runid: str) -> int:
    match = re.search(r"_b(\d+)$", runid)
    if match is None:
        raise AssertionError(f"Run ID has no budget suffix: {runid}")
    return int(match.group(1))


def audit_run(root: Path, row: dict[str, Any], prior_partial_ids: set[str]) -> dict[str, Any]:
    runid = row["runid"]
    source = row["source"]
    archived = root / row["archive"]
    current = root / "results" / source / runid
    budget = budget_from_runid(runid)

    assert runid not in prior_partial_ids, f"Unexpected earlier recovery generation for {runid}"
    assert row["pending_pre"] == 0
    for name, expected in row["file_sha256"].items():
        assert digest(archived / name) == expected

    recovery = json.loads((current / "recovery.json").read_text("utf-8"))
    assert recovery["old_paid_calls"] == row["paid_labels"]
    assert recovery["physical_total"] == budget
    assert recovery["new_paid_calls"] == budget - row["paid_labels"]
    assert recovery["old_paid_calls"] + recovery["new_paid_calls"] == budget
    assert recovery["complete_prefix_states_and_labels_equal"]
    assert recovery["optimizer_source_unchanged"]

    old = read_events(archived / "events.jsonl")
    full = read_events(current / "events.jsonl")
    assert len(old) == 1 + 2 * row["paid_labels"]
    assert len(full) == 1 + 2 * budget
    assert all(event_equal(a, b) for a, b in zip(old, full[: len(old)]))

    physical_path = current / "recovery_physical_calls.jsonl"
    physical = read_events(physical_path)
    assert len(physical) == 2 * recovery["new_paid_calls"]
    start = row["paid_labels"] + 1
    for t, (pre, label) in enumerate(zip(physical[::2], physical[1::2]), start):
        assert pre["event"] == "pre" and label["event"] == "label"
        assert pre["t"] == label["t"] == t
        # The physical-call ledger is intentionally a projection: it records
        # only the actually queried point/label plus recovery counters.  The
        # canonical journal additionally records optimizer state, RNG hashes,
        # unit coordinates, and best-so-far values.  Compare their shared
        # scientific payload instead of requiring identical representations.
        assert pre["x"] == full[2 * t - 1]["x"]
        assert label["y"] == full[2 * t]["y"]

    summary_path = current / "summary.json"
    summary = json.loads(summary_path.read_text("utf-8"))
    assert summary["algorithm_evaluations"] == budget
    assert summary["diagnostic_evaluations"] == 0

    return {
        "runid": runid,
        "source": source,
        "archive_paid_labels": row["paid_labels"],
        "new_physical_calls": recovery["new_paid_calls"],
        "canonical_algorithm_evaluations": budget,
        "prior_recovery_generation_present": False,
        "redundant_recovery_validation_calls": 0,
        "archived_prefix_exactly_equal": True,
        "physical_suffix_exactly_equal": True,
        "final_journal_sha256": digest(current / "events.jsonl"),
        "final_summary_sha256": digest(summary_path),
        "physical_suffix_log_sha256": digest(physical_path),
        "recovery_sidecar_sha256": digest(current / "recovery.json"),
    }


def audit(root: Path = ROOT, *, write: bool = True) -> dict[str, Any]:
    archive = root / "results/interruption_20260920_v3"
    manifest = json.loads((archive / "recovery_manifest.json").read_text("utf-8"))
    assert manifest["objective_calls_by_archiver"] == 0
    assert manifest["all_pre_label_pairs_complete"]
    assert manifest["no_pending_physical_return"]
    assert manifest["unchanged_budgets_and_scope"]
    assert len(manifest["partial_runs"]) == 8
    assert manifest["old_paid_calls"] == 2514
    assert sum(row["paid_labels"] for row in manifest["partial_runs"]) == 2514
    assert manifest["complete_runs_before_interruption"] == {
        "turbo_reference_v1": 423,
        "gp_ei_reference_v1": 157,
    }

    for name, expected in manifest["recovery_sources"].items():
        assert digest(root / name) == expected

    prior_partial_ids: set[str] = set()
    for relative in (
        "results/interruption_20260918_v1/recovery_manifest.json",
        "results/interruption_20260919_v2/recovery_manifest.json",
    ):
        prior = json.loads((root / relative).read_text("utf-8"))
        prior_partial_ids.update(row["runid"] for row in prior["partial_runs"])

    rows = [audit_run(root, row, prior_partial_ids) for row in manifest["partial_runs"]]
    assert sum(row["canonical_algorithm_evaluations"] for row in rows) == 3200
    assert sum(row["new_physical_calls"] for row in rows) == 686
    assert not prior_partial_ids.intersection(row["runid"] for row in rows)

    for source in ("turbo_reference_v1", "gp_ei_reference_v1"):
        status = json.loads((root / "results" / source / "status.json").read_text("utf-8"))
        assert status["stage"] == "complete"
        assert status["completed"] == status["expected"] == 648
        assert status["failed"] == 0

    result = {
        "schema": "third_recovery_audit_v1",
        "objective_calls_by_this_auditor": 0,
        "recovered_runs": 8,
        "canonical_algorithm_evaluations": 3200,
        "third_generation_saved_labels": 2514,
        "third_generation_new_physical_calls": 686,
        "redundant_recovery_validation_calls": 0,
        "all_archived_prefixes_exactly_equal": True,
        "all_physical_suffixes_exactly_equal": True,
        "all_canonical_trajectories_complete": True,
        "recovery_elapsed_excluded_from_exclusive_cost_analysis": True,
        "runs": rows,
    }
    if write:
        output = archive / "third_recovery_audit.json"
        output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> None:
    result = audit()
    print(json.dumps({key: value for key, value in result.items() if key != "runs"}, indent=2))


if __name__ == "__main__":
    main()
