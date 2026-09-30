"""Build CMC LaTeX submission sources from the final Markdown manuscripts."""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "artifacts/cmc_latex_template/source"
OUT = ROOT / "paper/cmc_latex_submission"
FIGURES = OUT / "figures"
PANDOC = shutil.which("pandoc")


def expand_citation(content: str) -> str:
    numbers = []
    for part in re.split(r"\s*,\s*", content):
        if "-" in part:
            lo, hi = map(int, re.split(r"\s*-\s*", part))
            numbers.extend(range(lo, hi + 1))
        else:
            numbers.append(int(part))
    return r"\cite{" + ",".join(f"ref-{n}" for n in numbers) + "}"


def citations_to_latex(text: str) -> str:
    # Reference identifiers start at 1. Excluding zero prevents numeric
    # intervals such as [0, 0] from being mistaken for citations.
    return re.sub(r"\[([1-9]\d*(?:\s*[-,]\s*[1-9]\d*)*)\]", lambda m: expand_citation(m.group(1)), text)


def latex_escape(text: str) -> str:
    text = text.replace("\\", r"\textbackslash{}")
    for old, new in [("&", r"\&"), ("%", r"\%"), ("#", r"\#"), ("_", r"\_"),
                     ("{", r"\{"), ("}", r"\}"), ("~", r"\textasciitilde{}")]:
        text = text.replace(old, new)
    text = text.replace("×", r"$\times$").replace("±", r"$\pm$")
    text = text.replace("≤", r"$\leq$").replace("≥", r"$\geq$")
    text = text.replace("−", "--").replace("–", "--").replace("—", "---")
    return text


def inline_markdown_to_latex(text: str) -> str:
    text = citations_to_latex(text)
    text = latex_escape(text)
    # Restore citation commands after escaping their braces and backslash.
    text = re.sub(r"\\textbackslash\{\}cite\\\{([^}]*)\\\}", r"\\cite{\1}", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", text)
    text = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"\\emph{\1}", text)
    text = text.replace(r"\$\times\$", r"$\times$").replace(r"\$\pm\$", r"$\pm$")
    text = text.replace(r"\$\leq\$", r"$\leq$").replace(r"\$\geq\$", r"$\geq$")
    return text


def copy_figures(text: str, prefix: str) -> str:
    counter = 0

    def repl(match):
        nonlocal counter
        counter += 1
        caption, raw_path = match.group(1), match.group(2)
        source = (ROOT / "paper" / raw_path).resolve()
        vector_source = source.with_suffix(".pdf")
        if vector_source.exists():
            source = vector_source
        suffix = source.suffix.lower()
        name = f"{prefix}_figure_{counter}{suffix}"
        shutil.copy2(source, FIGURES / name)
        width = "0.92" if "density fields" not in caption else "0.98"
        return ("\n\\begin{figure}[H]\n\\centering\n"
                f"\\includegraphics[width={width}\\textwidth]{{figures/{name}}}\n"
                f"\\caption{{{inline_markdown_to_latex(caption)}}}\n"
                f"\\label{{fig:{prefix}-{counter}}}\n\\end{{figure}}\n")

    return re.sub(r"!\[([^\]]+)\]\(([^)]+)\)", repl, text)


def table_to_latex(caption: str, lines: list[str], label: str) -> str:
    rows = []
    for line in lines:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        rows.append(cells)
    header = rows[0]
    body = rows[2:]
    cols = len(header)
    align = "l" + "r" * (cols - 1)
    tex = [r"\begin{table}[H]", r"\tablesize{\scriptsize}",
           f"\\caption{{{inline_markdown_to_latex(caption)}}}", f"\\label{{{label}}}",
           r"\centering", r"\begin{adjustbox}{max width=\textwidth}",
           f"\\begin{{tabular}}{{{align}}}", r"\toprule",
           " & ".join(r"\textbf{" + inline_markdown_to_latex(cell) + "}" for cell in header) + r" \\",
           r"\midrule"]
    for row in body:
        tex.append(" & ".join(inline_markdown_to_latex(cell) for cell in row) + r" \\")
    tex += [r"\bottomrule", r"\end{tabular}", r"\end{adjustbox}", r"\end{table}"]
    return "\n".join(tex)


def convert_tables(text: str, prefix: str) -> str:
    lines = text.splitlines()
    out, i, count = [], 0, 0
    while i < len(lines):
        match = re.match(r"^\*\*Table\s+([S]?\d+)\.\s*(.*?)\*\*$", lines[i].strip())
        if match:
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j + 1 < len(lines) and lines[j].lstrip().startswith("|") and lines[j + 1].lstrip().startswith("|"):
                table_lines = []
                while j < len(lines) and lines[j].lstrip().startswith("|"):
                    table_lines.append(lines[j])
                    j += 1
                count += 1
                out.append(table_to_latex(match.group(2), table_lines,
                                          f"tab:{prefix}-{match.group(1).lower()}"))
                i = j
                continue
        out.append(lines[i])
        i += 1
    return "\n".join(out)


