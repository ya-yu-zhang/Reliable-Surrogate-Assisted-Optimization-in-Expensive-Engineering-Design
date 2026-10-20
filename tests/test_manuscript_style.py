"""Style guards for the submission manuscript sources.

Two journal-facing rules are easy to break while editing and invisible to the evidence
tests: the text must stay in impersonal voice, and the paper must not advertise itself
as "new" or "novel". Both are checked on the Markdown submission source, which is what
the Word package is built from.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "paper" / "engineering_optimization_manuscript.md"
SUPPLEMENT = ROOT / "paper" / "engineering_optimization_supplementary.md"

FIRST_PERSON = re.compile(r"\b(we|We|our|Our|us|Us|I)\b")
SELF_PRAISE = re.compile(r"\b(new|New|novel|Novel)\b")


def _body(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    return text.split("## References")[0]


def _abstract_and_title(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    title = text.splitlines()[0]
    start = text.index("## Abstract")
    end = text.index("**Keywords:**")
    return title + "\n" + text[start:end]


@pytest.mark.parametrize("path", [MANUSCRIPT, SUPPLEMENT])
def test_no_first_person_voice(path):
    hits = FIRST_PERSON.findall(_body(path))
    assert not hits, f"first-person pronouns in {path.name}: {sorted(set(hits))}"


def test_title_and_abstract_avoid_new_or_novel():
    hits = SELF_PRAISE.findall(_abstract_and_title(MANUSCRIPT))
    assert not hits, f"title or abstract describes the work as new/novel: {hits}"


def test_every_figure_is_referenced_and_described():
    body = _body(MANUSCRIPT)
    embedded = re.findall(r"^!\[[^\]]*\]\(([^)]+)\)", body, re.M)
    assert embedded, "no figures found in the manuscript body"
    for number in range(1, len(embedded) + 1):
        pattern = rf"^Figure {number} (?:reports|shows|displays|arranges|separates|locates|makes)"
        assert re.search(pattern, body, re.M), f"Figure {number} has no describing paragraph"
