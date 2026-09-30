"""Render the corrected final English PDF and compose the authoritative eight-PDF review set."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
from time import perf_counter, sleep

from .finish_final_visual_review import contact_sheets, digest, page_count, page_diagnostics
from .run_solo_cost import process_inventory


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/all_pdf_visual_review_citation_v2"


def compose_papers(original: dict, revised: dict) -> dict:
    assert "final_english" in original and len(original) == 8
    retained = {label: record for label, record in original.items() if label != "final_english"}
    assert len(retained) == 7
    retained["final_english_citation_revision"] = revised
    return retained


def main() -> None:
    assert not OUT.exists(), "Citation visual-review v2 already exists"
    frozen_root = ROOT / "docs/frozen_citation_visual_protocol_v2"
    frozen = json.loads((frozen_root / "sha256.json").read_text("utf-8"))
    assert all(digest(frozen_root / name) == expected for name, expected in frozen.items())
    OUT.mkdir(parents=True)
    started = perf_counter()
    stage = "waiting_for_original_rendering_and_citation_revision"
    failure = None
    papers = {}

    def save() -> None:
        (OUT / "status.json").write_text(
            json.dumps(
                {
                    "stage": stage,
                    "pid": os.getpid(),
                    "elapsed": perf_counter() - started,
                    "failure": failure,
                    "visual_quality_verified": False,
                    "expected_pdfs": 8,
                    "papers": papers,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def execute(command: list[str], log: str) -> str:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        (OUT / log).write_text(result.stdout + result.stderr, encoding="utf-8")
        if result.returncode:
            raise RuntimeError(f"exit {result.returncode}; retained {log}")
        return result.stdout + result.stderr

    try:
        save()
        while True:
            original = json.loads((ROOT / "results/all_pdf_visual_review_v1/status.json").read_text("utf-8"))
            revision = json.loads((ROOT / "results/citation_revision_completion_v1/status.json").read_text("utf-8"))
            live = {row["ProcessId"] for row in process_inventory()}
            for label, status in (("original renderer", original), ("citation revision", revision)):
                if status["stage"] == "failed" or status["failure"] is not None:
                    raise RuntimeError(f"{label} failed")
            ready_original = original["stage"] in {"rendered_pending_visual_inspection", "complete"} and original["pid"] not in live
            ready_revision = revision["stage"] == "compiled_pending_visual_review" and revision["pid"] not in live
            if ready_original and ready_revision:
                break
            for label, status in (("original renderer", original), ("citation revision", revision)):
                if status["pid"] not in live and status["stage"] not in {
                    "rendered_pending_visual_inspection", "complete", "compiled_pending_visual_review"
                }:
                    raise RuntimeError(f"{label} ended before its terminal waiting stage")
            save()
            sleep(30)

        assert all(digest(frozen_root / name) == expected for name, expected in frozen.items())
        stage = "rendering_revised_english_pdf"
        save()
        pdf = ROOT / revision["pdf"]["path"]
        assert digest(pdf) == revision["pdf"]["sha256"] and pdf.stat().st_size > 10000
        # validate_review strips the ``final_`` label prefix when resolving
        # rendered pages, matching the original final-review directory scheme.
        target = OUT / "english_citation_revision"
        pages = target / "pages"
        pages.mkdir(parents=True)
        info = execute(["pdfinfo", str(pdf)], "revised_pdfinfo.log")
        expected = page_count(info)
        execute(["pdftoppm", "-png", "-r", "144", str(pdf), str(pages / "page")], "revised_render.log")
        rendered = sorted(pages.glob("page-*.png"))
        assert len(rendered) == expected
        text_path = target / "extracted.txt"
        execute(["pdftotext", "-layout", str(pdf), str(text_path)], "revised_text.log")
        extracted = text_path.read_text("utf-8", errors="replace")
        diagnostics = page_diagnostics(rendered)
        contacts = contact_sheets(rendered, target / "contacts")
        (target / "page_diagnostics.json").write_text(json.dumps(diagnostics, indent=2), encoding="utf-8")
        revised_record = {
            "pdf": pdf.relative_to(ROOT).as_posix(),
            "pdf_sha256": digest(pdf),
            "pages": expected,
            "rendered_pages": len(rendered),
            "contact_sheets": len(contacts),
            "replacement_characters": extracted.count("\ufffd"),
            "near_blank_pages": [row["page"] for row in diagnostics if row["near_blank"]],
            "possible_edge_contact_pages": [row["page"] for row in diagnostics if row["possible_edge_contact"]],
            "rendering_record": "results/all_pdf_visual_review_citation_v2",
        }
        papers = compose_papers(original["papers"], revised_record)
        assert len(papers) == 8
        for label, record in papers.items():
            source_pdf = ROOT / record["pdf"]
            assert digest(source_pdf) == record["pdf_sha256"], label
            assert record["pages"] == record["rendered_pages"] > 0
        stage = "rendered_pending_visual_inspection"
        save()
    except Exception as error:
        failure = {"error_type": type(error).__name__, "error": str(error)}
        stage = "failed"
        save()
        raise


if __name__ == "__main__":
    main()
