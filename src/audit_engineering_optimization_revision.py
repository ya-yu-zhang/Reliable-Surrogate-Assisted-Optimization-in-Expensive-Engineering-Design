"""Check revision evidence boundaries and unchanged reported numerical tables."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def references(text):
    entries = [int(n) for n in re.findall(r"^\[(\d+)\] ", text, re.M)]
    cited = set()
    for match in re.finditer(r"\[([1-9]\d*(?:\s*[-,]\s*[1-9]\d*)*)\]", text.split("## References")[0]):
        for item in match.group(1).split(","):
            if "-" in item:
                lo, hi = map(int, item.split("-"))
                cited.update(range(lo, hi + 1))
            else:
                cited.add(int(item))
    return entries, cited


def audit(root=ROOT):
    errors = []
    files = {}
    for new, old in [("engineering_optimization_manuscript", "cmc_submission_manuscript"),
                     ("engineering_optimization_supplementary", "cmc_supplementary_materials")]:
        path = root / f"paper/{new}.md"
        text = path.read_text(encoding="utf-8")
        original = (root / f"paper/{old}.md").read_text(encoding="utf-8")
        rows = lambda t: [line for line in t.splitlines() if line.startswith("|")]
        historical = re.sub(r"### 2\.3 .*?(?=## 3 )", "", text, flags=re.S)
        historical = re.sub(r"### 6\.3 .*?(?=## 7 )", "", historical, flags=re.S)
        historical = historical.split("# S9 ")[0]
        if rows(historical) != rows(original):
            errors.append(f"Reported table rows changed in {new}")
        if "will be deposited in the public GitHub repository upon acceptance" in text:
            errors.append(f"Obsolete availability statement in {new}")
        files[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    main = (root / "paper/engineering_optimization_manuscript.md").read_text(encoding="utf-8")
    supp = (root / "paper/engineering_optimization_supplementary.md").read_text(encoding="utf-8")
    expected = [
        (main, "Fixed 0.3 histories place the selected-point failure fraction above the pool value"),
        (main, "greedy histories place it below the pool value"),
        (supp, "Fixed03 bars are positive and greedy bars are negative"),
        (main, "lower one-step improvement alone does not reject exploration"),
        (main, "it does not establish performance-preserving net savings"),
        (main, "it does not retrospectively alter any frozen experimental protocol"),
    ]
    for text, phrase in expected:
        if phrase not in text:
            errors.append(f"Missing evidence-boundary statement: {phrase}")
    entries, cited = references(main)
    if entries != list(range(1, len(entries) + 1)) or cited - set(entries):
        errors.append("Reference list is incomplete or not contiguous")
    block = supp.split("## S2.1", 1)[1].split("The corresponding selected-minus-pool", 1)[0]
    direction = []
    for line in block.splitlines():
        if re.match(r"\| (10|20|40) \| (fixed03|greedy) \|", line):
            d, history, pool, selected = [x.strip() for x in line.strip("|").split("|")]
            delta = float(selected) - float(pool)
            if not (delta > 0 if history == "fixed03" else delta < 0):
                errors.append(f"Table contradicts direction: D={d}, {history}")
            direction.append({"dimension": int(d), "history": history, "selected_minus_pool": round(delta, 4)})
    if len(direction) != 6:
        errors.append("Expected six history-direction checks")
    format_complete=False
    status_path=root / "paper/engineering_optimization/pdf_build_status.json"
    if status_path.exists():
        status=json.loads(status_path.read_text())
        format_complete=bool(status.get("pdf_compiled") and status.get("layout_verified"))
        for name,digest in status.get("source_hashes",{}).items():
            current=root / "paper/engineering_optimization" / name
            if not current.exists() or hashlib.sha256(current.read_bytes()).hexdigest()!=digest:
                format_complete=False
        for stem,record in status.get("documents",{}).items():
            current=root / "paper/engineering_optimization" / f"EO_{stem}.pdf"
            if not current.exists() or hashlib.sha256(current.read_bytes()).hexdigest()!=record.get("sha256"):
                format_complete=False
    remaining=["Author affiliations 2 and 3 and substantive author review/approval",
               "Accurate AI disclosure and publisher-policy review",
               "Current journal-specific author instructions and portal requirements",
               "Journal editorial judgment of methodological novelty; acceptance not guaranteed"]
    if not format_complete:
        remaining.insert(1,"Final submission-format compilation and rendered layout verification")
    return {"errors": errors, "source_hashes": files, "numeric_table_rows_unchanged": not any("table rows" in e for e in errors),
            "direction_checks": direction, "reference_count": len(entries),
            "submission_ready": False,
            "format_compiled_and_rendered": format_complete, "unresolved": remaining}



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    raise SystemExit(bool(result["errors"]))

