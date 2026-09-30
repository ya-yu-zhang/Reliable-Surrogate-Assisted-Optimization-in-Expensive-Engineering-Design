"""Archive the post-application PID-reuse failure without altering frozen science."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

from .run_solo_cost import process_inventory


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "results/post_application_pid_reuse_failure_20260922_v1"
STATES = [
    "evidence_export_v1", "high_extension_completion_v1", "high_evidence_export_v1",
    "model_sensitivity_completion_v1", "sensitivity_evidence_export_v1",
    "budget_performance_sensitivity_completion_v1", "budget_evidence_export_v1",
    "final_visual_review_v1", "citation_revision_completion_v1", "all_pdf_visual_review_v1",
    "final_delivery_completion_v1", "all_pdf_visual_review_citation_v2",
    "final_delivery_citation_v2_completion", "final_delivery_addendum_completion_v1",
    "plan_delivery_bundle_completion_v1", "final_provenance_bundle_completion_v1",
]
FORBIDDEN = (
    "finish_evidence_export", "finish_high_extension", "finish_high_evidence_export",
    "finish_model_sensitivity", "finish_sensitivity_evidence_export",
    "finish_budget_performance_sensitivity", "finish_budget_evidence_export",
    "finish_final_visual_review", "finish_citation_revision", "finish_all_pdf_visual_review",
    "finish_final_delivery", "finish_citation_visual_review_v2",
    "finish_final_delivery_citation_v2", "finish_final_delivery_addendum",
    "finish_plan_delivery_bundle", "finish_final_provenance_bundle",
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert not ARCHIVE.exists()
    inventory = process_inventory()
    assert not any(any(name in (row["CommandLine"] or "") for name in FORBIDDEN)
                   for row in inventory), "Identity-matched helper is still live"
    app = json.loads((ROOT / "results/application_analysis_v1/audit.json").read_text("utf-8"))
    assert app["runs"] == 480 and app["algorithm_evaluations"] == 240000 and app["complete_design"]
    assert not any(path for name in (
        "application_high_v1", "model_sensitivity_v1", "budget_performance_sensitivity_v1"
    ) for path in (ROOT / "results" / name).glob("**/summary.json"))
    for name in STATES:
        status = json.loads((ROOT / "results" / name / "status.json").read_text("utf-8"))
        assert status["stage"] == "failed"
    ARCHIVE.mkdir(); states = ARCHIVE / "failed_states"; logs = ARCHIVE / "launcher_logs"
    states.mkdir(); logs.mkdir()
    for name in STATES:
        shutil.move(str(ROOT / "results" / name), str(states / name))
    launch_logs = sorted((ROOT / "results").glob("eighteenthb_*.log"))
    assert len(launch_logs) == 32, len(launch_logs)
    for path in launch_logs:
        shutil.move(str(path), str(logs / path.name))
    files = sorted(path for path in ARCHIVE.rglob("*") if path.is_file())
    manifest = {
        "schema": "post_application_pid_reuse_failure_archive_v1",
        "application_runs_preserved": 480,
        "new_scientific_runs_started": 0,
        "failed_states": len(STATES),
        "launcher_logs": len(launch_logs),
        "files": {path.relative_to(ROOT).as_posix(): digest(path) for path in files},
    }
    (ARCHIVE / "archive_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items() if k != "files"}, indent=2))


if __name__ == "__main__":
    main()
