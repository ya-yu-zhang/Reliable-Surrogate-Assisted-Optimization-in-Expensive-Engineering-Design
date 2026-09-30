"""Freeze the second application interruption recovery before suffix calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/frozen_application_second_interruption_protocol_v1"
FILES = [
    "docs/应用正式批次第二次中断恢复协议20260922.md",
    "src/archive_application_second_interruption.py", "src/audit_application_recovery_v2.py",
    "src/resume_application_after_second_interruption_v4.py", "src/freeze_application_second_interruption_protocol.py",
    "src/recover_interrupted_application_run.py", "src/application_batch_pid_reuse_entry.py",
    "src/run_application_batch.py", "src/analyze_application.py", "configs/application_formal.json",
    "docs/frozen_application_formal_v1/sha256.json", "docs/frozen_application_pid_reuse_protocol_v1/sha256.json",
    "results/application_interruption_20260922_v2/archive_manifest.json",
    "results/application_recovery_audit_v1/audit.json",
]


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert not OUT.exists(); manifest = {name: digest(ROOT / name) for name in FILES}
    for name in FILES:
        target = OUT / name; target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(ROOT / name, target)
    (OUT / "sha256.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    assert all(digest(OUT / name) == value for name, value in manifest.items())
    print(json.dumps({"files": len(manifest), "manifest": digest(OUT / "sha256.json")}, indent=2))


if __name__ == "__main__": main()
