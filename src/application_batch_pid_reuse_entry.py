"""Run the frozen application batch while rejecting only an identity-matched live prerequisite."""

from __future__ import annotations

import json
import os

from . import run_application_batch as batch
from .run_solo_cost import process_inventory


def prerequisite():
    path = batch.ROOT / "results/reference_completion_v1/status.json"
    status = json.loads(path.read_text("utf-8"))
    assert status["stage"] == "complete" and status["failure"] is None
    processes = process_inventory()
    same_pid = [row for row in processes if row["ProcessId"] == status["pid"]]
    prerequisite_names = (
        "src.finish_reference_batch", "src.finish_reference_after_fourth_recovery",
        "src.finish_reference_after_fifth_recovery", "src.resume_reference",
        "src.run_solo_cost", "src.solo_cost",
    )
    assert not any(any(name in (row["CommandLine"] or "") for name in prerequisite_names)
                   for row in same_pid), "Identity-matched reference/cost pipeline is still live"
    forbidden = [
        "src.run_gp_batch", "src.gp_references", "src.run_solo_cost", "src.solo_cost",
        "src.run_application_batch", "src.application_experiment", "src.mechanism_pipeline",
        "src.experiment", "src.diagnostics", "src.basic_references", "src.application_precheck",
    ]
    assert not any(row["ProcessId"] != os.getpid() and any(
        "-m " + name in (row["CommandLine"] or "") for name in forbidden
    ) for row in processes), "Scientific batch already active"
    audit = json.loads((batch.ROOT / "results/solo_cost_analysis_v1/integrity_audit.json").read_text("utf-8"))
    assert audit["runs"] == 54 and audit["complete_design"] and audit["source_hashes_verified"]
    return status


def main() -> None:
    batch.prerequisite = prerequisite
    batch.main()


if __name__ == "__main__":
    main()
