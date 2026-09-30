"""Recover evidence export after a documented PID-reuse false positive."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
from time import perf_counter


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/evidence_export_v1"


def verify_manifest(path):
    rows = json.loads(path.read_text("utf-8"))
    assert all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
               for name, digest in rows.items())


def main():
    OUT.mkdir(parents=True, exist_ok=True); status_path = OUT / "status.json"
    if status_path.exists():
        raise RuntimeError("Export record already exists; refuse duplicate or automatic restart")
    verify_manifest(ROOT / "docs/frozen_evidence_export_v1/sha256.json")
    verify_manifest(ROOT / "docs/frozen_post_application_pid_safe_recovery_v1/sha256.json")
    start = perf_counter(); stage = "full_evidence_integration"; failure = None
    own_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

    def save():
        status_path.write_text(json.dumps({
            "stage": stage, "pid": os.getpid(), "pipeline_sha256": own_hash,
            "elapsed": perf_counter() - start, "failure": failure,
            "visual_quality_verified": False,
        }, indent=2), encoding="utf-8")

    def execute(command, log, workdir=ROOT):
        result = subprocess.run(command, cwd=workdir, capture_output=True, text=True,
                                encoding="utf-8", errors="replace")
        (OUT / log).write_text(result.stdout + result.stderr, encoding="utf-8")
        if result.returncode:
            raise RuntimeError(f"Exit {result.returncode}; preserved {log}")

    try:
        save()
        execute([str(ROOT / ".venv312/Scripts/python.exe"), "-m",
                 "src.build_integrated_manuscripts_pid_safe"], "integrated_manuscripts.log")
        stage = "compiling_reading_pdfs"; save()
        for name, template in (("english_integrated_manuscript", "english-paper-template.tex"),
                               ("论文综合机制稿", "paper-template.tex")):
            execute(["pandoc", name + ".md", "--standalone", "--template", "../configs/" + template,
                     "--lua-filter", "../configs/keep-math-mechanism.lua", "-o", name + ".tex"],
                    name + "_pandoc.log", ROOT / "paper")
            for pass_number in (1, 2):
                execute(["xelatex", "--disable-installer", "-interaction=nonstopmode", "-halt-on-error",
                         "-output-directory=pdf", name + ".tex"],
                        f"{name}_xelatex_{pass_number}.log", ROOT / "paper")
            pdf = ROOT / "paper/pdf" / (name + ".pdf")
            assert pdf.exists() and pdf.stat().st_size > 10000
        stage = "compiled_pending_visual_review"; save()
    except Exception as error:
        stage = "failed"; failure = {"error": str(error)}; save(); raise


if __name__ == "__main__":
    main()
