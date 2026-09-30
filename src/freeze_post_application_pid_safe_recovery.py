"""Freeze the narrow post-application PID-safe representation recovery."""

import hashlib
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "docs/frozen_post_application_pid_safe_recovery_v1"
FILES = [
    "src/build_integrated_manuscripts_pid_safe.py",
    "src/finish_evidence_export_pid_safe.py",
    "src/archive_post_application_pid_reuse_failure.py",
    "tests/test_integrated_pid_safe.py",
    "results/post_application_pid_reuse_failure_20260922_v1/archive_manifest.json",
]


def main():
    assert not DEST.exists(); DEST.mkdir()
    hashes = {}
    for name in FILES:
        source = ROOT / name; target = DEST / name
        target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(source, target)
        hashes[name] = hashlib.sha256(source.read_bytes()).hexdigest()
    (DEST / "sha256.json").write_text(json.dumps(hashes, indent=2), encoding="utf-8")
    print(json.dumps({"schema": "post_application_pid_safe_recovery_freeze_v1",
                      "files": len(hashes)}, indent=2))


if __name__ == "__main__":
    main()
