"""Run the frozen application batch through its venv-safe entry and audit it."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
from time import perf_counter

from .run_solo_cost import process_inventory


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/application_completion_v1"


def execute(module: str, log: str) -> None:
    result = subprocess.run(
        [str(ROOT / ".venv312/Scripts/python.exe"), "-m", module],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    (OUT / log).write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"{module} exited {result.returncode}; original {log} retained")


def main() -> None:
    if OUT.exists():
        raise RuntimeError("Archived application failure directory must be absent")
    OUT.mkdir(parents=True)
    path = OUT / "status.json"
    own_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    stage = "checking_reference_and_cost_completion"
    failure = None
    started = perf_counter()

    def save() -> None:
        path.write_text(
            json.dumps(
                {
                    "stage": stage,
                    "pid": os.getpid(),
                    "pipeline_sha256": own_hash,
                    "recovery_protocol": "application_venv_self_overlap_v1",
                    "elapsed": perf_counter() - started,
                    "failure": failure,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    try:
        save()
        prior = json.loads((ROOT / "results/reference_completion_v1/status.json").read_text("utf-8"))
        processes = {row["ProcessId"] for row in process_inventory()}
        assert prior["stage"] == "complete" and prior["failure"] is None
        assert prior["pid"] not in processes
        stage = "formal_application_batch"
        save()
        execute("src.application_batch_venv_entry", "formal_application.log")
        stage = "full_raw_application_audit"
        save()
        execute("src.analyze_application", "full_raw_audit.log")
        stage = "complete"
        save()
        print("Application batch and full raw audit complete.", flush=True)
    except Exception as error:
        failure = {"error": str(error)}
        stage = "failed"
        save()
        raise


if __name__ == "__main__":
    main()
