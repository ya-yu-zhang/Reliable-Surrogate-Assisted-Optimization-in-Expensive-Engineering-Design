"""Wait for page-addressed visual acceptance, then run the final audit once."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
from time import perf_counter, sleep

from .run_solo_cost import process_inventory


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/final_delivery_completion_v1"


def main():
    assert not OUT.exists(), "Final delivery completion record exists; refuse duplicate restart"
    frozen = json.loads((ROOT / "docs/frozen_final_delivery_v1/sha256.json").read_text("utf-8"))
    assert all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == value for name, value in frozen.items())
    OUT.mkdir(parents=True)
    stage = "waiting_for_page_addressed_visual_acceptance"
    failure = None
    start = perf_counter()

    def save():
        (OUT / "status.json").write_text(
            json.dumps(dict(stage=stage, pid=os.getpid(), elapsed=perf_counter() - start, failure=failure), indent=2),
            encoding="utf-8",
        )

    try:
        save()
        while True:
            prior = json.loads((ROOT / "results/all_pdf_visual_review_v1/status.json").read_text("utf-8"))
            alive = {process["ProcessId"] for process in process_inventory()}
            if prior["stage"] == "failed" or prior["failure"] is not None:
                raise RuntimeError("All-PDF visual prerequisite failed")
            if prior["stage"] == "complete" and prior["visual_quality_verified"] and prior["pid"] not in alive:
                break
            if prior["pid"] in alive or prior["stage"] == "rendered_pending_visual_inspection":
                save()
                sleep(30)
                continue
            raise RuntimeError("Visual-review state ended without page-addressed acceptance")
        assert all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == value for name, value in frozen.items())
        stage = "final_cross_artifact_audit"
        save()
        result = subprocess.run(
            [str(ROOT / ".venv312/Scripts/python.exe"), "-m", "src.audit_final_delivery"],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        (OUT / "audit.log").write_text(result.stdout + result.stderr, encoding="utf-8")
        if result.returncode:
            raise RuntimeError(f"Final audit exited {result.returncode}; retained audit.log")
        audit = json.loads((ROOT / "results/final_delivery_audit_v1/audit.json").read_text("utf-8"))
        assert audit["complete"] and audit["objective_calls_by_this_auditor"] == 0
        stage = "complete"
        save()
        print("Final cross-artifact audit complete.", flush=True)
    except Exception as error:
        failure = dict(error_type=type(error).__name__, error=str(error))
        stage = "failed"
        save()
        raise


if __name__ == "__main__":
    main()
