"""Archive the fourth interrupted GP-EI prefixes and stale helper states without objective calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

from .run_solo_cost import process_inventory


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "results/interruption_20260920_v4"
SOURCE = "gp_ei_reference_v1"
CONFIG = "configs/gp_ei_reference.json"
HELPERS = [
    "reference_completion_v1", "application_completion_v1", "evidence_export_v1",
    "high_extension_completion_v1", "high_evidence_export_v1",
    "model_sensitivity_completion_v1", "sensitivity_evidence_export_v1",
    "budget_performance_sensitivity_completion_v1", "budget_evidence_export_v1",
    "final_visual_review_v1", "all_pdf_visual_review_v1", "final_delivery_completion_v1",
    "third_recovery_audit_completion_v1", "final_delivery_addendum_completion_v1",
    "citation_revision_completion_v1", "all_pdf_visual_review_citation_v2",
    "final_delivery_citation_v2_completion", "gp_ei_terminal_checkpoint_completion_v1",
    "plan_delivery_bundle_completion_v1", "final_provenance_bundle_completion_v1",
]
RELEVANT_MODULES = {
    "src.resume_interrupted_gp_batch_v4_parallel", "src.resume_interrupted_gp_batch_v5_parallel",
    "src.gp_references", "src.recover_interrupted_run",
    "src.finish_reference_batch", "src.finish_application_batch", "src.finish_evidence_export",
    "src.finish_high_extension", "src.finish_high_evidence_export", "src.finish_model_sensitivity",
    "src.finish_sensitivity_evidence_export", "src.finish_budget_performance_sensitivity",
    "src.finish_budget_evidence_export", "src.finish_final_visual_review",
    "src.finish_all_pdf_visual_review", "src.finish_final_delivery",
    "src.finish_third_recovery_audit", "src.finish_fourth_recovery_audit",
    "src.finish_final_delivery_addendum", "src.finish_citation_revision",
    "src.finish_citation_visual_review_v2", "src.finish_final_delivery_citation_v2",
    "src.finish_gp_ei_terminal_checkpoint", "src.finish_plan_delivery_bundle",
    "src.finish_final_provenance_bundle",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_inside(path: Path, parent: Path) -> Path:
    resolved = path.resolve()
    assert resolved.is_relative_to(parent.resolve()), f"unsafe path: {resolved}"
    return resolved


def inspect_events(path: Path) -> tuple[int, int]:
    events = [json.loads(line) for line in path.read_text("utf-8").splitlines()]
    assert events and events[0]["event"] == "meta"
    pre = [event for event in events if event["event"] == "pre"]
    labels = [event for event in events if event["event"] == "label"]
    assert len(pre) == len(labels) > 0 and len(events) == 1 + 2 * len(labels)
    for number, (before, after) in enumerate(zip(pre, labels), 1):
        assert before["t"] == after["t"] == number
        assert before["n_observed"] == number - 1 and "y" not in before
    return len(labels), len(pre) - len(labels)


def module_from_command(command: str) -> str | None:
    pieces = (command or "").replace('"', "").split()
    try:
        index = pieces.index("-m")
    except ValueError:
        return None
    return pieces[index + 1] if index + 1 < len(pieces) else None


def main() -> None:
    assert not DEST.exists(), "Fourth-interruption archive already exists"
    inventory = process_inventory()
    active = [row for row in inventory if module_from_command(row["CommandLine"] or "") in RELEVANT_MODULES]
    assert not active, f"relevant processes still live: {[row['ProcessId'] for row in active]}"
    results_root = assert_inside(ROOT / "results", ROOT)
    config = json.loads((ROOT / CONFIG).read_text("utf-8"))
    expected = len(config["functions"]) * len(config["dimensions"]) * len(config["instances"]) * config["repeats"]
    assert expected == 648 and Path(config["out"]).name == SOURCE
    base = ROOT / "results" / SOURCE
    status = json.loads((base / "status.json").read_text("utf-8"))
    assert status["stage"] == "running" and status["failed"] == 0
    assert status["completed"] == 534 and status["pid"] not in {row["ProcessId"] for row in inventory}

    complete = 0
    plans = []
    for directory in sorted(path for path in base.iterdir() if path.is_dir()):
        events = directory / "events.jsonl"
        if not events.exists():
            continue
        if (directory / "summary.json").exists():
            summary = json.loads((directory / "summary.json").read_text("utf-8"))
            budget = summary["signature"]["budget"]
            assert summary["algorithm_evaluations"] == budget
            assert len(events.read_text("utf-8").splitlines()) == 1 + 2 * budget
            complete += 1
        else:
            labels, pending = inspect_events(events)
            budget = int(directory.name.rsplit("_b", 1)[1])
            assert labels < budget and pending == 0
            destination = DEST / "partial_runs" / SOURCE / directory.name
            files = {path.name: digest(path) for path in sorted(directory.iterdir()) if path.is_file()}
            plans.append({
                "source": SOURCE, "runid": directory.name, "paid_labels": labels,
                "pending_pre": pending, "original": directory, "destination": destination,
                "file_sha256": files,
            })
    assert complete == 534 and len(plans) == 4
    assert sum(row["paid_labels"] for row in plans) == 716

    DEST.mkdir(parents=True)
    old = DEST / "old_state"
    old.mkdir()
    for name in ["status.json", "failures.json", "recovery_driver_v4.json"]:
        source = base / name
        if source.exists():
            shutil.copy2(source, old / name)
    for row in plans:
        assert_inside(row["original"], results_root)
        assert_inside(row["destination"], results_root)
        row["destination"].parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(row["original"]), str(row["destination"]))
        assert not row["original"].exists() and row["destination"].is_dir()
        assert all(digest(row["destination"] / name) == value for name, value in row["file_sha256"].items())

    for helper in HELPERS:
        source = ROOT / "results" / helper
        assert source.is_dir(), helper
        destination = DEST / "old_helper_states" / helper
        assert_inside(source, results_root)
        assert_inside(destination, results_root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))
        assert not source.exists() and destination.is_dir()
    logs = []
    for source in sorted((ROOT / "results").glob("fourth_*.log")):
        destination = DEST / "old_launcher_logs" / source.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        logs.append({"path": source.relative_to(ROOT).as_posix(), "sha256": digest(source)})

    rows = [{
        "source": row["source"], "runid": row["runid"], "paid_labels": row["paid_labels"],
        "pending_pre": row["pending_pre"],
        "archive": row["destination"].relative_to(ROOT).as_posix(),
        "file_sha256": row["file_sha256"],
    } for row in plans]
    recovery_sources = [
        "src/archive_fourth_interruption.py", "src/resume_interrupted_gp_batch_v5_parallel.py",
        "src/recover_interrupted_run.py", "src/gp_references.py",
        "src/audit_fourth_recovery.py", "configs/gp_ei_reference.json",
    ]
    manifest = {
        "interruption_date": "2026-09-20",
        "observation": "formal GP-EI parent, four workers, and all helper PIDs absent; no scientific failure record",
        "partial_runs": rows,
        "complete_runs_before_interruption": {SOURCE: complete},
        "old_paid_calls": 716,
        "expected_new_physical_calls": 884,
        "all_pre_label_pairs_complete": True,
        "no_pending_physical_return": True,
        "unchanged_budgets_and_scope": True,
        "objective_calls_by_archiver": 0,
        "stale_helper_states_archived": HELPERS,
        "launcher_logs_archived": logs,
        "recovery_sources": {name: digest(ROOT / name) for name in recovery_sources},
    }
    path = DEST / "recovery_manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "partial_runs": len(rows), "old_paid_calls": 716, "new_physical_calls": 884,
        "complete": complete, "helper_states": len(HELPERS), "launcher_logs": len(logs),
        "manifest_sha256": digest(path),
    }, indent=2))


if __name__ == "__main__":
    main()
