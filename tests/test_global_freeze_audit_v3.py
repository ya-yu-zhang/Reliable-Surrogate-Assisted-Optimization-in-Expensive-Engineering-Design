import hashlib
import json

from src.audit_global_freezes_v3 import audit_manifest


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_nested_manifest_checks_live_and_preserved_copy(tmp_path):
    source = tmp_path / "src/value.txt"
    source.parent.mkdir()
    source.write_text("frozen", encoding="utf-8")
    freeze = tmp_path / "docs/frozen_nested"
    copy = freeze / "src/value.txt"
    copy.parent.mkdir(parents=True)
    copy.write_text("frozen", encoding="utf-8")
    (freeze / "sha256.json").write_text(json.dumps({"src/value.txt": digest(source)}), encoding="utf-8")
    row, live, copies, hashed = audit_manifest(tmp_path, freeze)
    assert row["schema"] == "nested-dict" and row["files"] == 1
    assert not live and not copies and len(hashed) == 3


def test_flat_manifest_reports_missing_copy_without_losing_live_check(tmp_path):
    source = tmp_path / "configs/value.json"
    source.parent.mkdir()
    source.write_text("{}", encoding="utf-8")
    freeze = tmp_path / "docs/frozen_flat"
    freeze.mkdir(parents=True)
    (freeze / "sha256.json").write_text(
        json.dumps([{"Path": str(source.resolve()), "Hash": digest(source).upper()}]), encoding="utf-8"
    )
    row, live, copies, hashed = audit_manifest(tmp_path, freeze)
    assert row["schema"] == "flat-list" and not live
    assert copies[0]["expected_copy"].endswith("docs/frozen_flat/value.json")
    assert len(hashed) == 2


def test_relative_flat_manifest_accepts_sha256_field(tmp_path):
    source = tmp_path / "src/value.py"
    source.parent.mkdir()
    source.write_text("VALUE = 1\n", encoding="utf-8")
    freeze = tmp_path / "docs/frozen_relative"
    freeze.mkdir(parents=True)
    (freeze / "value.py").write_bytes(source.read_bytes())
    (freeze / "sha256.json").write_text(
        json.dumps([{"Path": "src/value.py", "SHA256": digest(source).upper()}]), encoding="utf-8"
    )
    row, live, copies, _ = audit_manifest(tmp_path, freeze)
    assert row["schema"] == "flat-list"
    assert not live and not copies
