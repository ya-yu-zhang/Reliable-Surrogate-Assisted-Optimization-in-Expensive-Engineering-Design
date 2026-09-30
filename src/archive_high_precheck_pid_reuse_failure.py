"""Archive the zero-call high-dimensional precheck PID-reuse refusal."""

import hashlib
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "results/high_extension_completion_v1"
ARCHIVE = ROOT / "results/high_precheck_pid_reuse_failure_20260922_v1"


def main():
    assert not ARCHIVE.exists()
    status = json.loads((SOURCE / "status.json").read_text("utf-8"))
    assert status["stage"] == "failed" and status["resource_point_calls"] == 0
    assert not (ROOT / "results/application_high_precheck_v1").exists()
    ARCHIVE.mkdir(); shutil.move(str(SOURCE), str(ARCHIVE / SOURCE.name))
    logs = []
    for name in ("nineteenth_high_extension_stdout.log", "nineteenth_high_extension_stderr.log"):
        path = ROOT / "results" / name; assert path.exists(); shutil.move(str(path), str(ARCHIVE / name)); logs.append(name)
    files = sorted(path for path in ARCHIVE.rglob("*") if path.is_file())
    manifest = {"schema": "high_precheck_pid_reuse_failure_archive_v1", "objective_calls": 0,
                "files": {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in files}}
    (ARCHIVE / "archive_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
