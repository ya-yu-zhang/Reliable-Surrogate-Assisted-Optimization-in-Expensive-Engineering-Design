"""Resume the frozen scheduler after paid-prefix recovery and complete both audits."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
from time import perf_counter


ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / ".venv312/Scripts/python.exe"
OUT = ROOT / "results/application_completion_v1"
FORMAL = ROOT / "results/application_formal_v1"


def main() -> None:
    assert not OUT.exists()
    assert sum((path / "summary.json").is_file() for path in FORMAL.iterdir() if path.is_dir()) == 289
    driver = json.loads((FORMAL / "recovery_driver_v2.json").read_text("utf-8"))
    assert driver["old_paid_calls"] == 1368 and driver["new_paid_calls"] == 632
    recovery_audit = json.loads((ROOT / "results/application_recovery_audit_v1/audit.json").read_text("utf-8"))
    assert recovery_audit["complete"] and recovery_audit["objective_calls_by_auditor"] == 0
    OUT.mkdir()
    started = perf_counter()
    stage = "resuming_formal_application_batch_after_pid_reuse"
    failure = None

    def save() -> None:
        (OUT / "status.json").write_text(json.dumps({
            "stage": stage, "pid": os.getpid(), "elapsed": perf_counter() - started,
            "failure": failure, "recovery_protocol": "application_pid_reuse_recovery_v1",
        }, indent=2), encoding="utf-8")

    def execute(module: str, log: str) -> None:
        result = subprocess.run([str(CORE), "-m", module], cwd=ROOT, capture_output=True,
                                text=True, encoding="utf-8", errors="replace")
        (OUT / log).write_text(result.stdout + result.stderr, encoding="utf-8")
        if result.returncode:
            raise RuntimeError(f"{module} failed with exit code {result.returncode}")

    try:
        save()
        execute("src.application_batch_pid_reuse_entry", "batch.log")
        stage = "full_raw_application_audit"; save()
        execute("src.analyze_application", "full_raw_audit.log")
        stage = "rechecking_paid_prefix_recovery_audit"; save()
        audit = json.loads((ROOT / "results/application_recovery_audit_v1/audit.json").read_text("utf-8"))
        assert audit["complete"] and audit["saved_paid_labels"] == 1368 and audit["new_physical_calls"] == 632
        stage = "complete"; save()
    except Exception as exc:
        failure = {"error_type": type(exc).__name__, "error": str(exc)}
        stage = "failed"; save(); raise


if __name__ == "__main__":
    main()
