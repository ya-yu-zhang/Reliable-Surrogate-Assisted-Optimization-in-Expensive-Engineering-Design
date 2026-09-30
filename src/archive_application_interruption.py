"""Archive the interrupted application prefixes and stale orchestration state."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

from .run_solo_cost import process_inventory


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "results/application_formal_v1"
ARCHIVE = ROOT / "results/application_interruption_20260921_v1"
PARTIALS = [
    "gp_ei_DNA_r11_b500",
    "PEM_T_DNA_r01_b500",
    "turbo_1_synt_simple_r14_b500",
    "turbo_1_DNA_r05_b500",
]
HELPERS = [
    "application_completion_v1", "evidence_export_v1", "high_extension_completion_v1",
    "high_evidence_export_v1", "model_sensitivity_completion_v1",
    "sensitivity_evidence_export_v1", "budget_performance_sensitivity_completion_v1",
    "budget_evidence_export_v1", "final_visual_review_v1", "citation_revision_completion_v1",
    "all_pdf_visual_review_v1", "final_delivery_completion_v1",
    "all_pdf_visual_review_citation_v2", "final_delivery_citation_v2_completion",
    "final_delivery_addendum_completion_v1", "plan_delivery_bundle_completion_v1",
    "final_provenance_bundle_completion_v1",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert not ARCHIVE.exists()
    active = {int(row["ProcessId"]) for row in process_inventory()}
    status = json.loads((SOURCE / "status.json").read_text("utf-8"))
    assert status["stage"] == "running" and status["completed"] == 285 and status["failed"] == 0
    assert status["pid"] not in active
    for name in HELPERS:
        helper = json.loads((ROOT / "results" / name / "status.json").read_text("utf-8"))
        assert helper["pid"] not in active and helper["failure"] is None
    ARCHIVE.mkdir(parents=True)
    partial_out = ARCHIVE / "partial_runs"
    helper_out = ARCHIVE / "stale_helper_states"
    logs_out = ARCHIVE / "launcher_logs"
    partial_out.mkdir(); helper_out.mkdir(); logs_out.mkdir()
    for name in PARTIALS:
        directory = SOURCE / name
        assert directory.is_dir() and not (directory / "summary.json").exists()
        shutil.move(str(directory), str(partial_out / name))
    for name in HELPERS:
        shutil.move(str(ROOT / "results" / name), str(helper_out / name))
    for name in ["manifest.json", "status.json", "failures.json"]:
        shutil.copy2(SOURCE / name, ARCHIVE / ("old_" + name))
    logs = sorted((ROOT / "results").glob("twelfth_*.log")) + sorted((ROOT / "results").glob("twelfthb_*.log"))
    assert len(logs) == 34, len(logs)
    for path in logs:
        shutil.move(str(path), str(logs_out / path.name))
    files = sorted(path for path in ARCHIVE.rglob("*") if path.is_file())
    payload = {
        "schema": "application_interruption_archive_v1",
        "complete_runs": 285,
        "partial_runs": len(PARTIALS),
        "saved_paid_labels": 1368,
        "expected_new_suffix_calls": 632,
        "stale_helper_states": len(HELPERS),
        "launcher_logs": len(logs),
        "files": {path.relative_to(ROOT).as_posix(): digest(path) for path in files},
    }
    (ARCHIVE / "archive_manifest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in payload.items() if key != "files"}, indent=2))


if __name__ == "__main__":
    main()
