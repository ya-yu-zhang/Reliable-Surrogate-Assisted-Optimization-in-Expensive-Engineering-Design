"""Freeze fifth-recovery evidence after its pointwise audit."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "docs/frozen_fifth_recovery_audit_v1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert not DEST.exists(), "Fifth recovery audit already frozen"
    archive = ROOT / "results/interruption_20260921_v5"
    audit = json.loads((archive / "fifth_recovery_audit.json").read_text("utf-8"))
    assert audit["objective_calls_by_this_auditor"] == 0 and audit["recovered_runs"] == 4
    assert audit["fifth_generation_saved_labels"] == 1319
    assert audit["fifth_generation_new_physical_calls"] == 281
    assert audit["redundant_recovery_validation_calls"] == 0
    relative = {
        "src/archive_fifth_interruption.py", "src/resume_manifest_gp_batch.py",
        "src/resume_interrupted_gp_batch_v6_parallel.py", "src/audit_fifth_recovery.py",
        "src/finish_fifth_recovery_audit.py", "src/freeze_fifth_recovery_audit.py",
        "src/recover_interrupted_run.py", "src/gp_references.py", "configs/gp_ei_reference.json",
        "docs/第五次中断恢复执行协议20260921.md",
        "docs/frozen_fifth_recovery_protocol_v1/sha256.json",
        "results/interruption_20260921_v5/recovery_manifest.json",
        "results/interruption_20260921_v5/fifth_recovery_audit.json",
        "results/gp_ei_reference_v1/status.json", "results/gp_ei_reference_v1/recovery_driver_v6.json",
    }
    manifest = json.loads((archive / "recovery_manifest.json").read_text("utf-8"))
    for row in manifest["partial_runs"]:
        relative.add(row["archive"] + "/events.jsonl")
    for row in audit["runs"]:
        base = f"results/{row['source']}/{row['runid']}"
        relative.update({base + "/events.jsonl", base + "/summary.json", base + "/recovery_physical_calls.jsonl", base + "/recovery.json"})
    hashes = {}
    for name in sorted(relative):
        source = ROOT / name; assert source.is_file(), name
        target = DEST / name; target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(source, target)
        hashes[name] = digest(source); assert digest(target) == hashes[name]
    path = DEST / "sha256.json"; path.write_text(json.dumps(hashes, ensure_ascii=False, indent=2), encoding="utf-8")
    assert all(digest(DEST / name) == expected for name, expected in json.loads(path.read_text("utf-8")).items())
    print(json.dumps({"files": len(hashes), "manifest_sha256": digest(path)}, indent=2))


if __name__ == "__main__":
    main()
