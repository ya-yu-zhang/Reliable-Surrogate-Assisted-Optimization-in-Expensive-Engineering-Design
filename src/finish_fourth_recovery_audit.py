"""Wait for formal references to finish, then audit and freeze fourth recovery."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
from time import perf_counter, sleep

from .run_solo_cost import process_inventory


ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / ".venv312/Scripts/python.exe"
OUT = ROOT / "results/fourth_recovery_audit_completion_v1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def execute(module: str, log_name: str) -> None:
    result = subprocess.run([str(CORE), "-m", module], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    (OUT / log_name).write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"{module} exited {result.returncode}; see {log_name}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    status_path = OUT / "status.json"
    if status_path.exists():
        previous = json.loads(status_path.read_text("utf-8"))
        live = {row["ProcessId"] for row in process_inventory()}
        if previous["stage"] != "complete" and previous["pid"] in live:
            raise RuntimeError("Fourth recovery audit helper already live")
    started = perf_counter()
    stage = "waiting_for_formal_gp_ei_completion"
    failure = None
    pipeline_hash = digest(Path(__file__))

    def save() -> None:
        status_path.write_text(json.dumps({
            "stage": stage, "pid": os.getpid(), "pipeline_sha256": pipeline_hash,
            "elapsed": perf_counter() - started, "failure": failure,
            "objective_calls_by_helper": 0,
        }, indent=2), encoding="utf-8")

    try:
        while True:
            live = {row["ProcessId"] for row in process_inventory()}
            gp = json.loads((ROOT / "results/gp_ei_reference_v1/status.json").read_text("utf-8"))
            turbo = json.loads((ROOT / "results/turbo_reference_v1/status.json").read_text("utf-8"))
            for label, status in [("gp_ei", gp), ("turbo", turbo)]:
                if status["stage"] == "failed" or status["failed"]:
                    raise RuntimeError(f"{label} formal batch failed")
                if status["pid"] not in live and status["stage"] != "complete":
                    raise RuntimeError(f"{label} parent ended before completion")
            if all(status["stage"] == "complete" and status["pid"] not in live for status in [gp, turbo]):
                break
            save()
            sleep(30)
        stage = "auditing_fourth_recovery"
        save()
        execute("src.audit_fourth_recovery", "audit.log")
        stage = "freezing_fourth_recovery"
        save()
        execute("src.freeze_fourth_recovery_audit", "freeze.log")
        stage = "complete"
        save()
    except Exception as error:
        failure = {"error_type": type(error).__name__, "error": str(error)}
        stage = "failed"
        save()
        raise


if __name__ == "__main__":
    main()
