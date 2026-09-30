"""Run the frozen manuscript builder while distinguishing PID reuse from a live pipeline."""

from __future__ import annotations

import json

from . import build_integrated_manuscripts as builder


IDENTITIES = {
    "reference_completion_v1": (
        "src.finish_reference_batch", "src.finish_reference_after_fourth_recovery",
        "src.finish_reference_after_fifth_recovery", "src.resume_reference",
        "src.run_solo_cost", "src.solo_cost", "src.run_gp_batch", "src.gp_references",
    ),
    "application_completion_v1": (
        "src.finish_application", "src.run_application_batch", "src.application_experiment",
        "src.application_batch_pid_reuse_entry", "src.resume_application",
        "src.recover_interrupted_application_run",
    ),
    "evidence_export_v1": (
        "src.finish_evidence_export", "src.finish_evidence_export_pid_safe",
        "src.build_integrated_manuscripts", "src.build_integrated_manuscripts_pid_safe",
    ),
}


def pid_safe_inventory(root, inventory):
    """Drop a same-PID process only when its command is unrelated to that completed pipeline."""
    reused = set()
    for stem, identities in IDENTITIES.items():
        path = root / "results" / stem / "status.json"
        if not path.exists():
            continue
        status = json.loads(path.read_text("utf-8"))
        if status["stage"] != "complete" or status["failure"] is not None:
            continue
        matches = [row for row in inventory if row["ProcessId"] == status["pid"]]
        if matches and not any(any(identity in (row["CommandLine"] or "") for identity in identities)
                               for row in matches):
            reused.add(status["pid"])
    return [row for row in inventory if row["ProcessId"] not in reused]


def main():
    original = builder.process_inventory
    builder.process_inventory = lambda: pid_safe_inventory(builder.ROOT, original())
    builder.main()


if __name__ == "__main__":
    main()
