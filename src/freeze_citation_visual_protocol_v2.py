"""Freeze the post-build citation revision and authoritative visual-v2 workflow."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "docs/frozen_citation_visual_protocol_v2"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_freeze(relative: str) -> None:
    base = ROOT / relative
    manifest = json.loads((base / "sha256.json").read_text("utf-8"))
    assert all(digest(base / name) == expected for name, expected in manifest.items())


def main() -> None:
    assert not DEST.exists(), "Citation visual-v2 protocol freeze already exists"
    verify_freeze("docs/frozen_citation_revision_protocol_v1")
    verify_freeze("docs/frozen_all_pdf_visual_review_v1")
    verify_freeze("docs/frozen_visual_finalization_v1")
    relative = {
        "src/finish_citation_revision.py",
        "src/finish_citation_visual_review_v2.py",
        "src/finalize_citation_visual_review_v2.py",
        "src/freeze_citation_visual_protocol_v2.py",
        "src/revise_final_citations.py",
        "src/audit_manuscript_citations.py",
        "tests/test_citation_visual_chain.py",
        "tests/test_manuscript_citations.py",
        "docs/引用修订终稿PDF视觉核查协议20260920.md",
        "docs/frozen_citation_revision_protocol_v1/sha256.json",
        "docs/frozen_all_pdf_visual_review_v1/sha256.json",
        "docs/frozen_visual_finalization_v1/sha256.json",
        "src/finish_final_visual_review.py",
        "src/finish_all_pdf_visual_review.py",
        "src/finalize_all_pdf_visual_review.py",
        "configs/english-paper-template.tex",
        "configs/keep-math-mechanism.lua",
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
