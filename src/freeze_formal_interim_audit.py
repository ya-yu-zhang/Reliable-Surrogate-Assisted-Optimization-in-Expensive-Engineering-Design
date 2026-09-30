"""Freeze the objective-free interim full-journal audit checkpoint."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "docs/frozen_formal_interim_audit_20260920_v1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert not DEST.exists(), "Formal interim audit freeze already exists"
    audit_path = ROOT / "results/formal_interim_audit_20260920_v1/audit.json"
    audit = json.loads(audit_path.read_text("utf-8"))
    assert audit["objective_calls_by_this_auditor"] == 0
    assert not audit["terminal_audit"] and audit["full_648_per_method_audits_still_required"]
    assert audit["audited_runs"] == 760 and audit["algorithm_evaluations"] == 175100
    assert audit["failures"] == 0
    assert [row["snapshot_completed_runs"] for row in audit["sources"]] == [535, 225]
    assert [row["algorithm_evaluations"] for row in audit["sources"]] == [124000, 51100]

    relative = {
        "src/audit_formal_interim.py",
        "src/analyze_gp_references.py",
        "src/freeze_formal_interim_audit.py",
        "results/formal_interim_audit_20260920_v1/audit.json",
        "docs/正式外部参照中途全日志核查20260920.md",
        "docs/frozen_turbo_reference_v1/sha256.json",
        "docs/frozen_gp_ei_reference_v1/sha256.json",
        "docs/frozen_third_recovery_subset_v1/sha256.json",
        "docs/baselines-environment-lock.txt",
        "configs/turbo_reference.json",
        "configs/gp_ei_reference.json",
    }
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
