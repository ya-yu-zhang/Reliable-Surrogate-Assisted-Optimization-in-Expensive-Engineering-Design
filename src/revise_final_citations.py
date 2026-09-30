"""Create a citation-corrected derivative of the future final English manuscript."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from .audit_manuscript_citations import audit_text


ROOT = Path(__file__).resolve().parents[1]
OLD = (
    "We preselected BBOB functions 1, 3, 6, 10, 15, 20, 21, and 24, "
    "dimensions 10 and 20, instances 1–3, and three repeats per instance."
)
NEW = (
    "Using the COCO BBOB specification and IOHexperimenter implementation [8,9], "
    "we preselected functions 1, 3, 6, 10, 15, 20, 21, and 24, dimensions 10 and 20, "
    "instances 1–3, and three repeats per instance."
)


def revise(text: str) -> str:
    assert text.count(OLD) == 1
    assert text.count(NEW) == 0
    revised = text.replace(OLD, NEW, 1)
    audit = audit_text(revised, "# References")
    assert not audit["undefined_citations"]
    assert not audit["uncited_references"]
    return revised


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source = ROOT / args.input
    output = ROOT / args.output
    assert source.is_file() and not output.exists()
    revised = revise(source.read_text("utf-8"))
    output.write_text(revised, encoding="utf-8")
    record = {
        "source": source.relative_to(ROOT).as_posix(),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "output": output.relative_to(ROOT).as_posix(),
        "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "change": "Add explicit [8,9] citation to the COCO BBOB/IOHexperimenter protocol sentence.",
        "scientific_results_changed": False,
    }
    output.with_suffix(output.suffix + ".source.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
