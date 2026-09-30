"""Freeze the fifth-launch helper JSON-race archive."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "docs/frozen_helper_json_race_v1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert not DEST.exists(), "Helper JSON-race archive already frozen"
    manifest_path = ROOT / "results/interruption_20260920_helper_json_race_v1/manifest.json"
    record = json.loads(manifest_path.read_text("utf-8"))
    assert record["objective_calls_by_archiver"] == 0
    assert record["scientific_evaluations_started_by_failed_helpers"] == 0
    assert record["root_failure"]["type"] == "JSONDecodeError"
    assert record["cascade_failures"] == 6 and len(record["failed_state_dirs"]) == 7
    assert all(digest(ROOT / name) == expected for name, expected in record["files"].items())
    relative = set(record["files"])
    relative.update({
        "src/archive_helper_json_race.py",
        "src/freeze_helper_json_race.py",
        "docs/第五轮等待器JSON读取竞态记录20260920.md",
        "results/interruption_20260920_helper_json_race_v1/manifest.json",
    })
    hashes = {}
    for name in sorted(relative):
        source = ROOT / name
        assert source.is_file(), name
        target = DEST / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        hashes[name] = digest(source)
        assert digest(target) == hashes[name]
    output = DEST / "sha256.json"
    output.write_text(json.dumps(hashes, ensure_ascii=False, indent=2), encoding="utf-8")
    assert all(digest(DEST / name) == expected for name, expected in json.loads(output.read_text("utf-8")).items())
    print(json.dumps({"files": len(hashes), "manifest_sha256": digest(output)}, indent=2))


if __name__ == "__main__":
    main()
