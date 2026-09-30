"""Freeze the citation audit and post-build final-manuscript correction protocol."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "docs/frozen_citation_revision_protocol_v1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert not DEST.exists(), "Citation-revision protocol freeze already exists"
    audit_path = ROOT / "results/manuscript_citation_audit_v1/audit.json"
    audit = json.loads(audit_path.read_text("utf-8"))
    assert audit["objective_calls_by_this_auditor"] == 0
    assert audit["papers_audited"] == 4 and audit["undefined_citations"] == 0
    assert audit["english_uncited_reference_issue"] == [8, 9]
    assert audit["chinese_citation_reference_sets_complete"]
    assert audit["bilingual_reference_locators_equal"]
    assert audit["requires_final_english_citation_revision"]
    assert not audit["frozen_base_manuscripts_modified"]

    relative = {
        "src/audit_manuscript_citations.py",
        "src/revise_final_citations.py",
        "src/freeze_citation_revision_protocol.py",
        "tests/test_manuscript_citations.py",
        "results/manuscript_citation_audit_v1/audit.json",
        "docs/双语论文引用一致性核查与终稿修订协议20260920.md",
        "paper/english_mechanism_manuscript.md",
        "paper/论文机制研究稿.md",
        "paper/english_development_manuscript.md",
        "paper/论文阶段稿.md",
        "paper/english_mechanism_source_hashes.json",
        "paper/english_development_source_hashes.json",
        "src/build_integrated_manuscripts.py",
        "src/build_high_extension_revision.py",
        "src/build_sensitivity_revision.py",
        "src/build_budget_sensitivity_revision.py",
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
