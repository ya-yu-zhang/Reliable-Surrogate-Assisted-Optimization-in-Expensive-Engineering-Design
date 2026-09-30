"""Archive the zero-new-design-call PID-reuse orchestration failure."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

from .run_solo_cost import process_inventory


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "results/application_pid_reuse_failure_20260921_v1"
STATES = [
    "application_completion_v1", "evidence_export_v1", "high_extension_completion_v1",
    "high_evidence_export_v1", "model_sensitivity_completion_v1", "sensitivity_evidence_export_v1",
    "budget_performance_sensitivity_completion_v1", "budget_evidence_export_v1",
    "final_visual_review_v1", "citation_revision_completion_v1", "all_pdf_visual_review_v1",
    "final_delivery_completion_v1", "all_pdf_visual_review_citation_v2",
    "final_delivery_citation_v2_completion", "final_delivery_addendum_completion_v1",
    "plan_delivery_bundle_completion_v1", "final_provenance_bundle_completion_v1",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert not ARCHIVE.exists()
    active = {row["ProcessId"] for row in process_inventory()}
    for name in STATES:
        status = json.loads((ROOT / "results" / name / "status.json").read_text("utf-8"))
        assert status["pid"] not in active and status["stage"] == "failed"
    assert sum((path / "summary.json").is_file() for path in (ROOT / "results/application_formal_v1").iterdir()
               if path.is_dir()) == 289
    ARCHIVE.mkdir(); states = ARCHIVE / "failed_states"; logs = ARCHIVE / "launcher_logs"
    states.mkdir(); logs.mkdir()
    for name in STATES:
        shutil.move(str(ROOT / "results" / name), str(states / name))
    launch_logs = sorted((ROOT / "results").glob("thirteenth*.log"))
    assert len(launch_logs) == 34, len(launch_logs)
    for path in launch_logs:
        shutil.move(str(path), str(logs / path.name))
    files = sorted(path for path in ARCHIVE.rglob("*") if path.is_file())
    manifest = {
        "schema": "application_pid_reuse_failure_archive_v1",
        "complete_runs_after_prefix_recovery": 289,
        "new_design_units_started_by_failed_scheduler": 0,
        "failed_states": len(STATES), "launcher_logs": len(launch_logs),
        "files": {path.relative_to(ROOT).as_posix(): digest(path) for path in files},
    }
    (ARCHIVE / "archive_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in manifest.items() if key != "files"}, indent=2))


if __name__ == "__main__":
    main()
