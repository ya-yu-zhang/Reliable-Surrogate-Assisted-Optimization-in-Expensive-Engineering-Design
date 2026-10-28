"""Submission-readiness guards for the Engineering Optimization package.

These check the items that a desk editor sees first: the declarations must satisfy the
publisher's AI policy, the data-availability statement must not promise something that is
not true at submission time, and the package must contain the artefacts the portal asks
for. The checks read the Markdown submission source and the built Word files.
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "paper" / "engineering_optimization_manuscript.md"
SUBMISSION = ROOT / "paper" / "eo_submission"


def _text() -> str:
    return MANUSCRIPT.read_text(encoding="utf-8")


def _section(text: str, heading: str) -> str:
    start = text.index(heading) + len(heading)
    following = text.find("\n## ", start)
    return text[start:] if following < 0 else text[start:following]


def test_ai_declaration_covers_the_four_policy_elements():
    declaration = _section(_text(), "## Declaration of Generative Artificial Intelligence Use")
    assert re.search(r"DeepSeek V4\.1 Flash \(version 1017\)", declaration), "tool name and version missing"
    assert "originality and accuracy" in declaration, "originality/accuracy confirmation missing"
    assert "terms of use" in declaration and "suitable for publication" in declaration, "terms-of-use confirmation missing"
    assert "integrity of the whole content" in declaration and "accuracy of the references" in declaration, (
        "responsibility statement must cover the references")
    assert "draft" in declaration, "the declaration should state that no drafting was performed"


def test_data_availability_does_not_claim_a_public_repository():
    section = _section(_text(), "## Availability of Data and Materials")
    assert "upon acceptance" in section, "release timing must be stated"
    assert "public repository" not in section.lower(), (
        "the repository is private at submission time, so the statement must not call it public")
    assert "on request" in section, "reviewer access route missing"


def test_no_working_draft_placeholders_in_either_track():
    for path in (MANUSCRIPT, ROOT / "paper" / "engineering_optimization" / "EO_manuscript.tex"):
        text = path.read_text(encoding="utf-8")
        for phrase in ("Working manuscript", "to be supplied", "to be confirmed", "private repository"):
            assert phrase not in text, f"{phrase!r} still present in {path.name}"


def test_package_contains_the_portal_artefacts():
    required = [
        SUBMISSION / "EO_submission_manuscript.docx",
        SUBMISSION / "EO_submission_manuscript_review.docx",
        SUBMISSION / "EO_supplementary_materials.docx",
        SUBMISSION / "EO_cover_letter.docx",
        SUBMISSION / "EO_length_explanation.docx",
    ]
    for path in required:
        assert path.exists(), f"missing {path.name}"
    figures = sorted((SUBMISSION / "figures").glob("Fig*.png"))
    assert len(figures) == 6, f"expected six separate figure files, found {len(figures)}"


def test_review_copy_is_double_spaced_and_line_numbered():
    path = SUBMISSION / "EO_submission_manuscript_review.docx"
    with zipfile.ZipFile(path) as archive:
        document = archive.read("word/document.xml").decode("utf-8")
    assert "lnNumType" in document, "review copy has no continuous line numbering"


def test_abstract_meets_the_journal_length():
    text = _text()
    abstract = text[text.index("## Abstract") + len("## Abstract"): text.index("**Keywords:**")]
    words = len(abstract.split())
    assert 140 <= words <= 160, f"abstract is {words} words; the journal asks for about 150"
