import hashlib
import json

from src.audit_final_delivery_addendum import require_helper_race_archive, verify_hash_map


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_hash_map_verification(tmp_path):
    path = tmp_path / "artifact.txt"
    path.write_text("immutable", encoding="utf-8")
    verify_hash_map(tmp_path, {"artifact.txt": digest(path)})


def test_helper_race_archive_requires_all_recorded_bytes(tmp_path):
    archive = tmp_path / "results/interruption_20260920_helper_race_v1"
    archive.mkdir(parents=True)
    files = []
    for index in range(36):
        path = archive / f"entry-{index}.txt"
        path.write_text(str(index), encoding="utf-8")
        files.append({"path": path.name, "bytes": path.stat().st_size, "sha256": digest(path)})
    manifest = {
        "schema": "helper_relaunch_race_archive_v1",
        "reason": "no scientific objective evaluation was started",
        "moved_state_dirs": [f"state-{i}" for i in range(12)],
        "moved_logs": [f"log-{i}" for i in range(24)],
        "files": files,
    }
    (archive / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    checked = require_helper_race_archive(tmp_path)
    assert len(checked["files"]) == 36
