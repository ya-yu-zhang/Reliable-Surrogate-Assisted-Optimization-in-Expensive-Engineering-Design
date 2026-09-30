import hashlib

import pytest

from src.audit_plan_delivery_bundle import validate_headings, verify_file_manifest


def test_heading_validator_requires_unique_ordered_sections():
    headings = ["# 1 A", "# 2 B", "# 3 C"]
    validate_headings("# 1 A\ntext\n# 2 B\ntext\n# 3 C\n", headings)
    with pytest.raises(AssertionError):
        validate_headings("# 1 A\n# 3 C\n# 2 B\n", headings)
    with pytest.raises(AssertionError):
        validate_headings("# 1 A\n# 2 B\n# 2 B\n# 3 C\n", headings)


def test_file_manifest_detects_content_drift(tmp_path):
    path = tmp_path / "artifact.txt"
    path.write_text("frozen", encoding="utf-8")
    manifest = {"artifact.txt": hashlib.sha256(path.read_bytes()).hexdigest()}
    verify_file_manifest(tmp_path, manifest)
    path.write_text("changed", encoding="utf-8")
    with pytest.raises(AssertionError):
        verify_file_manifest(tmp_path, manifest)
