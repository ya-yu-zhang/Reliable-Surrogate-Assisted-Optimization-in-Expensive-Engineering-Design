"""Audit numeric citation/reference consistency without modifying manuscripts."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/manuscript_citation_audit_v1"
PAPERS = {
    "english_mechanism": ("paper/english_mechanism_manuscript.md", "# References"),
    "chinese_mechanism": ("paper/论文机制研究稿.md", "# 参考文献"),
    "english_development": ("paper/english_development_manuscript.md", "# References"),
    "chinese_development": ("paper/论文阶段稿.md", "# 参考文献"),
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expand_group(group: str) -> set[int]:
    pieces = group.replace("–", "-").split(",")
    values: set[int] = set()
    for piece in pieces:
        if "-" in piece:
            left, right = (int(value) for value in piece.split("-", 1))
            assert 0 <= left <= right
            values.update(range(left, right + 1))
        else:
            values.add(int(piece))
    return values


def body_citations(body: str) -> set[int]:
    citations: set[int] = set()
    for match in re.finditer(r"\[(\d+(?:(?:,|–|-)\d+)*)\]", body):
        values = expand_group(match.group(1))
        # Mathematical vectors and intervals in these papers contain zero;
        # reference numbering starts at one.
        if 0 in values:
            continue
        citations.update(values)
    return citations


def reference_rows(references: str) -> dict[int, str]:
    rows: dict[int, str] = {}
    for line in references.splitlines():
        match = re.match(r"^\[(\d+)\]\s+(.+)$", line.strip())
        if match:
            number = int(match.group(1))
            assert number not in rows
            rows[number] = match.group(2)
    return rows


def locator(entry: str) -> str:
    doi = re.search(r"(?:DOI:|https://doi\.org/)(10\.\d{4,9}/[^>\s]+)", entry, re.I)
    if doi:
        return "doi:" + doi.group(1).rstrip(".").lower()
    url = re.search(r"<(https?://[^>]+)>", entry)
    assert url is not None, entry
    return "url:" + url.group(1).rstrip("/").lower()


def audit_text(text: str, marker: str) -> dict[str, Any]:
    assert text.count(marker) == 1
    body, references = text.split(marker, 1)
    cited = body_citations(body)
    rows = reference_rows(references)
    numbers = set(rows)
    assert numbers == set(range(1, len(rows) + 1))
    return {
        "citations": sorted(cited),
        "references": sorted(numbers),
        "undefined_citations": sorted(cited - numbers),
        "uncited_references": sorted(numbers - cited),
        "locators": {str(number): locator(entry) for number, entry in rows.items()},
    }


def main() -> None:
    assert not OUT.exists(), "Manuscript citation audit already exists"
    papers = {}
    for label, (relative, marker) in PAPERS.items():
        path = ROOT / relative
        result = audit_text(path.read_text("utf-8"), marker)
        result["path"] = relative
        result["sha256"] = digest(path)
        papers[label] = result

    assert not any(row["undefined_citations"] for row in papers.values())
    assert papers["english_mechanism"]["uncited_references"] == [8, 9]
    assert papers["english_development"]["uncited_references"] == [8, 9]
    assert not papers["chinese_mechanism"]["uncited_references"]
    assert not papers["chinese_development"]["uncited_references"]
    assert papers["english_mechanism"]["locators"] == papers["chinese_mechanism"]["locators"]
    assert papers["english_development"]["locators"] == papers["chinese_development"]["locators"]

    result = {
        "schema": "manuscript_citation_audit_v1",
        "objective_calls_by_this_auditor": 0,
        "papers_audited": len(papers),
        "undefined_citations": 0,
        "english_uncited_reference_issue": [8, 9],
        "chinese_citation_reference_sets_complete": True,
        "bilingual_reference_locators_equal": True,
        "requires_final_english_citation_revision": True,
        "frozen_base_manuscripts_modified": False,
        "papers": papers,
    }
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / "audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "papers"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
