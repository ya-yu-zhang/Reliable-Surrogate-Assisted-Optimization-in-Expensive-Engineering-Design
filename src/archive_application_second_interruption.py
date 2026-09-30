"""Archive the second interrupted application batch and stale orchestration state."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

from .run_solo_cost import process_inventory


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "results/application_formal_v1"
ARCHIVE = ROOT / "results/application_interruption_20260922_v2"
PARTIALS = ["cma_es_DNA_r08_b500", "turbo_1_DNA_r04_b500", "turbo_1_synt_simple_r07_b500"]
HELPERS = [
    "application_completion_v1", "evidence_export_v1", "high_extension_completion_v1",
    "high_evidence_export_v1", "model_sensitivity_completion_v1", "sensitivity_evidence_export_v1",
    "budget_performance_sensitivity_completion_v1", "budget_evidence_export_v1",
    "final_visual_review_v1", "citation_revision_completion_v1", "all_pdf_visual_review_v1",
    "final_delivery_completion_v1", "all_pdf_visual_review_citation_v2",
    "final_delivery_citation_v2_completion", "final_delivery_addendum_completion_v1",
    "plan_delivery_bundle_completion_v1", "final_provenance_bundle_completion_v1",
]
FORBIDDEN_IDENTITIES = (
    "application_batch_pid_reuse_entry", "application_experiment", "finish_application_after_recovery_v3",
    "finish_evidence_export", "finish_high_extension", "finish_high_evidence_export",
    "finish_model_sensitivity", "finish_sensitivity_evidence_export",
    "finish_budget_performance_sensitivity", "finish_budget_evidence_export",
    "finish_final_visual_review", "finish_citation_revision", "finish_all_pdf_visual_review",
    "finish_final_delivery", "finish_citation_visual_review_v2", "finish_final_delivery_citation_v2",
    "finish_final_delivery_addendum", "finish_plan_delivery_bundle", "finish_final_provenance_bundle",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert not ARCHIVE.exists()
    processes = process_inventory()
    assert not any(any(name in (row["CommandLine"] or "") for name in FORBIDDEN_IDENTITIES)
                   for row in processes), "Identity-matched application or helper process is still live"
    status = json.loads((SOURCE / "status.json").read_text("utf-8"))
    assert status["stage"] == "running" and status["completed"] == 376 and status["failed"] == 0
    assert sum((path / "summary.json").is_file() for path in SOURCE.iterdir() if path.is_dir()) == 376
    ARCHIVE.mkdir(); partial_out = ARCHIVE / "partial_runs"; helper_out = ARCHIVE / "stale_helper_states"
    logs_out = ARCHIVE / "launcher_logs"; partial_out.mkdir(); helper_out.mkdir(); logs_out.mkdir()
    paid = 0
    for name in PARTIALS:
        directory = SOURCE / name
        assert directory.is_dir() and not (directory / "summary.json").exists()
        events = [json.loads(line) for line in (directory / "events.jsonl").read_text("utf-8").splitlines()]
        labels = [row for row in events if row["event"] == "label"]
        assert len(labels) in (227, 494, 203)
        paid += len(labels)
        shutil.move(str(directory), str(partial_out / name))
    assert paid == 924
    for name in HELPERS:
        shutil.move(str(ROOT / "results" / name), str(helper_out / name))
    for name in ("manifest.json", "status.json", "failures.json"):
        shutil.copy2(SOURCE / name, ARCHIVE / ("old_" + name))
    logs = sorted((ROOT / "results").glob("fourteenth*.log"))
    assert len(logs) == 34, len(logs)
    for path in logs:
        shutil.move(str(path), str(logs_out / path.name))
    files = sorted(path for path in ARCHIVE.rglob("*") if path.is_file())
    manifest = {
        "schema": "application_interruption_archive_v2", "complete_runs": 376,
        "partial_runs": 3, "saved_paid_labels": 924, "expected_new_suffix_calls": 576,
        "stale_helper_states": len(HELPERS), "launcher_logs": len(logs),
        "files": {path.relative_to(ROOT).as_posix(): digest(path) for path in files},
    }
    (ARCHIVE / "archive_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in manifest.items() if key != "files"}, indent=2))


if __name__ == "__main__":
    main()
