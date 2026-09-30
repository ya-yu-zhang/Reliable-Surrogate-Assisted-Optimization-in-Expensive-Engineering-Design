"""Freeze the third global integrity audit and every manifest it inspected."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "docs/frozen_global_freeze_audit_20260920_v3"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert not DEST.exists(), "Third global-freeze audit snapshot already exists"
    audit_path = ROOT / "results/freeze_integrity_20260920_v3/audit.json"
    audit = json.loads(audit_path.read_text("utf-8"))
    assert audit["objective_calls"] == 0
    assert audit["manifests"] == 29
    assert audit["all_live_originals_match"]
    assert audit["all_present_frozen_copies_match"]
    assert not audit["live_mismatches"] and not audit["unexpected_copy_issues"]

    relative = {
        "src/audit_global_freezes_v3.py",
        "src/freeze_global_freeze_audit_v3.py",
        "tests/test_global_freeze_audit_v3.py",
        "results/freeze_integrity_20260920_v3/audit.json",
        "docs/冻结完整性全局核查第三次20260920.md",
    }
    relative.update(f"docs/{row['freeze']}/sha256.json" for row in audit["rows"])
    hashes: dict[str, str] = {}
    for name in sorted(relative):
        source = ROOT / name
        assert source.is_file(), name
        target = DEST / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        hashes[name] = digest(source)
        assert digest(target) == hashes[name]

    manifest_path = DEST / "sha256.json"
    manifest_path.write_text(json.dumps(hashes, ensure_ascii=False, indent=2), encoding="utf-8")
    check = json.loads(manifest_path.read_text("utf-8"))
    assert len(check) == len(hashes)
    assert all(digest(DEST / name) == expected for name, expected in check.items())
    print(json.dumps({"files": len(hashes), "manifest_sha256": digest(manifest_path)}, indent=2))


if __name__ == "__main__":
    main()
