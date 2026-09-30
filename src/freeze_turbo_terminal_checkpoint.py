"""Freeze the completed TuRBO terminal audit checkpoint without duplicating raw journals."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "docs/frozen_turbo_terminal_checkpoint_v1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert not DEST.exists(), "TuRBO terminal checkpoint freeze already exists"
    audit_path = ROOT / "results/turbo_reference_terminal_checkpoint_v1/audit.json"
    audit = json.loads(audit_path.read_text("utf-8"))
    assert audit["objective_calls_by_this_auditor"] == 0
    assert audit["terminal_status_verified"] and audit["formal_parent_absent"]
    assert audit["complete_design_verified"] and audit["audited_runs"] == 648
    assert audit["algorithm_evaluations"] == 151200 and audit["failures"] == 0
    assert audit["raw_journal_hashes_verified"] == audit["raw_summary_hashes_verified"] == 648

    relative = {
        "src/audit_turbo_terminal_checkpoint.py",
        "src/freeze_turbo_terminal_checkpoint.py",
        "src/analyze_gp_references.py",
        "results/turbo_reference_terminal_checkpoint_v1/audit.json",
        "results/turbo_reference_v1/status.json",
        "results/turbo_reference_v1/manifest.json",
        "results/turbo_reference_v1/failures.json",
        "results/turbo_reference_v1/recovery_driver_v4.json",
        "docs/TuRBO终态审计检查点20260920.md",
        "docs/frozen_turbo_reference_v1/sha256.json",
        "docs/frozen_third_recovery_subset_v1/sha256.json",
        "configs/turbo_reference.json",
        "docs/baselines-environment-lock.txt",
    }
    relative.update(audit["analysis_files"])
    hashes: dict[str, str] = {}
    for name in sorted(relative):
        source = ROOT / name
        assert source.is_file(), name
        target = DEST / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        hashes[name] = digest(source)
        assert digest(target) == hashes[name]
    manifest = DEST / "sha256.json"
    manifest.write_text(json.dumps(hashes, ensure_ascii=False, indent=2), encoding="utf-8")
    check = json.loads(manifest.read_text("utf-8"))
    assert len(check) == len(hashes)
    assert all(digest(DEST / name) == expected for name, expected in check.items())
    print(json.dumps({"files": len(hashes), "manifest_sha256": digest(manifest)}, indent=2))


if __name__ == "__main__":
    main()
