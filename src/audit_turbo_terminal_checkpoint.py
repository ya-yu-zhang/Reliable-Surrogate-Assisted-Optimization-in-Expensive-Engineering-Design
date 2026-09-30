"""Independent zero-call checkpoint for the completed TuRBO formal batch."""

from __future__ import annotations

import csv
import hashlib
import itertools
import json
from pathlib import Path

from .run_solo_cost import process_inventory


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "results/turbo_reference_v1"
ANALYSIS = ROOT / "results/turbo_reference_analysis_v1"
OUT = ROOT / "results/turbo_reference_terminal_checkpoint_v1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert not OUT.exists(), "TuRBO terminal checkpoint already exists"
    status_path = SOURCE / "status.json"
    status = json.loads(status_path.read_text("utf-8"))
    live = {row["ProcessId"] for row in process_inventory()}
    assert status["stage"] == "complete"
    assert status["completed"] == status["expected"] == 648
    assert status["failed"] == 0 and status["pid"] not in live
    assert json.loads((SOURCE / "failures.json").read_text("utf-8")) == []

    manifest_path = SOURCE / "manifest.json"
    manifest = json.loads(manifest_path.read_text("utf-8"))
    assert all(digest(ROOT / name) == expected for name, expected in manifest["fingerprints"].items())
    config = manifest["config"]
    expected_keys = set(
        itertools.product(
            config["functions"], config["dimensions"], config["instances"], range(config["repeats"]), config["methods"]
        )
    )
    assert len(expected_keys) == 648 and config["methods"] == ["turbo_1"]

    analysis_path = ANALYSIS / "audit.json"
    analysis = json.loads(analysis_path.read_text("utf-8"))
    assert analysis["audited_runs"] == 648 and analysis["algorithm_evaluations"] == 151200
    assert analysis["failures"] == 0 and analysis["all_calls_charged"]
    assert analysis["no_future_labels_in_pre"] and analysis["all_points_in_bounds"]
    assert analysis["current_source_matches_manifest"] and analysis["environment_versions_match"]
    assert analysis["exact_duplicate_calls"] == 0

    with (ANALYSIS / "runs.csv").open("r", encoding="utf-8", newline="") as handle:
        runs = list(csv.DictReader(handle))
    keys = {(int(row["fid"]), int(row["dim"]), int(row["instance"]), int(row["rep"]), row["method"]) for row in runs}
    assert len(runs) == len(keys) == 648 and keys == expected_keys
    assert sum(int(row["algorithm_evaluations"]) for row in runs) == 151200
    assert sum(int(row["exact_duplicate_calls"]) for row in runs) == 0
    assert sum(int(row["partial_restart_paid_labels"]) for row in runs) == 364

    hashes_path = ANALYSIS / "source_journal_hashes.json"
    hashes = json.loads(hashes_path.read_text("utf-8"))
    assert len(hashes) == 648 and len({row["runid"] for row in hashes}) == 648
    for row in hashes:
        run = SOURCE / row["runid"]
        assert digest(run / "events.jsonl") == row["journal_sha256"]
        assert digest(run / "summary.json") == row["summary_sha256"]

    analysis_files = {
        path.relative_to(ROOT).as_posix(): digest(path)
        for path in sorted(ANALYSIS.glob("*"))
        if path.is_file()
    }
    result = {
        "schema": "turbo_reference_terminal_checkpoint_v1",
        "objective_calls_by_this_auditor": 0,
        "terminal_status_verified": True,
        "formal_parent_absent": True,
        "complete_design_verified": True,
        "audited_runs": 648,
        "algorithm_evaluations": 151200,
        "failures": 0,
        "exact_duplicate_calls": 0,
        "partial_restart_paid_labels": 364,
        "raw_journal_hashes_verified": 648,
        "raw_summary_hashes_verified": 648,
        "status_sha256": digest(status_path),
        "manifest_sha256": digest(manifest_path),
        "source_hash_list_sha256": digest(hashes_path),
        "analysis_files": analysis_files,
    }
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / "audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
