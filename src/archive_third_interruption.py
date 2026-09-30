"""Archive the third interrupted prefixes and stale helper states without objective calls."""
import hashlib
import json
from pathlib import Path
import re
import shutil

from .run_solo_cost import process_inventory


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "results/interruption_20260920_v3"
SOURCES = [
    ("turbo_reference_v1", "configs/turbo_reference.json"),
    ("gp_ei_reference_v1", "configs/gp_ei_reference.json"),
]
HELPERS = [
    "reference_completion_v1", "application_completion_v1", "evidence_export_v1",
    "high_extension_completion_v1", "high_evidence_export_v1",
    "model_sensitivity_completion_v1", "sensitivity_evidence_export_v1",
    "budget_performance_sensitivity_completion_v1", "budget_evidence_export_v1",
    "final_visual_review_v1", "all_pdf_visual_review_v1", "final_delivery_completion_v1",
]
LAUNCHER_LOGS = [
    "budget_evidence_launcher_stderr.log", "budget_evidence_launcher_stdout.log",
    "final_visual_launcher_stdout.log", "final_visual_launcher_stderr.log",
    "all_pdf_visual_launcher_stdout.log", "all_pdf_visual_launcher_stderr.log",
    "final_delivery_launcher_stdout.log", "final_delivery_launcher_stderr.log",
]
MODULE = re.compile(
    r'^\s*(?:"[^"]*python(?:\.exe)?"|\S*python(?:\.exe)?)\s+-m\s+'
    r'(?:src\.resume_interrupted_gp_batch_v4_parallel|src\.gp_references|src\.recover_interrupted_run|'
    r'src\.finish_reference_batch|src\.finish_application_batch|src\.finish_evidence_export|'
    r'src\.finish_high_extension|src\.finish_high_evidence_export|src\.finish_model_sensitivity|'
    r'src\.finish_sensitivity_evidence_export|src\.finish_budget_performance_sensitivity|'
    r'src\.finish_budget_evidence_export|src\.finish_final_visual_review|'
    r'src\.finish_all_pdf_visual_review|src\.finish_final_delivery)\b',
    re.I,
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_inside(path: Path, parent: Path):
    resolved = path.resolve()
    assert resolved.is_relative_to(parent.resolve()), f"unsafe path: {resolved}"
    return resolved


def inspect_events(path: Path):
    events = [json.loads(line) for line in path.read_text("utf-8").splitlines()]
    assert events and events[0]["event"] == "meta"
    pre = [event for event in events if event["event"] == "pre"]
    labels = [event for event in events if event["event"] == "label"]
    assert len(pre) == len(labels) > 0 and len(events) == 1 + 2 * len(labels)
    for number, (before, after) in enumerate(zip(pre, labels), 1):
        assert before["t"] == after["t"] == number
        assert before["n_observed"] == number - 1 and "y" not in before
    return len(labels), len(pre) - len(labels)


def main():
    assert not DEST.exists(), "Third-interruption archive already exists"
    active = [row for row in process_inventory() if MODULE.search(row["CommandLine"] or "")]
    assert not active, f"relevant processes still live: {[row['ProcessId'] for row in active]}"
    assert_inside(ROOT / "results", ROOT)
    plans = []
    complete_counts = {}
    old_calls = 0
    for source, config_name in SOURCES:
        config = json.loads((ROOT / config_name).read_text("utf-8"))
        expected = len(config["functions"]) * len(config["dimensions"]) * len(config["instances"]) * config["repeats"] * len(config["methods"])
        assert expected == 648 and Path(config["out"]).name == source
        base = ROOT / "results" / source
        status = json.loads((base / "status.json").read_text("utf-8"))
        assert status["stage"] == "running" and status["failed"] == 0
        assert status["pid"] not in {row["ProcessId"] for row in process_inventory()}
        complete = 0
        partial = []
        for directory in sorted(path for path in base.iterdir() if path.is_dir()):
            events = directory / "events.jsonl"
            if not events.exists():
                continue
            if (directory / "summary.json").exists():
                summary = json.loads((directory / "summary.json").read_text("utf-8"))
                budget = summary["signature"]["budget"]
                lines = events.read_text("utf-8").splitlines()
                assert summary["algorithm_evaluations"] == budget and len(lines) == 1 + 2 * budget
                complete += 1
            else:
                labels, pending = inspect_events(events)
                budget = int(directory.name.rsplit("_b", 1)[1])
                assert labels < budget and pending == 0
                partial.append((directory, labels, pending))
        assert complete == status["completed"] and len(partial) == 4
        complete_counts[source] = complete
        for directory, labels, pending in partial:
            destination = DEST / "partial_runs" / source / directory.name
            assert_inside(directory, ROOT / "results")
            assert_inside(destination, ROOT / "results")
            files = {path.name: digest(path) for path in sorted(directory.iterdir()) if path.is_file()}
            assert "events.jsonl" in files
            plans.append(
                dict(
                    source=source, runid=directory.name, paid_labels=labels, pending_pre=pending,
                    original=directory, destination=destination, file_sha256=files,
                )
            )
            old_calls += labels
    assert len(plans) == 8 and old_calls == 2514

    DEST.mkdir(parents=True)
    for source, _ in SOURCES:
        old = DEST / "old_states" / source
        old.mkdir(parents=True)
        for name in ["status.json", "failures.json", "recovery_driver_v2.json"]:
            path = ROOT / "results" / source / name
            if path.exists():
                shutil.copy2(path, old / name)
    for plan in plans:
        plan["destination"].parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(plan["original"]), str(plan["destination"]))
        assert not plan["original"].exists() and plan["destination"].is_dir()
        assert all(digest(plan["destination"] / name) == value for name, value in plan["file_sha256"].items())

    for helper in HELPERS:
        source = ROOT / "results" / helper
        assert source.is_dir(), helper
        destination = DEST / "old_helper_states" / helper
        assert_inside(source, ROOT / "results")
        assert_inside(destination, ROOT / "results")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))
        assert not source.exists() and destination.is_dir()
    for name in LAUNCHER_LOGS:
        source = ROOT / "results" / name
        if source.exists():
            destination = DEST / "old_launcher_logs" / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

    rows = []
    for plan in plans:
        rows.append(
            dict(
                source=plan["source"], runid=plan["runid"], paid_labels=plan["paid_labels"],
                pending_pre=plan["pending_pre"],
                archive=plan["destination"].relative_to(ROOT).as_posix(),
                file_sha256=plan["file_sha256"],
            )
        )
    recovery_sources = [
        "src/archive_third_interruption.py", "src/resume_interrupted_gp_batch_v4_parallel.py",
        "src/recover_interrupted_run.py", "src/gp_references.py",
        "configs/turbo_reference.json", "configs/gp_ei_reference.json",
    ]
    manifest = dict(
        interruption_date="2026-09-20",
        observation="all recorded parent and child PIDs absent; no scientific failure record",
        partial_runs=rows,
        complete_runs_before_interruption=complete_counts,
        old_paid_calls=old_calls,
        all_pre_label_pairs_complete=True,
        no_pending_physical_return=True,
        unchanged_budgets_and_scope=True,
        objective_calls_by_archiver=0,
        stale_helper_states_archived=HELPERS,
        recovery_sources={name: digest(ROOT / name) for name in recovery_sources},
    )
    path = DEST / "recovery_manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"partial_runs": len(rows), "old_paid_calls": old_calls, "complete": complete_counts, "manifest_sha256": digest(path)}, indent=2))


if __name__ == "__main__":
    main()
