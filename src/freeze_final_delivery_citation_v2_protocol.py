"""Freeze the authoritative citation-corrected final delivery gate."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "docs/frozen_final_delivery_citation_v2_protocol"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_freeze(relative: str) -> None:
    base = ROOT / relative
    manifest = json.loads((base / "sha256.json").read_text("utf-8"))
    assert all(digest(base / name) == expected for name, expected in manifest.items())


def main() -> None:
    assert not DEST.exists(), "Citation-corrected final-delivery protocol already exists"
    for relative in (
        "docs/frozen_citation_visual_protocol_v2",
        "docs/frozen_final_delivery_v1",
        "docs/frozen_final_delivery_addendum_protocol_v1",
        "docs/frozen_third_recovery_subset_v1",
    ):
        verify_freeze(relative)
    relative = {
        "src/audit_final_delivery_citation_v2.py",
        "src/finish_final_delivery_citation_v2.py",
        "src/freeze_final_delivery_citation_v2_protocol.py",
        "src/audit_final_delivery.py",
        "src/audit_final_delivery_addendum.py",
        "src/audit_manuscript_citations.py",
        "tests/test_final_delivery_citation_v2.py",
        "tests/test_final_delivery_guards.py",
        "tests/test_final_delivery_addendum.py",
        "docs/引用修订版最终交付审计门槛20260920.md",
        "docs/frozen_citation_visual_protocol_v2/sha256.json",
        "docs/frozen_final_delivery_v1/sha256.json",
        "docs/frozen_final_delivery_addendum_protocol_v1/sha256.json",
        "docs/frozen_third_recovery_subset_v1/sha256.json",
    }
    hashes: dict[str, str] = {}
    for name in sorted(relative):
        source = ROOT / name
        assert source.is_file(), name
        target = DEST / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        hashes[name] = digest(source)
        assert digest(target) == hashes[name]
    manifest = DEST / "sha256.json"
    manifest.write_text(json.dumps(hashes, ensure_ascii=False, indent=2), encoding="utf-8")
    check = json.loads(manifest.read_text("utf-8"))
    assert len(check) == len(hashes)
    assert all(digest(DEST / name) == expected for name, expected in check.items())
    print(json.dumps({"files": len(hashes), "manifest_sha256": digest(manifest)}, indent=2))


if __name__ == "__main__":
    main()
