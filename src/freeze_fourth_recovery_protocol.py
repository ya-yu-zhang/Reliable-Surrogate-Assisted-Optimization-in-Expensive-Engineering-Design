"""Freeze fourth-interruption recovery inputs before relaunch."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "docs/frozen_fourth_recovery_protocol_v1"
FILES = [
    "src/archive_fourth_interruption.py", "src/resume_interrupted_gp_batch_v5_parallel.py",
    "src/audit_fourth_recovery.py", "src/finish_fourth_recovery_audit.py",
    "src/freeze_fourth_recovery_audit.py", "src/freeze_fourth_recovery_protocol.py",
    "src/recover_interrupted_run.py", "src/gp_references.py", "tests/test_fourth_recovery.py",
    "configs/gp_ei_reference.json", "docs/第四次中断恢复执行协议20260920.md",
    "results/interruption_20260920_v4/recovery_manifest.json",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert not DEST.exists(), "Fourth recovery protocol already frozen"
    hashes = {}
    for name in FILES:
        source = ROOT / name
        assert source.is_file(), name
        target = DEST / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        hashes[name] = digest(source)
        assert digest(target) == hashes[name]
    path = DEST / "sha256.json"
    path.write_text(json.dumps(hashes, ensure_ascii=False, indent=2), encoding="utf-8")
    assert all(digest(DEST / name) == expected for name, expected in json.loads(path.read_text("utf-8")).items())
    print(json.dumps({"files": len(hashes), "manifest_sha256": digest(path)}, indent=2))


if __name__ == "__main__":
    main()
