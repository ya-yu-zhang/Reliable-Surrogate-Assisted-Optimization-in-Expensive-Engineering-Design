"""Archive the zero-physical-call strict CMA replay refusal."""

from __future__ import annotations
import hashlib, json, shutil
from pathlib import Path
from .run_solo_cost import process_inventory

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "results/application_cma_strict_replay_failure_v1"

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    assert not ARCHIVE.exists()
    assert not any("resume_application_after_second_interruption_v4" in (p["CommandLine"] or "") or
                   "recover_interrupted_application_run" in (p["CommandLine"] or "") for p in process_inventory())
    status = json.loads((ROOT / "results/application_completion_v1/status.json").read_text("utf-8"))
    assert status["stage"] == "failed"
    cma = ROOT / "results/application_formal_v1/cma_es_DNA_r08_b500"
    assert cma.is_dir() and not (cma / "summary.json").exists()
    assert (cma / "recovery_physical_calls.jsonl").read_text("utf-8") == ""
    assert sum((p / "summary.json").is_file() for p in (ROOT / "results/application_formal_v1").iterdir() if p.is_dir()) == 378
    ARCHIVE.mkdir(); shutil.move(str(cma), str(ARCHIVE / cma.name))
    shutil.move(str(ROOT / "results/application_completion_v1"), str(ARCHIVE / "failed_completion_state"))
    for path in sorted((ROOT / "results").glob("fifteenth_application_*.log")):
        shutil.move(str(path), str(ARCHIVE / path.name))
    files = sorted(p for p in ARCHIVE.rglob("*") if p.is_file())
    manifest = {"schema": "application_cma_strict_replay_failure_v1", "physical_objective_calls": 0,
                "strict_pairs_equal": 38, "first_roundoff_mismatch_t": 39,
                "files": {p.relative_to(ROOT).as_posix(): digest(p) for p in files}}
    (ARCHIVE / "archive_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items() if k != "files"}, indent=2))

if __name__ == "__main__": main()
