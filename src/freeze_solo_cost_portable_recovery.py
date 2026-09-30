"""Freeze the exact path-portability correction before any solo-cost calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/frozen_solo_cost_portable_recovery_v2"
FILES = [
    "docs/独占成本冻结清单路径兼容协议20260921.md",
    "src/run_solo_cost_portable.py",
    "src/finish_reference_batch_portable.py",
    "src/freeze_solo_cost_portable_recovery.py",
    "tests/test_solo_cost_portable.py",
    "docs/frozen_solo_cost_launcher_recovery_v1/sha256.json",
    "docs/frozen_solo_cost_v1/sha256.json",
    "src/run_solo_cost.py",
    "src/analyze_solo_cost.py",
    "configs/solo_cost.json",
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
