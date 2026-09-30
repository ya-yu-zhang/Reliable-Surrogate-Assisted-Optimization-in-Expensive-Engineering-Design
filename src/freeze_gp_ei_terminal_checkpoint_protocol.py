"""Freeze the GP-EI terminal-checkpoint protocol before its waiter is launched."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "docs/frozen_gp_ei_terminal_checkpoint_protocol_v1"
FILES = [
    "src/audit_gp_ei_terminal_checkpoint.py",
    "src/freeze_gp_ei_terminal_checkpoint.py",
    "src/finish_gp_ei_terminal_checkpoint.py",
    "src/freeze_gp_ei_terminal_checkpoint_protocol.py",
    "tests/test_gp_ei_terminal_checkpoint.py",
    "docs/GP-EI终态审计检查点20260920.md",
    "configs/gp_ei_reference.json",
    "src/analyze_gp_references.py",
    "docs/baselines-environment-lock.txt",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert not DEST.exists(), "GP-EI terminal checkpoint protocol already frozen"
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
    assert all(digest(DEST / name) == value for name, value in json.loads(manifest.read_text("utf-8")).items())
    print(json.dumps({"files": len(hashes), "manifest_sha256": digest(manifest)}, indent=2))


if __name__ == "__main__":
    main()
