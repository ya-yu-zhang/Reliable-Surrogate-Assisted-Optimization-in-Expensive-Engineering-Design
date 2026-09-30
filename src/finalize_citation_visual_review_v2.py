"""Finalize page-addressed visual acceptance for the citation-corrected eight-PDF set."""

from __future__ import annotations

import json
from pathlib import Path

from .finalize_all_pdf_visual_review import digest, validate_review
from .run_solo_cost import process_inventory


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/all_pdf_visual_review_citation_v2"


def main() -> None:
    status_path = OUT / "status.json"
    status = json.loads(status_path.read_text("utf-8"))
    assert not status["visual_quality_verified"]
    live = {row["ProcessId"] for row in process_inventory()}
    assert status["pid"] not in live
    frozen_root = ROOT / "docs/frozen_citation_visual_protocol_v2"
    frozen = json.loads((frozen_root / "sha256.json").read_text("utf-8"))
    assert all(digest(frozen_root / name) == expected for name, expected in frozen.items())
    review_path = OUT / "review.json"
    review = json.loads(review_path.read_text("utf-8"))
    manifest = validate_review(ROOT, status, review)
    record = {
        "schema": 1,
        "review_sha256": digest(review_path),
        "reviewer": review["reviewer"],
        "reviewed_at": review["reviewed_at"],
        "papers": manifest,
    }
    manifest_path = OUT / "reviewed_pdf_manifest.json"
    manifest_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    status["stage"] = "complete"
    status["visual_quality_verified"] = True
    status["review_sha256"] = record["review_sha256"]
    status["reviewed_pdf_manifest_sha256"] = digest(manifest_path)
    status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
