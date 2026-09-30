import hashlib

from src import finalize_all_pdf_visual_review as finalizer


def test_complete_page_addressed_review_is_required(tmp_path):
    papers = {}
    review_papers = {}
    labels = ["final_english", "final_chinese"] + [f"intermediate_{number}" for number in range(6)]
    for label in labels:
        record_root = "results/final_visual_review_v1" if label.startswith("final_") else "results/all_pdf_visual_review_v1"
        render_label = label.removeprefix("final_") if label.startswith("final_") else label
        pdf = tmp_path / "paper/pdf" / f"{label}.pdf"
        pdf.parent.mkdir(parents=True, exist_ok=True)
        pdf.write_bytes(("PDF-" + label).encode())
        page = tmp_path / record_root / render_label / "pages/page-1.png"
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_bytes(("PNG-" + label).encode())
        pdf_hash = hashlib.sha256(pdf.read_bytes()).hexdigest()
        page_hash = hashlib.sha256(page.read_bytes()).hexdigest()
        papers[label] = dict(
            pdf=pdf.relative_to(tmp_path).as_posix(), pdf_sha256=pdf_hash, pages=1,
            rendered_pages=1, rendering_record=record_root,
        )
        review_papers[label] = dict(
            pdf_sha256=pdf_hash, inspected_pages=[1], page_sha256={"1": page_hash},
            verdict="pass", unresolved_issues=[], checks={name: True for name in finalizer.CHECKS},
        )
    status = dict(
        stage="rendered_pending_visual_inspection", visual_quality_verified=False,
        failure=None, expected_pdfs=8, papers=papers,
    )
    review = dict(schema=1, all_pass=True, reviewer="test", reviewed_at="2026-09-19", papers=review_papers)
    assert len(finalizer.validate_review(tmp_path, status, review)) == 8
    review["papers"][labels[0]]["inspected_pages"] = []
    try:
        finalizer.validate_review(tmp_path, status, review)
    except AssertionError:
        pass
    else:
        raise AssertionError("Incomplete page review was accepted")
