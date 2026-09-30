"""Wait for plan closure, then generate the final provenance and freeze audit."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
from time import perf_counter, sleep

from .run_solo_cost import process_inventory


ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / ".venv312/Scripts/python.exe"
OUT = ROOT / "results/final_provenance_bundle_completion_v1"
UPSTREAM = ROOT / "results/plan_delivery_bundle_completion_v1/status.json"


def execute(module: str, log_name: str) -> None:
    result = subprocess.run(
        [str(CORE), "-m", module], cwd=ROOT, capture_output=True,
        text=True, encoding="utf-8", errors="replace",
    )
    (OUT / log_name).write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"{module} exited {result.returncode}; see {log_name}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    status_path = OUT / "status.json"
    live = {row["ProcessId"] for row in process_inventory()}
    if status_path.exists():
        previous = json.loads(status_path.read_text("utf-8"))
        if previous["stage"] != "complete" and previous["pid"] in live:
            raise RuntimeError("Final provenance helper already live; refusing duplicate")
    start = perf_counter()
    stage = "waiting_for_original_plan_delivery_bundle"
    failure = None

    def save() -> None:
        status_path.write_text(json.dumps({
            "stage": stage,
            "pid": os.getpid(),
            "elapsed": perf_counter() - start,
            "failure": failure,
            "objective_calls_by_helper": 0,
        }, indent=2), encoding="utf-8")

    try:
        while True:
            upstream = json.loads(UPSTREAM.read_text("utf-8"))
            live = {row["ProcessId"] for row in process_inventory()}
            if upstream["stage"] == "failed" or upstream["failure"] is not None:
                raise RuntimeError("Original-plan delivery bundle failed")
            if upstream["stage"] == "complete" and upstream["pid"] not in live:
                break
            if upstream["pid"] not in live:
                raise RuntimeError("Original-plan delivery parent ended before completion")
            save()
            sleep(30)
        stage = "auditing_final_provenance"
        save()
        execute("src.audit_final_provenance_bundle", "audit.log")
        stage = "freezing_final_provenance"
        save()
        execute("src.freeze_final_provenance_bundle", "freeze.log")
        stage = "complete"
        save()
    except Exception as error:
        failure = {"error_type": type(error).__name__, "error": str(error)}
        stage = "failed"
        save()
        raise


if __name__ == "__main__":
    main()