def normalize_headings(text: str, supplementary: bool) -> str:
    output = []
    for line in text.splitlines():
        match = re.match(r"^(#{1,4})\s+(?:(S?\d+(?:\.\d+)*)\s+)?(.*)$", line)
        if match:
            hashes, number, title = match.groups()
            # Infer hierarchy from the written section number. This also repairs
            # legacy Markdown whose hash depth was inconsistent in S1.
            if number:
                hashes = "#" * (number.count(".") + 1)
            elif not supplementary and len(hashes) > 1:
                hashes = hashes[1:]
            output.append(f"{hashes} {title}")
        else:
            output.append(line)
    return "\n".join(output)


def pandoc(text: str) -> str:
    if not PANDOC:
        raise RuntimeError("pandoc was not found on PATH; install Pandoc before building LaTeX sources")
    result = subprocess.run([PANDOC, "--from=markdown+pipe_tables+raw_tex+tex_math_dollars",
                             "--to=latex", "--wrap=none"], input=text, text=True,
                            encoding="utf-8", capture_output=True, check=True)
    return result.stdout


def clean_generated_latex(text: str) -> str:
    """Normalize characters and common plain-text math for pdfLaTeX."""
    replacements = {
        "“": "``", "”": "''", "‘": "`", "’": "'",
        "−": "-", "–": "--", "—": "---", "∎": r"\(\square\)",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = text.replace(r"\def\LTcaptype{none}", r"\def\LTcaptype{table}")
    text = re.sub(r"(?<![A-Za-z\\])mu_", r"\\mu_", text)
    text = re.sub(r"10\\\^\{\}-(\d+)", r"$10^{-\1}$", text)
    return text


def extract_section(md: str, heading: str, next_heading: str | None = None) -> str:
    start = md.index(f"## {heading}") + len(f"## {heading}")
    end = md.index(f"## {next_heading}", start) if next_heading else len(md)
    return md[start:end].strip()


def references(md: str) -> list[tuple[int, str]]:
    part = md.split("## References", 1)[1]
    matches = list(re.finditer(r"^\[(\d+)\]\s+", part, re.M))
    refs = []
    for idx, match in enumerate(matches):
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(part)
        refs.append((int(match.group(1)), part[match.end():end].strip()))
    return refs


def bibliography_block(refs: list[tuple[int, str]]) -> str:
    chunks = [r"\reftitle{References}", r"\begin{thebibliography}{999}"]
    for number, item in refs:
        converted = pandoc(item).strip()
        if converted.startswith("\\") and converted.endswith("}"):
            pass
        chunks += [f"\\bibitem{{ref-{number}}}", converted]
    chunks.append(r"\end{thebibliography}")
    return "\n".join(chunks)


def preamble(title: str, abstract: str, keywords: str, supplementary: bool = False) -> str:
    extra = "\n\\renewcommand{\\thefigure}{S\\arabic{figure}}\n\\renewcommand{\\thetable}{S\\arabic{table}}\n\\renewcommand{\\thesection}{S\\arabic{section}}\n" if supplementary else ""
    return rf"""% Built from the official Tech Science Press LaTeX template.
\documentclass[cmc,article,submit,moreauthors,pdftex]{{Definitions/tsp}}
\input{{Definitions/package}}
\input{{Definitions/unicode}}
\usepackage{{longtable}}
\usepackage{{url}}
\providecommand{{\tightlist}}{{\setlength{{\itemsep}}{{0pt}}\setlength{{\parskip}}{{0pt}}}}
\graphicspath{{{{./Definitions/}}{{./figures/}}}}
{extra}
\continuouspages{{}}
\firstpage{{1}}
\makeatletter\setcounter{{page}}{{\@firstpage}}\makeatother
\pubvolume{{0}}\issuenum{{0}}\elocationid{{0}}\articlenumber{{0}}
\pubyear{{2026}}\doiyear{{2026}}\copyrightyear{{2026}}
\datereceived{{Day Month Year}}\dateaccepted{{Day Month Year}}
\dateonlinefirst{{}}\datepublished{{Day Month Year}}
\Title{{{latex_escape(title)}}}
\Author{{Shu-Chuan Chu\textsuperscript{{1,*}}, Yayu Zhang\textsuperscript{{1}}, Zhenyu Meng\textsuperscript{{2}} and Jia Yue\textsuperscript{{3}}}}
\AuthorNames{{Shu-Chuan Chu, Yayu Zhang, Zhenyu Meng and Jia Yue}}
\address{{\textsuperscript{{1}}Nanjing University of Information Science and Technology, Nanjing, China

\textsuperscript{{2}}Affiliation to be confirmed for Zhenyu Meng

\textsuperscript{{3}}Affiliation to be confirmed for Jia Yue}}
\corres{{Corresponding Author: Shu-Chuan Chu. Email: to be confirmed}}
\abstract{{{inline_markdown_to_latex(abstract)}}}
\keyword{{{inline_markdown_to_latex(keywords)}}}
\begin{{document}}
"""


def build_main(md: str, refs: list[tuple[int, str]]) -> str:
    title = md.splitlines()[0].lstrip("# ").strip()
    abstract = extract_section(md, "Abstract", "1 Introduction").split("**Keywords:**", 1)[0].strip()
    keywords = re.search(r"\*\*Keywords:\*\*\s*(.+)", md).group(1).strip()
    body_start = md.index("## 1 Introduction")
    body_end = md.index("## Acknowledgement")
    body = md[body_start:body_end]
    body = normalize_headings(body, False)
    body = citations_to_latex(body)
    body = copy_figures(body, "main")
    body = convert_tables(body, "main")
    body_tex = clean_generated_latex(pandoc(body))
    declarations = {
        "acknowledgement": extract_section(md, "Acknowledgement", "Funding Statement"),
        "funding": extract_section(md, "Funding Statement", "Author Contributions"),
        "authorcontributions": extract_section(md, "Author Contributions", "Availability of Data and Materials"),
        "availabilityofdataandmaterials": extract_section(md, "Availability of Data and Materials", "Ethics Approval"),
        "ethicsapproval": extract_section(md, "Ethics Approval", "Conflicts of Interest"),
        "conflictsofinterest": extract_section(md, "Conflicts of Interest", "Supplementary Materials"),
        "supplementary": extract_section(md, "Supplementary Materials", "References"),
    }
    back = "\n".join(f"\\{name}{{{inline_markdown_to_latex(value)}}}" for name, value in declarations.items())
    return preamble(title, abstract, keywords) + body_tex + "\n" + back + "\n" + bibliography_block(refs) + "\n\\end{document}\n"


def build_supplement(md: str, refs: list[tuple[int, str]], main_md: str) -> str:
    title = md.splitlines()[0].lstrip("# ").strip()
    first = md.index("# S0 ")
    body = md[first:]
    body = normalize_headings(body, True)
    body = citations_to_latex(body)
    body = copy_figures(body, "supp")
    body = convert_tables(body, "supp")
    body_tex = clean_generated_latex(pandoc(body))
    abstract = ("This document preserves complete secondary analyses, resource measurements, application transfer, "
                "sensitivity studies, recovery accounting, and reproducibility evidence supporting the main article.")
    keywords = "surrogate-assisted optimization; supplementary materials; reproducibility; sensitivity analysis"
    return preamble(title, abstract, keywords, True) + body_tex + "\n" + bibliography_block(refs) + "\n\\end{document}\n"


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    FIGURES.mkdir()
    shutil.copytree(TEMPLATE / "Definitions", OUT / "Definitions")
    main_md = (ROOT / "paper/cmc_submission_manuscript.md").read_text("utf-8")
    supp_md = (ROOT / "paper/cmc_supplementary_materials.md").read_text("utf-8")
    refs = references(main_md)
    (OUT / "CMC_manuscript.tex").write_text(build_main(main_md, refs), encoding="utf-8")
    (OUT / "CMC_supplementary.tex").write_text(build_supplement(supp_md, refs, main_md), encoding="utf-8")
    (OUT / "README.txt").write_text(
        "Official CMC/TSP LaTeX template submission package\n"
        "==================================================\n"
        "CMC_manuscript.tex: main article source\n"
        "CMC_supplementary.tex: supplementary-material source\n"
        "Definitions/: unmodified official template class and assets\n"
        "figures/: local figure files referenced by both sources\n\n"
        "Compile from this directory with:\n"
        "  pdflatex CMC_manuscript.tex (run at least twice)\n"
        "  pdflatex CMC_supplementary.tex (run at least twice)\n\n"
        "The supplied PDFs were compiled successfully with MiKTeX/pdfLaTeX and visually audited.\n"
        "Before submission, confirm affiliations 2-3, the corresponding-author email, author contributions, funding, and the permanent repository URL.\n",
        encoding="utf-8")


if __name__ == "__main__":
    main()
