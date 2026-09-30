"""Accept visual QA only from a complete, page-addressed review record."""
import hashlib
import json
from pathlib import Path

from .run_solo_cost import process_inventory


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/all_pdf_visual_review_v1"
CHECKS = ["readable", "no_clipping", "numbering_and_references", "no_unintended_blank", "evidence_boundaries"]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_review(root, status, review):
    assert status["stage"] == "rendered_pending_visual_inspection"
    assert not status["visual_quality_verified"] and status["failure"] is None
    papers = status["papers"]
    assert status["expected_pdfs"] == len(papers) == 8
    assert review["schema"] == 1 and review["all_pass"]
    assert review["reviewer"] and review["reviewed_at"]
    assert set(review["papers"]) == set(papers)
    manifest = {}
    for label, record in papers.items():
        decision = review["papers"][label]
        assert decision["verdict"] == "pass"
        assert decision["unresolved_issues"] == []
        assert set(decision["checks"]) == set(CHECKS)
        assert all(decision["checks"].values())
        pages = int(record["pages"])
        assert record["rendered_pages"] == pages and pages > 0
        assert decision["inspected_pages"] == list(range(1, pages + 1))
        assert set(decision["page_sha256"]) == {str(number) for number in range(1, pages + 1)}
        pdf = root / record["pdf"]
        assert digest(pdf) == record["pdf_sha256"] == decision["pdf_sha256"]
        render_label = label.removeprefix("final_") if label.startswith("final_") else label
        page_dir = root / record["rendering_record"] / render_label / "pages"
        images = sorted(page_dir.glob("page-*.png"))
        assert len(images) == pages
        for number, image in enumerate(images, 1):
            assert digest(image) == decision["page_sha256"][str(number)]
        manifest[label] = dict(
            pdf=record["pdf"], pdf_sha256=record["pdf_sha256"], pages=pages,
            rendered_page_sha256=decision["page_sha256"], verdict="pass",
        )
    return manifest


def main():
    status_path = OUT / "status.json"
    status = json.loads(status_path.read_text("utf-8"))
    assert not status["visual_quality_verified"], "Visual review is already finalized"
    alive = {process["ProcessId"] for process in process_inventory()}
    assert status["pid"] not in alive, "Rendering process is still live"
    frozen = json.loads((ROOT / "docs/frozen_visual_finalization_v1/sha256.json").read_text("utf-8"))
    assert all(digest(ROOT / name) == value for name, value in frozen.items())
    review_path = OUT / "review.json"
    review = json.loads(review_path.read_text("utf-8"))
    manifest = validate_review(ROOT, status, review)
    record = dict(
        schema=1,
        review_sha256=digest(review_path),
        reviewer=review["reviewer"],
        reviewed_at=review["reviewed_at"],
        papers=manifest,
    )
    (OUT / "reviewed_pdf_manifest.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    status["stage"] = "complete"
    status["visual_quality_verified"] = True
    status["review_sha256"] = record["review_sha256"]
    status["reviewed_pdf_manifest_sha256"] = digest(OUT / "reviewed_pdf_manifest.json")
    status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    print("All eight PDFs have a complete page-addressed visual review record.", flush=True)


if __name__ == "__main__":
    main()
