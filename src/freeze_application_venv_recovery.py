"""Freeze the application venv self-overlap correction before labels."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/frozen_application_venv_recovery_v1"
FILES = [
    "docs/应用批次启动器自重叠修正协议20260921.md",
    "src/application_batch_venv_entry.py",
    "src/finish_application_batch_venv_safe.py",
    "src/freeze_application_venv_recovery.py",
    "tests/test_application_venv_entry.py",
    "src/run_application_batch.py",
    "src/application_experiment.py",
    "src/analyze_application.py",
    "configs/application_formal.json",
    "docs/frozen_application_formal_v1/sha256.json",
    "results/solo_cost_analysis_v1/integrity_audit.json",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert not OUT.exists()
    manifest = {name: digest(ROOT / name) for name in FILES}
    for name in FILES:
        target = OUT / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    (OUT / "sha256.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    assert all(digest(OUT / name) == expected for name, expected in manifest.items())
    print(json.dumps({"files": len(manifest), "manifest": digest(OUT / "sha256.json")}, indent=2))


if __name__ == "__main__":
    main()
