"""Freeze application interruption recovery before any suffix calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/frozen_application_interruption_protocol_v1"
FILES = [
    "docs/应用正式批次中断恢复协议20260921.md",
    "src/recover_interrupted_application_run.py", "src/archive_application_interruption.py",
    "src/resume_application_batch_v2.py", "src/audit_application_recovery.py",
    "src/freeze_application_interruption_protocol.py",
    "tests/test_application_paid_prefix_recovery.py",
    "src/application_experiment.py", "src/application_methods.py",
    "src/application_batch_venv_entry.py", "src/run_application_batch.py",
    "configs/application_formal.json", "docs/frozen_application_formal_v1/sha256.json",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert not OUT.exists()
    manifest = {name: digest(ROOT / name) for name in FILES}
    for name in FILES:
        target = OUT / name; target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(ROOT / name, target)
    (OUT / "sha256.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    assert all(digest(OUT / name) == value for name, value in manifest.items())
    print(json.dumps({"files": len(manifest), "manifest": digest(OUT / "sha256.json")}, indent=2))


if __name__ == "__main__":
    main()
