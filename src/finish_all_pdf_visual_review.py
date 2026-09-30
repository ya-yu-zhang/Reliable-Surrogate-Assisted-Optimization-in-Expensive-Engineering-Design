"""Render every bilingual evidence-stage PDF after final-paper rendering."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
from time import perf_counter, sleep

from .finish_final_visual_review import contact_sheets, digest, page_count, page_diagnostics
from .run_solo_cost import process_inventory


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/all_pdf_visual_review_v1"
INTERMEDIATE = [
    ("english_integrated_manuscript", "integrated_english"),
    ("论文综合机制稿", "integrated_chinese"),
    ("english_high_extension_manuscript", "high_english"),
    ("论文高维扩展机制稿", "high_chinese"),
    ("english_complete_mechanism_manuscript", "sensitivity_english"),
    ("论文完整机制稿", "sensitivity_chinese"),
]


def main():
    assert not OUT.exists(), "All-PDF visual-review record exists; refuse duplicate restart"
    frozen_path = ROOT / "docs/frozen_all_pdf_visual_review_v1/sha256.json"
    frozen = json.loads(frozen_path.read_text("utf-8"))
    assert all(digest(ROOT / name) == value for name, value in frozen.items())
    OUT.mkdir(parents=True)
    stage = "waiting_for_final_pdf_rendering"
    failure = None
    papers = {}
    start = perf_counter()

    def save():
        (OUT / "status.json").write_text(
            json.dumps(
                dict(
                    stage=stage,
                    pid=os.getpid(),
                    elapsed=perf_counter() - start,
                    failure=failure,
                    visual_quality_verified=False,
                    expected_pdfs=8,
                    papers=papers,
                ),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def execute(command, log):
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        (OUT / log).write_text(result.stdout + result.stderr, encoding="utf-8")
        if result.returncode:
            raise RuntimeError(f"exit {result.returncode}; retained {log}")
        return result.stdout + result.stderr

    try:
        save()
        while True:
            prior = json.loads((ROOT / "results/final_visual_review_v1/status.json").read_text("utf-8"))
            alive = {process["ProcessId"] for process in process_inventory()}
            if prior["stage"] == "failed" or prior["failure"] is not None:
                raise RuntimeError("Final-paper rendering prerequisite failed")
            if prior["stage"] == "rendered_pending_visual_inspection" and prior["pid"] not in alive:
                break
            if prior["pid"] not in alive:
                raise RuntimeError("Final-paper renderer ended before all pages were produced")
            save()
            sleep(30)
        assert all(digest(ROOT / name) == value for name, value in frozen.items())
        for label, record in prior["papers"].items():
            page_dir = ROOT / "results/final_visual_review_v1" / label / "pages"
            rendered = sorted(page_dir.glob("page-*.png"))
            assert record["pages"] == record["rendered_pages"] == len(rendered)
            pdf = ROOT / record["pdf"]
            assert digest(pdf) == record["pdf_sha256"]
            papers[f"final_{label}"] = dict(**record, rendering_record="results/final_visual_review_v1")
        assert len(papers) == 2

        stage = "rendering_intermediate_pdfs"
        save()
        for name, label in INTERMEDIATE:
            pdf = ROOT / "paper/pdf" / f"{name}.pdf"
            assert pdf.is_file() and pdf.stat().st_size > 10000
            target = OUT / label
            pages = target / "pages"
            pages.mkdir(parents=True)
            info = execute(["pdfinfo", str(pdf)], f"{label}_pdfinfo.log")
            expected = page_count(info)
            execute(["pdftoppm", "-png", "-r", "144", str(pdf), str(pages / "page")], f"{label}_render.log")
            rendered = sorted(pages.glob("page-*.png"))
            assert len(rendered) == expected
            text_path = target / "extracted.txt"
            execute(["pdftotext", "-layout", str(pdf), str(text_path)], f"{label}_text.log")
            extracted = text_path.read_text("utf-8", errors="replace")
            diagnostics = page_diagnostics(rendered)
            contacts = contact_sheets(rendered, target / "contacts")
            papers[label] = dict(
                pdf=pdf.relative_to(ROOT).as_posix(),
                pdf_sha256=hashlib.sha256(pdf.read_bytes()).hexdigest(),
                pages=expected,
                rendered_pages=len(rendered),
                contact_sheets=len(contacts),
                replacement_characters=extracted.count("\ufffd"),
                near_blank_pages=[row["page"] for row in diagnostics if row["near_blank"]],
                possible_edge_contact_pages=[row["page"] for row in diagnostics if row["possible_edge_contact"]],
                rendering_record="results/all_pdf_visual_review_v1",
            )
            (target / "page_diagnostics.json").write_text(json.dumps(diagnostics, indent=2), encoding="utf-8")
            save()
        assert len(papers) == 8
        assert all(record["rendered_pages"] == record["pages"] for record in papers.values())
        stage = "rendered_pending_visual_inspection"
        save()
        print("All eight evidence-stage PDFs rendered; visual acceptance remains pending.", flush=True)
    except Exception as error:
        failure = dict(error_type=type(error).__name__, error=str(error))
        stage = "failed"
        save()
        raise


if __name__ == "__main__":
    main()
