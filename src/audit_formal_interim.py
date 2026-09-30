"""Read-only full-journal audit of completed formal runs while batches continue.

Only directories that already contain ``summary.json`` at the initial snapshot
are read.  The result is an interim checkpoint and cannot replace the required
648/648 terminal audits.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

from .analyze_gp_references import adapter_hash, audit_run


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/formal_interim_audit_20260920_v1"
SOURCES = ("turbo_reference_v1", "gp_ei_reference_v1")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_source(source_name: str, expected_hash: str) -> dict:
    source = ROOT / "results" / source_name
    manifest = json.loads((source / "manifest.json").read_text("utf-8"))
    status_before = json.loads((source / "status.json").read_text("utf-8"))
    assert status_before["stage"] == "running" and status_before["failed"] == 0
    assert all(digest(ROOT / name) == expected for name, expected in manifest["fingerprints"].items())

    config = manifest["config"]
    all_keys = set(
        itertools.product(
            config["functions"],
            config["dimensions"],
            config["instances"],
            range(config["repeats"]),
            config["methods"],
        )
    )
    summaries = sorted(source.glob("*/summary.json"))
    assert len(summaries) >= status_before["completed"]
    rows = []
    hashes = []
    warnings = Counter()
    for summary_path in summaries:
        row, counts, file_hashes = audit_run(summary_path, expected_hash)
        rows.append(row)
        hashes.append(file_hashes)
        warnings.update(counts)

    keys = {(row["fid"], row["dim"], row["instance"], row["rep"], row["method"]) for row in rows}
    assert len(keys) == len(rows)
    assert keys.issubset(all_keys)
    status_after = json.loads((source / "status.json").read_text("utf-8"))
    assert status_after["failed"] == 0
    assert len(rows) <= status_after["completed"] + 4
    evaluations = sum(row["algorithm_evaluations"] for row in rows)
    assert evaluations == sum(10 * row["dim"] for row in rows)

    return {
        "source": source_name,
        "terminal_audit": False,
        "snapshot_completed_runs": len(rows),
        "status_completed_before": status_before["completed"],
        "status_completed_after": status_after["completed"],
        "expected_terminal_runs": status_after["expected"],
        "algorithm_evaluations": evaluations,
        "failures": 0,
        "all_calls_charged": True,
        "no_future_labels_in_pre": True,
        "all_points_in_bounds": True,
        "current_source_matches_manifest": True,
        "environment_versions_match": True,
        "exact_duplicate_calls": sum(row["exact_duplicate_calls"] for row in rows),
        "partial_restart_paid_labels": sum(row["partial_restart_paid_labels"] for row in rows),
        "warnings": dict(warnings),
        "journal_hashes": hashes,
    }


def main() -> None:
    assert not OUT.exists(), "Formal interim audit already exists"
    expected_hash = adapter_hash()
    sources = [audit_source(name, expected_hash) for name in SOURCES]
    result = {
        "schema": "formal_interim_audit_v1",
        "objective_calls_by_this_auditor": 0,
        "terminal_audit": False,
        "full_648_per_method_audits_still_required": True,
        "adapter_hash": expected_hash,
        "audited_runs": sum(source["snapshot_completed_runs"] for source in sources),
        "algorithm_evaluations": sum(source["algorithm_evaluations"] for source in sources),
        "failures": 0,
        "sources": sources,
    }
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / "audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "objective_calls_by_this_auditor": 0,
                "terminal_audit": False,
                "audited_runs": result["audited_runs"],
                "algorithm_evaluations": result["algorithm_evaluations"],
                "sources": [
                    {key: value for key, value in source.items() if key != "journal_hashes"}
                    for source in sources
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
