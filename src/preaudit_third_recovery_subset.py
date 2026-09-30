"""Audit and record the eight completed third-recovery trajectories before full batches end."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .audit_third_recovery import audit_run, digest


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/interruption_20260920_v3/third_recovery_subset_pre_audit.json"


def main() -> None:
    assert not OUT.exists(), "Third-recovery subset pre-audit already exists"
    manifest_path = ROOT / "results/interruption_20260920_v3/recovery_manifest.json"
    manifest = json.loads(manifest_path.read_text("utf-8"))
    assert len(manifest["partial_runs"]) == 8
    assert manifest["old_paid_calls"] == 2514
    for name, expected in manifest["recovery_sources"].items():
        assert digest(ROOT / name) == expected

    prior_ids: set[str] = set()
    prior_manifest_hashes = {}
    for relative in (
        "results/interruption_20260918_v1/recovery_manifest.json",
        "results/interruption_20260919_v2/recovery_manifest.json",
    ):
        path = ROOT / relative
        prior = json.loads(path.read_text("utf-8"))
        prior_ids.update(row["runid"] for row in prior["partial_runs"])
        prior_manifest_hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()

    rows = [audit_run(ROOT, row, prior_ids) for row in manifest["partial_runs"]]
    result = {
        "schema": "third_recovery_subset_pre_audit_v1",
        "full_formal_batches_required_for_final_audit": True,
        "objective_calls_by_this_auditor": 0,
        "recovered_runs": len(rows),
        "saved_labels": sum(row["archive_paid_labels"] for row in rows),
        "new_physical_calls": sum(row["new_physical_calls"] for row in rows),
        "canonical_algorithm_evaluations": sum(row["canonical_algorithm_evaluations"] for row in rows),
        "redundant_recovery_validation_calls": sum(row["redundant_recovery_validation_calls"] for row in rows),
        "all_archived_prefixes_exactly_equal": all(row["archived_prefix_exactly_equal"] for row in rows),
        "all_physical_suffixes_exactly_equal": all(row["physical_suffix_exactly_equal"] for row in rows),
        "third_manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "prior_manifest_sha256": prior_manifest_hashes,
        "runs": rows,
    }
    assert result["recovered_runs"] == 8
    assert result["saved_labels"] == 2514
    assert result["new_physical_calls"] == 686
    assert result["canonical_algorithm_evaluations"] == 3200
    assert result["redundant_recovery_validation_calls"] == 0
    assert result["all_archived_prefixes_exactly_equal"]
    assert result["all_physical_suffixes_exactly_equal"]
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "runs"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
