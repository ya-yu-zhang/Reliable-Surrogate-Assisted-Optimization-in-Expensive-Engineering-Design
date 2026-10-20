"""Bibliography integrity guards for the submission manuscript.

The numbered reference list must stay contiguous, every in-text citation must resolve,
every reference must be cited, and nothing may survive that a reader cannot resolve
(a DOI that does not exist, an author list that contradicts the record). The
verification record is checked for the two defects this repository previously carried:
the superseded COCO DOI and the wrong first author of reference 8.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper" / "engineering_optimization"
MANUSCRIPT = ROOT / "paper" / "engineering_optimization_manuscript.md"
VERIFICATION = PAPER / "bibliography_verification.json"


def _split():
    text = MANUSCRIPT.read_text(encoding="utf-8")
    body, _, refs = text.partition("## References")
    return body, refs


def _entries(refs):
    return {int(m.group(1)): m.group(2).strip() for m in re.finditer(r"^\[(\d+)\]\s+(.+)$", refs, re.M)}


def _cited(body):
    numbers = set()
    for m in re.finditer(r"\[(\d{1,2})(?:\s*[,;\u2013-]\s*\d{1,2})*\]", body):
        for part in re.split(r"[,;]", m.group(0).strip("[]")):
            part = part.strip()
            if re.fullmatch(r"\d{1,2}", part):
                numbers.add(int(part))
            elif re.fullmatch(r"\d{1,2}\s*[\u2013-]\s*\d{1,2}", part):
                lo, hi = [int(x) for x in re.split(r"[\u2013-]", part)]
                numbers.update(range(lo, hi + 1))
    return numbers


def test_reference_numbers_are_contiguous():
    entries = _entries(_split()[1])
    assert sorted(entries) == list(range(1, len(entries) + 1)), sorted(entries)


def test_every_citation_resolves_and_every_reference_is_cited():
    body, refs = _split()
    entries = _entries(refs)
    cited = _cited(body)
    assert not (cited - set(entries)), f"cited but not listed: {sorted(cited - set(entries))}"
    assert not (set(entries) - cited), f"listed but never cited: {sorted(set(entries) - cited)}"


def test_errors_that_were_corrected_do_not_reappear():
    refs = _split()[1]
    assert "10.1080/10556788.2018.1502028" not in refs, "superseded COCO DOI returned"
    assert "X. Yang" not in refs, "wrong first author of the dual-space-driven paper returned"
    assert "Int. J. Autom. Comput." not in refs, "superseded journal name for reference 5 returned"


def test_verification_record_covers_every_reference():
    record = json.loads(VERIFICATION.read_text(encoding="utf-8"))
    ids = {item["id"] for item in record["records"]}
    assert ids == set(_entries(_split()[1])), "verification record and reference list disagree"
    assert all(item["title_matches_source"] for item in record["records"])
    blob = json.dumps(record, ensure_ascii=False)
    assert "Xiaomin Ma" not in blob, "the superseded author-name note returned"
