"""Wait for both final-delivery v1 and third-recovery audit, then run the addendum."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from time import perf_counter, sleep

from .run_solo_cost import process_inventory


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/final_delivery_addendum_completion_v1"
PREREQUISITES = (
    "results/final_delivery_completion_v1/status.json",
    "results/third_recovery_audit_completion_v1/status.json",
)


def main() -> None:
    assert not OUT.exists(), "Final-delivery addendum completion exists; refuse duplicate restart"
    OUT.mkdir(parents=True)
    started = perf_counter()
    stage = "waiting_for_original_delivery_and_third_recovery_audit"
    failure = None

    def save() -> None:
        (OUT / "status.json").write_text(
            json.dumps(
                {
                    "stage": stage,
                    "pid": os.getpid(),
                    "elapsed": perf_counter() - started,
                    "failure": failure,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    try:
        save()
        while True:
            statuses = [json.loads((ROOT / name).read_text("utf-8")) for name in PREREQUISITES]
            live = {row["ProcessId"] for row in process_inventory()}
            for name, status in zip(PREREQUISITES, statuses):
                if status["stage"] == "failed" or status["failure"] is not None:
                    raise RuntimeError(f"Prerequisite failed: {name}")
            if all(status["stage"] == "complete" and status["pid"] not in live for status in statuses):
                break
            for name, status in zip(PREREQUISITES, statuses):
                if status["stage"] != "complete" and status["pid"] not in live:
                    raise RuntimeError(f"Prerequisite ended without completion: {name}")
            save()
            sleep(30)

        stage = "auditing_final_delivery_addendum"
        save()
        result = subprocess.run(
            [str(ROOT / ".venv312/Scripts/python.exe"), "-m", "src.audit_final_delivery_addendum"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        (OUT / "audit.log").write_text(result.stdout + result.stderr, encoding="utf-8")
        if result.returncode:
            raise RuntimeError(f"Final-delivery addendum audit exited {result.returncode}")
        audit = json.loads((ROOT / "results/final_delivery_addendum_audit_v1/audit.json").read_text("utf-8"))
        assert audit["complete"] and audit["objective_calls_by_this_auditor"] == 0
        stage = "complete"
        save()
    except Exception as error:
        failure = {"error_type": type(error).__name__, "error": str(error)}
        stage = "failed"
        save()
        raise


if __name__ == "__main__":
    main()
