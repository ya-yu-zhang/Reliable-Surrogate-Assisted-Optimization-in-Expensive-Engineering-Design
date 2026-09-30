"""Freeze the third-recovery audit and its complete evidence chain."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "docs/frozen_third_recovery_audit_v1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert not DEST.exists(), "Third-recovery audit freeze already exists"
    frozen_root = ROOT / "docs/frozen_third_recovery_v1"
    frozen_manifest = json.loads((frozen_root / "sha256.json").read_text("utf-8"))
    assert all(digest(frozen_root / name) == expected for name, expected in frozen_manifest.items())

    audit_path = ROOT / "results/interruption_20260920_v3/third_recovery_audit.json"
    audit = json.loads(audit_path.read_text("utf-8"))
    assert audit["recovered_runs"] == 8
    assert audit["third_generation_saved_labels"] == 2514
    assert audit["third_generation_new_physical_calls"] == 686
    assert audit["redundant_recovery_validation_calls"] == 0
    assert audit["objective_calls_by_this_auditor"] == 0

    relative = {
        "src/audit_third_recovery.py",
        "src/freeze_third_recovery_audit.py",
        "src/finish_third_recovery_audit.py",
        "tests/test_third_recovery_audit.py",
        "docs/第三次恢复编排层启动时序记录20260920.md",
        "results/interruption_20260920_helper_race_v1/manifest.json",
        "results/interruption_20260918_v1/recovery_manifest.json",
        "results/interruption_20260919_v2/recovery_manifest.json",
        "results/interruption_20260920_v3/recovery_manifest.json",
        "results/interruption_20260920_v3/third_recovery_audit.json",
        "results/turbo_reference_v1/status.json",
        "results/turbo_reference_v1/recovery_driver_v4.json",
        "results/gp_ei_reference_v1/status.json",
        "results/gp_ei_reference_v1/recovery_driver_v4.json",
        "docs/frozen_third_recovery_v1/sha256.json",
    }
    relative.update("docs/frozen_third_recovery_v1/" + name for name in frozen_manifest)
    for row in audit["runs"]:
        base = f"results/{row['source']}/{row['runid']}"
        relative.update(
            {
                f"{base}/events.jsonl",
                f"{base}/summary.json",
                f"{base}/recovery_physical_calls.jsonl",
                f"{base}/recovery.json",
            }
        )

    hashes: dict[str, str] = {}
    for name in sorted(relative):
        source = ROOT / name
        assert source.is_file(), name
        target = DEST / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        hashes[name] = digest(source)
        assert digest(target) == hashes[name]

    manifest_path = DEST / "sha256.json"
    manifest_path.write_text(json.dumps(hashes, ensure_ascii=False, indent=2), encoding="utf-8")
    check = json.loads(manifest_path.read_text("utf-8"))
    assert len(check) == len(hashes)
    assert all(digest(DEST / name) == expected for name, expected in check.items())
    print(json.dumps({"files": len(hashes), "manifest_sha256": digest(manifest_path)}, indent=2))


if __name__ == "__main__":
    main()
