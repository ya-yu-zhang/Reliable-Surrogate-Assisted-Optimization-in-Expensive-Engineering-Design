"""Recover reference postprocessing with the portable ancestor-safe cost entry."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from time import perf_counter

from .finish_reference_batch_launcher_safe import ROOT, OUT, TASKS, execute


def main() -> None:
    if OUT.exists():
        raise RuntimeError("Archived failure directory must be absent before portable recovery")
    OUT.mkdir(parents=True)
    started = perf_counter()
    stage = "auditing_formal_references"
    failure = None
    completed: list[str] = []
    own_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    status_path = OUT / "status.json"

    def save() -> None:
        status_path.write_text(
            json.dumps(
                {
                    "stage": stage,
                    "pid": os.getpid(),
                    "pipeline_sha256": own_hash,
                    "recovery_protocol": "portable_ancestor_safe_solo_cost_v2",
                    "external_audits_completed": sorted(completed),
                    "elapsed": perf_counter() - started,
                    "failure": failure,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    try:
        save()
        for source, destination in TASKS:
            batch = json.loads((ROOT / "results" / source / "status.json").read_text("utf-8"))
            assert batch["stage"] == "complete"
            assert batch["completed"] == batch["expected"] == 648
            assert batch["failed"] == 0
            execute(
                "src.analyze_gp_references",
                ["--source", "results/" + source, "--out", "results/" + destination],
                source + "_audit.log",
            )
            completed.append(source)
            save()
        stage = "serial_cost_measurement"
        save()
        execute("src.run_solo_cost_portable", [], "solo_cost_measurement.log")
        stage = "serial_cost_audit"
        save()
        execute("src.analyze_solo_cost", [], "solo_cost_audit.log")
        stage = "complete"
        save()
        print("Reference audits and portable ancestor-safe serial cost audit complete.", flush=True)
    except Exception as error:
        failure = {"error": str(error)}
        stage = "failed"
        save()
        raise


if __name__ == "__main__":
    main()
