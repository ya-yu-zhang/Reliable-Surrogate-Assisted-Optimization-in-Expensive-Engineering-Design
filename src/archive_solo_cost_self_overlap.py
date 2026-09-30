"""Archive the second zero-call self-overlap refusal and failed dependency states."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

from .run_solo_cost import process_inventory


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "results/solo_cost_self_overlap_20260921_v2"
STATE_DIRS = [
    "reference_completion_v1",
    "application_completion_v1",
    "evidence_export_v1",
    "high_extension_completion_v1",
    "high_evidence_export_v1",
    "model_sensitivity_completion_v1",
    "sensitivity_evidence_export_v1",
    "budget_performance_sensitivity_completion_v1",
    "budget_evidence_export_v1",
    "final_visual_review_v1",
    "all_pdf_visual_review_v1",
    "final_delivery_completion_v1",
    "citation_revision_completion_v1",
    "all_pdf_visual_review_citation_v2",
    "final_delivery_citation_v2_completion",
    "final_delivery_addendum_completion_v1",
    "plan_delivery_bundle_completion_v1",
    "final_provenance_bundle_completion_v1",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def within_workspace(path: Path) -> bool:
    try:
        path.resolve().relative_to(ROOT.resolve())
        return True
    except ValueError:
        return False


def main() -> None:
    assert not ARCHIVE.exists()
    active = {int(row["ProcessId"]) for row in process_inventory()}
    sources: list[Path] = []
    for name in STATE_DIRS:
        directory = ROOT / "results" / name
        status_path = directory / "status.json"
        assert directory.is_dir() and within_workspace(directory)
        status = json.loads(status_path.read_text("utf-8"))
        assert status["stage"] == "failed" and status["pid"] not in active
        sources.append(directory)
    log_files = sorted((ROOT / "results").glob("sixth_finish_*.log"))
    log_files += sorted((ROOT / "results").glob("sixthb_finish_*.log"))
    log_files += sorted((ROOT / "results").glob("seventh_finish_reference_batch_*.log"))
    assert len(log_files) == 46, len(log_files)
    assert all(within_workspace(path) for path in log_files)

    ARCHIVE.mkdir(parents=True)
    states_out = ARCHIVE / "failed_state_dirs"
    logs_out = ARCHIVE / "launcher_logs"
    states_out.mkdir()
    logs_out.mkdir()
    for directory in sources:
        shutil.move(str(directory), str(states_out / directory.name))
    for path in log_files:
        shutil.move(str(path), str(logs_out / path.name))

    files = sorted(path for path in ARCHIVE.rglob("*") if path.is_file())
    manifest = {
        "schema": "solo_cost_self_overlap_archive_v2",
        "objective_calls_from_both_refusals": 0,
        "solo_cost_runs_completed": 0,
        "failed_state_directories": len(STATE_DIRS),
        "launcher_logs": len(log_files),
        "files": {
            path.relative_to(ROOT).as_posix(): digest(path)
            for path in files
        },
    }
    (ARCHIVE / "archive_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({key: value for key, value in manifest.items() if key != "files"}, indent=2))


if __name__ == "__main__":
    main()
