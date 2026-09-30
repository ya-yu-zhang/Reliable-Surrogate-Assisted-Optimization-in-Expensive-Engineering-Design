"""Render the final bilingual PDFs and stop before visual acceptance."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from time import perf_counter, sleep

from PIL import Image, ImageDraw

from .run_solo_cost import process_inventory


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/final_visual_review_v1"
PAPERS = [
    ("english_budget_complete_manuscript", "english"),
    ("论文预算完整机制稿", "chinese"),
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def page_count(info: str) -> int:
    match = re.search(r"(?m)^Pages:\s+(\d+)\s*$", info)
    assert match, "pdfinfo did not report Pages"
    result = int(match.group(1))
    assert result > 0
    return result


def page_diagnostics(images):
    rows = []
    for number, path in enumerate(images, 1):
        with Image.open(path) as source:
            gray = source.convert("L")
            histogram = gray.histogram()
            pixels = gray.width * gray.height
            nonwhite = sum(histogram[:245]) / pixels
            border = max(2, min(gray.size) // 250)
            edge = Image.new("L", gray.size, 255)
            edge.paste(gray.crop((0, 0, gray.width, border)), (0, 0))
            edge.paste(gray.crop((0, gray.height - border, gray.width, gray.height)), (0, gray.height - border))
            edge.paste(gray.crop((0, 0, border, gray.height)), (0, 0))
            edge.paste(gray.crop((gray.width - border, 0, gray.width, gray.height)), (gray.width - border, 0))
            edge_histogram = edge.histogram()
            edge_dark = sum(edge_histogram[:220]) / pixels
            rows.append(
                dict(
                    page=number,
                    file=path.name,
                    width=gray.width,
                    height=gray.height,
                    nonwhite_fraction=nonwhite,
                    dark_edge_fraction=edge_dark,
                    near_blank=nonwhite < 0.001,
                    possible_edge_contact=edge_dark > 0,
                )
            )
    return rows


def contact_sheets(images, destination: Path, columns=2, rows=3, thumb_width=420):
    destination.mkdir(parents=True, exist_ok=True)
    outputs = []
    per_sheet = columns * rows
    for start in range(0, len(images), per_sheet):
        group = images[start : start + per_sheet]
        thumbs = []
        for number, path in enumerate(group, start + 1):
            with Image.open(path) as source:
                image = source.convert("RGB")
                height = round(image.height * thumb_width / image.width)
                image = image.resize((thumb_width, height), Image.Resampling.LANCZOS)
                thumbs.append((number, image))
        cell_height = max(image.height for _, image in thumbs) + 38
        sheet = Image.new("RGB", (columns * (thumb_width + 24) + 24, rows * cell_height + 24), "white")
        draw = ImageDraw.Draw(sheet)
        for index, (number, image) in enumerate(thumbs):
            x = 24 + (index % columns) * (thumb_width + 24)
            y = 24 + (index // columns) * cell_height
            draw.text((x, y), f"Page {number}", fill="black")
            sheet.paste(image, (x, y + 28))
        output = destination / f"contact-{start // per_sheet + 1:02d}.jpg"
        sheet.save(output, quality=90, optimize=True)
        outputs.append(output)
    return outputs


def main():
    assert not OUT.exists(), "Final visual-review record exists; refuse duplicate restart"
    frozen_path = ROOT / "docs/frozen_final_visual_review_v1/sha256.json"
    frozen = json.loads(frozen_path.read_text("utf-8"))
    assert all(digest(ROOT / name) == value for name, value in frozen.items())
    OUT.mkdir(parents=True)
    stage = "waiting_for_budget_pdf_export"
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
            prior = json.loads((ROOT / "results/budget_evidence_export_v1/status.json").read_text("utf-8"))
            alive = {process["ProcessId"] for process in process_inventory()}
            if prior["stage"] == "failed" or prior["failure"] is not None:
                raise RuntimeError("Budget PDF prerequisite failed")
            if prior["stage"] in ["compiled_pending_visual_review", "complete"] and prior["pid"] not in alive:
                break
            if prior["pid"] not in alive:
                raise RuntimeError("Budget PDF parent ended before successful compilation")
            save()
            sleep(30)
        assert all(digest(ROOT / name) == value for name, value in frozen.items())
        stage = "rendering_all_pages"
        save()
        for name, label in PAPERS:
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
                pdf_sha256=digest(pdf),
                pages=expected,
                rendered_pages=len(rendered),
                contact_sheets=len(contacts),
                replacement_characters=extracted.count("\ufffd"),
                near_blank_pages=[row["page"] for row in diagnostics if row["near_blank"]],
                possible_edge_contact_pages=[row["page"] for row in diagnostics if row["possible_edge_contact"]],
            )
            (target / "page_diagnostics.json").write_text(
                json.dumps(diagnostics, indent=2), encoding="utf-8"
            )
            save()
        assert all(value["rendered_pages"] == value["pages"] for value in papers.values())
        stage = "rendered_pending_visual_inspection"
        save()
        print("All final PDF pages rendered; visual acceptance remains pending.", flush=True)
    except Exception as error:
        failure = dict(error_type=type(error).__name__, error=str(error))
        stage = "failed"
        save()
        raise


if __name__ == "__main__":
    main()
