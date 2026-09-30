"""Wait for the budget-complete manuscript, then build a citation-corrected derivative."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from time import perf_counter, sleep

from .audit_manuscript_citations import audit_text
from .run_solo_cost import process_inventory


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/citation_revision_completion_v1"
NAME = "english_budget_complete_manuscript_citation_revision"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert not OUT.exists(), "Citation-revision completion record already exists"
    frozen_root = ROOT / "docs/frozen_citation_revision_protocol_v1"
    frozen = json.loads((frozen_root / "sha256.json").read_text("utf-8"))
    assert all(digest(frozen_root / name) == expected for name, expected in frozen.items())
    OUT.mkdir(parents=True)
    started = perf_counter()
    stage = "waiting_for_budget_complete_manuscript"
    failure = None
    source_record = None
    pdf_record = None

    def save() -> None:
        (OUT / "status.json").write_text(
            json.dumps(
                {
                    "stage": stage,
                    "pid": os.getpid(),
                    "elapsed": perf_counter() - started,
                    "failure": failure,
                    "visual_quality_verified": False,
                    "source": source_record,
                    "pdf": pdf_record,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def execute(command: list[str], log: str, cwd: Path = ROOT) -> None:
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        (OUT / log).write_text(result.stdout + result.stderr, encoding="utf-8")
        if result.returncode:
            raise RuntimeError(f"exit {result.returncode}; retained {log}")

    try:
        save()
        while True:
            prior = json.loads((ROOT / "results/budget_evidence_export_v1/status.json").read_text("utf-8"))
            live = {row["ProcessId"] for row in process_inventory()}
            if prior["stage"] == "failed" or prior["failure"] is not None:
                raise RuntimeError("Budget-complete manuscript prerequisite failed")
            if prior["stage"] in {"compiled_pending_visual_review", "complete"} and prior["pid"] not in live:
                break
            if prior["pid"] not in live:
                raise RuntimeError("Budget evidence parent ended before manuscript compilation")
            save()
            sleep(30)

        assert all(digest(frozen_root / name) == expected for name, expected in frozen.items())
        source = ROOT / "paper/english_budget_complete_manuscript.md"
        output = ROOT / "paper" / f"{NAME}.md"
        stage = "revising_english_citations"
        save()
        execute(
            [
                str(ROOT / ".venv312/Scripts/python.exe"),
                "-m",
                "src.revise_final_citations",
                "--input",
                source.relative_to(ROOT).as_posix(),
                "--output",
                output.relative_to(ROOT).as_posix(),
            ],
            "revision.log",
        )
        citation = audit_text(output.read_text("utf-8"), "# References")
        assert not citation["undefined_citations"] and not citation["uncited_references"]
        record_path = output.with_suffix(output.suffix + ".source.json")
        record = json.loads(record_path.read_text("utf-8"))
        assert record["source_sha256"] == digest(source) and record["output_sha256"] == digest(output)
        source_record = {
            "path": output.relative_to(ROOT).as_posix(),
            "sha256": digest(output),
            "record": record_path.relative_to(ROOT).as_posix(),
            "record_sha256": digest(record_path),
            "undefined_citations": 0,
            "uncited_references": 0,
        }

        stage = "compiling_citation_revision_pdf"
        save()
        execute(
            [
                "pandoc",
                f"{NAME}.md",
                "--standalone",
                "--template",
                "../configs/english-paper-template.tex",
                "--lua-filter",
                "../configs/keep-math-mechanism.lua",
                "-o",
                f"{NAME}.tex",
            ],
            "pandoc.log",
            ROOT / "paper",
        )
        for number in (1, 2):
            execute(
                [
                    "xelatex",
                    "--disable-installer",
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    "-output-directory=pdf",
                    f"{NAME}.tex",
                ],
                f"xelatex_{number}.log",
                ROOT / "paper",
            )
        tex = ROOT / "paper" / f"{NAME}.tex"
        pdf = ROOT / "paper/pdf" / f"{NAME}.pdf"
        assert tex.is_file() and pdf.is_file() and pdf.stat().st_size > 10000
        pdf_record = {
            "path": pdf.relative_to(ROOT).as_posix(),
            "sha256": digest(pdf),
            "tex": tex.relative_to(ROOT).as_posix(),
            "tex_sha256": digest(tex),
        }
        stage = "compiled_pending_visual_review"
        save()
    except Exception as error:
        failure = {"error_type": type(error).__name__, "error": str(error)}
        stage = "failed"
        save()
        raise


if __name__ == "__main__":
    main()
