"""Package compiled review sources and locally installed publisher dependencies."""
from __future__ import annotations
import hashlib
import json
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'paper/engineering_optimization'


def package():
    build=json.loads((OUT/'pdf_build_status.json').read_text())
    if not build.get('pdf_compiled') or not build.get('layout_verified'):
        raise ValueError('Compile and review the current PDFs before packaging.')
    for stem,record in build['documents'].items():
        if hashlib.sha256((OUT/f'EO_{stem}.pdf').read_bytes()).hexdigest()!=record['sha256']:
            raise ValueError('PDF differs from the reviewed version')
    for name,digest in build['source_hashes'].items():
        if hashlib.sha256((OUT/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('Source differs from the reviewed build')
    assets=['EO_manuscript.tex','EO_supplementary.tex','EO_references.bib',
            'EO_manuscript.bbl','EO_supplementary.bbl','EO_manuscript.pdf','EO_supplementary.pdf',
            'interact.cls','tfcad.bst','template_provenance.json','FORMAT_REVIEW.md',
            'pdf_build_status.json','revision_audit.json','bibliography_verification.json']
    status=json.loads((OUT/'source_build_status.json').read_text())
    assets+=sorted(set(p for values in status['figures'].values() for p in values))
    readme='''ENGINEERING OPTIMIZATION AUTHOR-REVIEW PACKAGE

This package is an author-review draft. Affiliations b/c, substantive author review
of AI-assisted added arguments, accurate disclosure and final author approvals
are still pending. See FORMAT_REVIEW.md before preparing a submission.

The publisher Interact-CAD class and BibTeX style are unmodified official assets
included for this author workflow. No redistribution license is asserted.
Current journal-specific instructions/word limits still need portal confirmation.

Compile in this directory with a normal TeX Live installation:
  pdflatex EO_manuscript.tex
  bibtex EO_manuscript
  pdflatex EO_manuscript.tex
  pdflatex EO_manuscript.tex
  pdflatex EO_supplementary.tex
  bibtex EO_supplementary
  pdflatex EO_supplementary.tex
  pdflatex EO_supplementary.tex

The sources, shared .bib, both .bbl files and all 20 figure assets are included.
Do not substitute a detector score for authorship or publisher-policy review.
'''
    dest=OUT/'EO_author_review_package.zip'
    with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name in assets:z.write(OUT/name,name)
        for stem in ('manuscript','supplementary'):
            z.write(ROOT/f'paper/engineering_optimization_{stem}.md',f'drafts/{stem}.md')
        z.writestr('README.txt',readme)
    return {'path':str(dest),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'files':len(assets)+3}

if __name__=='__main__':print(json.dumps(package(),indent=2))
