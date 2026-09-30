"""Archive the fifth-launch JSON read race; this code performs no scientific calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

from .run_solo_cost import process_inventory


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "results/interruption_20260920_helper_json_race_v1"
FAILED = {
    "all_pdf_visual_review_v1": "JSONDecodeError",
    "all_pdf_visual_review_citation_v2": "original renderer failed",
    "final_delivery_completion_v1": "All-PDF visual prerequisite failed",
    "final_delivery_addendum_completion_v1": "Prerequisite failed",
    "final_delivery_citation_v2_completion": "Prerequisite ended before completion",
    "plan_delivery_bundle_completion_v1": "Citation-corrected final delivery failed",
    "final_provenance_bundle_completion_v1": "Original-plan delivery bundle failed",
}
LOG_STEMS = [
    "finish_all_pdf_visual_review", "finish_citation_visual_review_v2",
    "finish_final_delivery", "finish_final_delivery_addendum",
    "finish_final_delivery_citation_v2", "finish_plan_delivery_bundle",
    "finish_final_provenance_bundle",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert not DEST.exists(), "Helper JSON-race archive already exists"
    live = {row["ProcessId"] for row in process_inventory()}
    plans = []
    for name, phrase in FAILED.items():
        source = ROOT / "results" / name
        status = json.loads((source / "status.json").read_text("utf-8"))
        assert status["stage"] == "failed" and status["pid"] not in live
        failure = json.dumps(status["failure"], ensure_ascii=False)
        assert phrase in failure, (name, failure)
        destination = DEST / "state_dirs" / name
        plans.append((source, destination))
    DEST.mkdir(parents=True)
    hashes = {}
    for source, destination in plans:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))
        assert not source.exists() and destination.is_dir()
        for path in sorted(destination.rglob("*")):
            if path.is_file():
                hashes[path.relative_to(ROOT).as_posix()] = digest(path)
    for stem in LOG_STEMS:
        for suffix in ["stdout", "stderr"]:
            source = ROOT / "results" / f"fifth_{stem}_{suffix}.log"
            assert source.is_file(), source
            destination = DEST / "logs" / source.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            hashes[destination.relative_to(ROOT).as_posix()] = digest(destination)
    manifest = {
        "schema": "helper_json_read_race_v1",
        "objective_calls_by_archiver": 0,
        "scientific_evaluations_started_by_failed_helpers": 0,
        "root_failure": {
            "module": "src.finish_all_pdf_visual_review",
            "type": "JSONDecodeError",
            "cause": "non-atomic upstream status rewrite observed as an empty JSON document",
        },
        "cascade_failures": 6,
        "failed_state_dirs": sorted(FAILED),
        "files": hashes,
    }
    path = DEST / "manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "failed_states": len(FAILED), "archived_files": len(hashes),
        "objective_calls": 0, "manifest_sha256": digest(path),
    }, indent=2))


if __name__ == "__main__":
    main()
