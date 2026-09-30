import hashlib
import json

from src.audit_final_delivery_citation_v2 import require_citation_visual_complete


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_corrected_visual_manifest_is_required(tmp_path):
    directory = tmp_path / "results/all_pdf_visual_review_citation_v2"
    directory.mkdir(parents=True)
    papers = {}
    for index in range(8):
        label = "final_english_citation_revision" if index == 0 else f"paper_{index}"
        pdf = tmp_path / f"paper-{index}.pdf"
        pdf.write_bytes(f"pdf-{index}".encode())
        papers[label] = {
            "pdf": pdf.relative_to(tmp_path).as_posix(),
            "pdf_sha256": digest(pdf),
            "pages": 1,
            "rendered_page_sha256": {"1": "page-hash"},
            "verdict": "pass",
        }
    reviewed = {"schema": 1, "review_sha256": "review-hash", "papers": papers}
    reviewed_path = directory / "reviewed_pdf_manifest.json"
    reviewed_path.write_text(json.dumps(reviewed), encoding="utf-8")
    status = {
        "stage": "complete",
        "visual_quality_verified": True,
        "failure": None,
        "expected_pdfs": 8,
        "papers": {label: {} for label in papers},
        "review_sha256": "review-hash",
        "reviewed_pdf_manifest_sha256": digest(reviewed_path),
    }
    (directory / "status.json").write_text(json.dumps(status), encoding="utf-8")
    loaded, manifest = require_citation_visual_complete(tmp_path)
    assert loaded["visual_quality_verified"] and len(manifest["papers"]) == 8
