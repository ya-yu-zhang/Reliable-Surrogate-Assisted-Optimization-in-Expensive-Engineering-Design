"""Freeze the completed eight-run recovery subset while the full batches continue."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "docs/frozen_third_recovery_subset_v1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert not DEST.exists(), "Third-recovery subset freeze already exists"
    preaudit_path = ROOT / "results/interruption_20260920_v3/third_recovery_subset_pre_audit.json"
    preaudit = json.loads(preaudit_path.read_text("utf-8"))
    assert preaudit["objective_calls_by_this_auditor"] == 0
    assert preaudit["recovered_runs"] == 8
    assert preaudit["saved_labels"] == 2514
    assert preaudit["new_physical_calls"] == 686
    assert preaudit["canonical_algorithm_evaluations"] == 3200
    assert preaudit["redundant_recovery_validation_calls"] == 0
    assert preaudit["all_archived_prefixes_exactly_equal"]
    assert preaudit["all_physical_suffixes_exactly_equal"]

    manifest_path = ROOT / "results/interruption_20260920_v3/recovery_manifest.json"
    manifest = json.loads(manifest_path.read_text("utf-8"))
    relative = {
        "src/preaudit_third_recovery_subset.py",
        "src/freeze_third_recovery_subset.py",
        "src/audit_third_recovery.py",
        "tests/test_third_recovery_audit.py",
        "results/interruption_20260918_v1/recovery_manifest.json",
        "results/interruption_20260919_v2/recovery_manifest.json",
        "results/interruption_20260920_v3/recovery_manifest.json",
        "results/interruption_20260920_v3/third_recovery_subset_pre_audit.json",
        "docs/frozen_final_delivery_addendum_protocol_v1/sha256.json",
    }
    for archived in manifest["partial_runs"]:
        for name in archived["file_sha256"]:
            relative.add(f"{archived['archive']}/{name}")
    for row in preaudit["runs"]:
        base = f"results/{row['source']}/{row['runid']}"
        relative.update(
            {
                f"{base}/events.jsonl",
                f"{base}/summary.json",
                f"{base}/recovery_physical_calls.jsonl",
                f"{base}/recovery.json",
            }
        )

    hashes: dict[str, str] = {}
    for name in sorted(relative):
        source = ROOT / name
        assert source.is_file(), name
        target = DEST / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        hashes[name] = digest(source)
        assert digest(target) == hashes[name]

    manifest_out = DEST / "sha256.json"
    manifest_out.write_text(json.dumps(hashes, ensure_ascii=False, indent=2), encoding="utf-8")
    check = json.loads(manifest_out.read_text("utf-8"))
    assert len(check) == len(hashes)
    assert all(digest(DEST / name) == expected for name, expected in check.items())
    print(json.dumps({"files": len(hashes), "manifest_sha256": digest(manifest_out)}, indent=2))


if __name__ == "__main__":
    main()
