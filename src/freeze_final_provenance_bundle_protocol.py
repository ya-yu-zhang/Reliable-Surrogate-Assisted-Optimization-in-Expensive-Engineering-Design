"""Freeze the terminal provenance protocol before its waiter starts."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "docs/frozen_final_provenance_bundle_protocol_v1"
FILES = [
    "src/audit_final_provenance_bundle.py",
    "src/finish_final_provenance_bundle.py",
    "src/freeze_final_provenance_bundle.py",
    "src/freeze_final_provenance_bundle_protocol.py",
    "tests/test_final_provenance_bundle.py",
    "docs/最终来源索引协议20260920.md",
    "src/audit_global_freezes_v3.py",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert not DEST.exists(), "Final provenance protocol already frozen"
    hashes = {}
    for name in FILES:
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
