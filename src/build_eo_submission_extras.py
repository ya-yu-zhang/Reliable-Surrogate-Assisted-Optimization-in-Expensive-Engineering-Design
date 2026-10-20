"""Build the Engineering Optimization cover letter and highlights."""

from __future__ import annotations

import shutil
import stat
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Inches, Pt


ROOT = Path(__file__).resolve().parents[1]
OUTDIR = ROOT / "paper" / "eo_submission"
TMPDIR = ROOT / "tmp" / "eo_cover_highlights"
REFERENCE = Path(
    r"E:\新建文件夹\xwechat_files\wxid_gatb8ol0b1zd21_b04b\msg\file\2026-07\Cover letter-reference.docx"
)


def set_font(run, size: float = 12, *, bold: bool = False, italic: bool = False) -> None:
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    rfonts = run._element.get_or_add_rPr().get_or_add_rFonts()
    for name in ("ascii", "hAnsi", "eastAsia", "cs"):
        rfonts.set(qn(f"w:{name}"), "Times New Roman")


def replace_paragraph(paragraph, segments: list[tuple[str, bool, bool]]) -> None:
    paragraph.clear()
    for text, bold, italic in segments:
        run = paragraph.add_run(text)
        set_font(run, bold=bold, italic=italic)


def build_cover_letter() -> Path:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    target = OUTDIR / "EO_cover_letter.docx"
    if target.exists():
        target.chmod(stat.S_IWRITE | stat.S_IREAD)
    shutil.copy2(REFERENCE, target)
    target.chmod(stat.S_IWRITE | stat.S_IREAD)
    doc = Document(target)
    paragraphs = doc.paragraphs
    if len(paragraphs) != 24:
        raise RuntimeError(f"Expected 24 template paragraphs, found {len(paragraphs)}")

    content: list[list[tuple[str, bool, bool]]] = [
        [("Dear Editor-in-Chief,", False, False)],
        [("", False, False)],
        [
            ("Please consider the manuscript entitled ", False, False),
            ("“Decision-consequence auditing for surrogate-assisted optimization in expensive engineering design”", True, False),
            (" for publication in ", False, False),
            ("Engineering Optimization", False, True),
            (".", False, False),
        ],
        [("Surrogate-assisted optimization can report credible uncertainty or residual diagnostics without changing candidate ranking or improving a paid engineering decision. The submitted study addresses this gap by auditing the complete path from surrogate information to evaluation allocation, finite-horizon policy performance, and physical-call cost.", False, False)],
        [("Core Scientific Contributions", True, False)],
        [("The manuscript's contributions are:", False, False)],
        [("Decision-path audit: ", True, False), ("Calibration, structural decision influence, frozen-state utility, closed-loop performance, and total cost are evaluated as distinct evidence levels.", False, False)],
        [("Query allocation by decision equivalence: ", True, False), ("Identical context-point decisions share deterministic responses, so the same exact immediate-utility report costs 138 paid finite-element solves instead of 480, with a minimality argument for the declared oracle.", False, False)],
        [("Recorded verdicts and engineering validation: ", True, False), ("One declared promotion rule applied to three frozen acquisition rules returns one promotion, one stop and one held-for-revision verdict; the procedure is applied to 24 BBOB functions, a finite-element beam family, frozen acquisition states and twenty transfer cases at two load positions.", False, False)],
        [("Engineering Optimization Scope Alignment", True, False)],
        [("The study concerns numerical optimization when function evaluations are expensive and surrogate model management determines which simulations are paid for. Its object is the reliability of the decision, not prediction accuracy in isolation, and it claims no optimizer superiority.", False, False)],
        [("The manuscript contributes directly to two areas within the journal's scope:", False, False)],
        [("Surrogate model management for expensive optimization: ", True, False), ("The audit determines whether model-derived information changes ranking, selects a more useful action at a common state, and improves a validated trajectory.", False, False)],
        [("Optimization in engineering design: ", True, False), ("A density-based finite-element beam problem compares residual control, Gaussian-process acquisition, relation-model evolutionary search, and trust-region optimization under explicit evaluation budgets.", False, False)],
        [("Reproducibility and Publication Ethics", True, False)],
        [("Frozen protocols, deterministic seed maps, prediction-before-label journals, source hashes and recovery-aware cost ledgers support the reported evidence. The sources and curated records will be released in the project repository upon acceptance and are available to reviewers on request.", False, False)],
        [("The manuscript is original, is not under consideration elsewhere (an earlier version was submitted to Computers, Materials & Continua and rejected there as out of scope), and has been approved by all authors. No conflicts of interest or specific funding are reported. DeepSeek V4.1 Flash (version 1017) was used only for copyediting and language refinement. The authors confirm the originality and accuracy of the content, have checked the tool's terms of use and confirm that this use is suitable for publication, and take full responsibility for the integrity of the whole content, including the accuracy of the references.", False, False)],
        [("Thank you for considering this work. The manuscript is intended to provide Engineering Optimization readers with a reproducible way to test whether surrogate information produces valuable engineering decisions before large simulation budgets are committed.", False, False)],
        [("", False, False)],
        [("Sincerely,", False, False)],
        [("", False, False)],
        [("Jeng-Shyang Pan, Ph.D.\nCorresponding author, on behalf of all authors", False, False)],
        [("School of Computer Science\nSchool of Artificial Intelligence/School of Future Technology\nNanjing University of Information Science and Technology", False, False)],
        [("Email: 100112@nuist.edu.cn", False, False)],
    ]
    for paragraph, segments in zip(paragraphs, content, strict=True):
        replace_paragraph(paragraph, segments)
    doc.core_properties.title = "Cover Letter for Engineering Optimization"
    doc.core_properties.author = "Jeng-Shyang Pan"
    doc.core_properties.last_modified_by = "Jeng-Shyang Pan"
    doc.save(target)
    return target


def build_highlights_docx() -> Path:
    TMPDIR.mkdir(parents=True, exist_ok=True)
    target = TMPDIR / "Highlights.docx"
    doc = Document()
    section = doc.sections[0]
    section.page_width = Inches(8.27)
    section.page_height = Inches(11.69)
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")

    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_after = Pt(14)
    run = title.add_run("Highlights")
    set_font(run, size=14, bold=True)

    highlights = [
        "Audits whether surrogate signals change a paid engineering decision.",
        "Screens ranking-invariant corrections before expensive evaluations.",
        "Recorded verdicts: one acquisition rule promoted, one stopped, one held.",
        "Exact immediate-utility reporting costs 138 solves instead of 480.",
        "Separates calibration evidence from optimization utility and reports full costs.",
    ]
    for item in highlights:
        paragraph = doc.add_paragraph(style="List Bullet")
        paragraph.paragraph_format.space_after = Pt(6)
        paragraph.paragraph_format.line_spacing = 1.15
        run = paragraph.add_run(item)
        set_font(run)
    doc.core_properties.title = "Highlights"
    doc.core_properties.author = "Jeng-Shyang Pan"
    doc.core_properties.last_modified_by = "Jeng-Shyang Pan"
    doc.save(target)
    return target


def main() -> None:
    print(build_cover_letter())
    print(build_highlights_docx())


if __name__ == "__main__":
    main()
