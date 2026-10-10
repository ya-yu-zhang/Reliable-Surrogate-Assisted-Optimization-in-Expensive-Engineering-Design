"""Build journal-neutral LaTeX working sources; no publisher template is claimed."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper/engineering_optimization"


def build() -> dict:
    pandoc = shutil.which("pandoc")
    if not pandoc:
        raise RuntimeError("Install Pandoc to generate the LaTeX working sources.")
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {"format": "journal-neutral article; not the official publisher template",
                "pdf_compiled": False, "layout_verified": False, "sources": {}, "figures": {}}
    for stem, prefix in [("manuscript", "main"), ("supplementary", "supp")]:
        source = ROOT / f"paper/engineering_optimization_{stem}.md"
        text = source.read_text(encoding="utf-8")
        manifest["sources"][source.relative_to(ROOT).as_posix()] = hashlib.sha256(source.read_bytes()).hexdigest()
        figures = []

        def figure(match):
            number = len(figures) + 1
            # Reuse the already committed vector figures in the previous package.
            # The figure data have not changed; Figure 3/S3 prose is corrected.
            path = f"../cmc_latex_submission/figures/{prefix}_figure_{number}.pdf"
            figures.append(path)
            return f"![{match.group(1)}]({path})"

        text = re.sub(r"!\[([^\]]+)\]\(([^)]+)\)", figure, text)
        result = subprocess.run([pandoc, "--from=markdown+pipe_tables+tex_math_dollars",
                                 "--to=latex", "--standalone", "--wrap=none",
                                 "--top-level-division=section", "--variable=documentclass:article",
                                 "--variable=geometry:margin=25mm"],
                                input=text, text=True, encoding="utf-8", capture_output=True, check=True)
        target = OUT / f"EO_{stem}.tex"
        target.write_text("% Working revision: journal-neutral source; PDF not rebuilt or visually verified.\n"
                          + result.stdout, encoding="utf-8")
        manifest["figures"][stem] = figures
        manifest["sources"][target.relative_to(ROOT).as_posix()] = hashlib.sha256(target.read_bytes()).hexdigest()
    (OUT / "source_build_status.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
