"""Wait for the formal GP-EI audit, then create and freeze its zero-call checkpoint."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
from time import perf_counter, sleep

from .run_solo_cost import process_inventory


ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / ".venv312/Scripts/python.exe"
OUT = ROOT / "results/gp_ei_terminal_checkpoint_completion_v1"
SOURCE = ROOT / "results/gp_ei_reference_v1"
ANALYSIS = ROOT / "results/gp_ei_reference_analysis_v1"
REFERENCE = ROOT / "results/reference_completion_v1/status.json"


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
    inventory = {row["ProcessId"] for row in process_inventory()}
    if status_path.exists():
        previous = json.loads(status_path.read_text("utf-8"))
        if previous["stage"] != "complete" and previous["pid"] in inventory:
            raise RuntimeError("GP-EI terminal checkpoint helper already live; refusing duplicate")
    start = perf_counter()
    stage = "waiting_for_gp_ei_full_raw_audit"
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
            processes = {row["ProcessId"] for row in process_inventory()}
            batch = json.loads((SOURCE / "status.json").read_text("utf-8"))
            if batch["stage"] == "failed" or batch["failed"]:
                raise RuntimeError("GP-EI formal batch failed; refusing checkpoint")
            if batch["pid"] not in processes and batch["stage"] != "complete":
                raise RuntimeError("GP-EI formal parent ended without complete stage")
            reference = json.loads(REFERENCE.read_text("utf-8"))
            required = [ANALYSIS / name for name in [
                "audit.json", "runs.csv", "resource_counts.csv", "source_journal_hashes.json", "warnings.json"
            ]]
            if (
                batch["stage"] == "complete"
                and batch["pid"] not in processes
                and "gp_ei_reference_v1" in reference.get("external_audits_completed", [])
                and all(path.is_file() for path in required)
            ):
                break
            save()
            sleep(30)
        stage = "auditing_terminal_checkpoint"
        save()
        execute("src.audit_gp_ei_terminal_checkpoint", "audit.log")
        stage = "freezing_terminal_checkpoint"
        save()
        execute("src.freeze_gp_ei_terminal_checkpoint", "freeze.log")
        stage = "complete"
        save()
    except Exception as error:
        failure = {"error_type": type(error).__name__, "error": str(error)}
        stage = "failed"
        save()
        raise


if __name__ == "__main__":
    main()
