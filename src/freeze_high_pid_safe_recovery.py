import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "docs/frozen_high_pid_safe_recovery_v1"
FILES = ["src/build_integrated_manuscripts_pid_safe.py", "src/application_high_precheck_pid_safe.py",
         "src/finish_high_extension_pid_safe.py", "src/archive_high_precheck_pid_reuse_failure.py",
         "tests/test_integrated_pid_safe.py", "results/high_precheck_pid_reuse_failure_20260922_v1/archive_manifest.json"]

def main():
    assert not DEST.exists(); DEST.mkdir(); rows = {}
    for name in FILES:
        source = ROOT / name; target = DEST / name; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target); rows[name] = hashlib.sha256(source.read_bytes()).hexdigest()
    (DEST / "sha256.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")

if __name__ == "__main__": main()
