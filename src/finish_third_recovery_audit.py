"""Wait for both formal reference recoveries, then audit and freeze them once."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from time import perf_counter, sleep

from .run_solo_cost import process_inventory


ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv-baselines/Scripts/python.exe"
OUT = ROOT / "results/third_recovery_audit_completion_v1"
SOURCES = ("turbo_reference_v1", "gp_ei_reference_v1")


def execute(module: str, log_name: str) -> None:
    result = subprocess.run(
        [str(PYTHON), "-m", module],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    (OUT / log_name).write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"{module} exited {result.returncode}; see {log_name}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=False)
    started = perf_counter()
    own_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    status_path = OUT / "status.json"
    stage = "waiting_for_both_formal_recoveries"
    failure = None

    def save() -> None:
        status_path.write_text(
            json.dumps(
                {
                    "stage": stage,
                    "pid": os.getpid(),
                    "pipeline_sha256": own_hash,
                    "elapsed": perf_counter() - started,
                    "failure": failure,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    try:
        while True:
            live = {row["ProcessId"] for row in process_inventory()}
            statuses = []
            for source in SOURCES:
                status = json.loads((ROOT / "results" / source / "status.json").read_text("utf-8"))
                if status["stage"] == "failed" or status["failed"]:
                    raise RuntimeError(f"{source} failed; third-recovery audit will not run")
                statuses.append(status)
            if all(
                status["stage"] == "complete"
                and status["completed"] == status["expected"] == 648
                and status["pid"] not in live
                for status in statuses
            ):
                break
            for source, status in zip(SOURCES, statuses):
                if status["stage"] != "complete" and status["pid"] not in live:
                    raise RuntimeError(f"{source} ended without a complete status")
            save()
            sleep(30)

        stage = "auditing_third_recovery"
        save()
        execute("src.audit_third_recovery", "audit.log")
        stage = "freezing_third_recovery_audit"
        save()
        execute("src.freeze_third_recovery_audit", "freeze.log")
        stage = "complete"
        save()
    except Exception as error:
        failure = {"error_type": type(error).__name__, "error": str(error)}
        stage = "failed"
        save()
        raise


if __name__ == "__main__":
    main()
