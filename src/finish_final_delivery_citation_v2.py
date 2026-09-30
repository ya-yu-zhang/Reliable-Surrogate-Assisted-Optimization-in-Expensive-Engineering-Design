"""Wait for corrected visual acceptance and recovery audit, then run final delivery v2."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from time import perf_counter, sleep

from .run_solo_cost import process_inventory


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/final_delivery_citation_v2_completion"
PREREQUISITES = (
    "results/all_pdf_visual_review_citation_v2/status.json",
    "results/third_recovery_audit_completion_v1/status.json",
)


def main() -> None:
    assert not OUT.exists(), "Citation-corrected final completion exists"
    OUT.mkdir(parents=True)
    started = perf_counter()
    stage = "waiting_for_citation_visual_acceptance_and_recovery_audit"
    failure = None

    def save() -> None:
        (OUT / "status.json").write_text(
            json.dumps(
                {"stage": stage, "pid": os.getpid(), "elapsed": perf_counter() - started, "failure": failure},
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
            ready = (
                statuses[0]["stage"] == "complete"
                and statuses[0]["visual_quality_verified"]
                and statuses[0]["pid"] not in live
                and statuses[1]["stage"] == "complete"
                and statuses[1]["pid"] not in live
            )
            if ready:
                break
            for name, status in zip(PREREQUISITES, statuses):
                if status["pid"] not in live and status["stage"] != "complete":
                    if name.endswith("all_pdf_visual_review_citation_v2/status.json") and status["stage"] == "rendered_pending_visual_inspection":
                        continue
                    raise RuntimeError(f"Prerequisite ended before completion: {name}")
            save()
            sleep(30)

        stage = "final_citation_corrected_cross_artifact_audit"
        save()
        result = subprocess.run(
            [str(ROOT / ".venv312/Scripts/python.exe"), "-m", "src.audit_final_delivery_citation_v2"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        (OUT / "audit.log").write_text(result.stdout + result.stderr, encoding="utf-8")
        if result.returncode:
            raise RuntimeError(f"Final citation-v2 audit exited {result.returncode}")
        audit = json.loads((ROOT / "results/final_delivery_citation_v2_audit/audit.json").read_text("utf-8"))
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
