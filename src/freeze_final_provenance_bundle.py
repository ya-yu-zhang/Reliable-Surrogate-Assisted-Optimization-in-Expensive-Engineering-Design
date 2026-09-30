"""Freeze the terminal provenance audit; no later protocol layer is expected."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "docs/frozen_final_provenance_bundle_v1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert not DEST.exists(), "Final provenance bundle already frozen"
    audit_path = ROOT / "results/final_provenance_bundle_audit_v1/audit.json"
    audit = json.loads(audit_path.read_text("utf-8"))
    assert audit["complete"] and audit["objective_calls_by_this_auditor"] == 0
    assert audit["upstream_plan_delivery_complete"]
    assert not audit["unexpected_live_mismatches"] and not audit["unexpected_copy_issues"]
    assert len(audit["authorized_dynamic_live_drift"]) == 1
    assert len(audit["known_missing_old_flat_copies"]) == 2

    relative = [
        "src/audit_final_provenance_bundle.py",
        "src/finish_final_provenance_bundle.py",
        "src/freeze_final_provenance_bundle.py",
        "results/final_provenance_bundle_audit_v1/audit.json",
        "paper/final_provenance_manifest.json",
        "docs/最终来源与冻结完整性核查.md",
        "docs/最终来源索引协议20260920.md",
        "docs/frozen_final_provenance_bundle_protocol_v1/sha256.json",
        "results/plan_delivery_bundle_audit_v1/audit.json",
        "paper/plan_delivery_bundle_manifest.json",
    ]
    hashes = {}
    for name in relative:
        source = ROOT / name
        assert source.is_file(), name
        target = DEST / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        hashes[name] = digest(source)
        assert digest(target) == hashes[name]
    manifest = DEST / "sha256.json"
    manifest.write_text(json.dumps(hashes, ensure_ascii=False, indent=2), encoding="utf-8")
    assert all(digest(DEST / name) == expected for name, expected in json.loads(manifest.read_text("utf-8")).items())
    print(json.dumps({"files": len(hashes), "manifest_sha256": digest(manifest)}, indent=2))


if __name__ == "__main__":
    main()
