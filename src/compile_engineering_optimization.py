"""Compile both review PDFs with BibTeX and record unresolved layout warnings.

Normal TeX Live installations need no special environment. When a container has
TeX trees but lacks its search database/formats, use --repair-runtime PATH to
build only local format/font-map files, without changing the system install.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import subprocess
from pypdf import PdfReader
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'paper/engineering_optimization'


def environment(runtime=None):
    env=os.environ.copy()
    if runtime:
        runtime=runtime.resolve();runtime.mkdir(parents=True,exist_ok=True)
        trees=['/usr/share/texlive/texmf-dist','/usr/share/texmf']
        env.update(TEXINPUTS='.:'+':'.join(t+'/tex//' for t in trees)+':',
                   TFMFONTS=':'.join(t+'/fonts/tfm//' for t in trees)+':',
                   TEXFORMATS=str(runtime)+':', TEXFONTMAPS=str(runtime)+':'+':'.join(t+'/fonts/map//' for t in trees)+':',
                   T1FONTS=':'.join(t+'/fonts/type1//' for t in trees)+':',
                   ENCFONTS=':'.join(t+'/fonts/enc//' for t in trees)+':',
                   BSTINPUTS='.:', BIBINPUTS='.:')
        if not (runtime/'pdflatex.fmt').exists():
            subprocess.run(['pdftex','-ini','-etex','-interaction=nonstopmode',
                            '-jobname=pdflatex','-progname=pdflatex','pdflatex.ini'],
                           cwd=runtime,env=env,check=True,capture_output=True)
        maps=[Path('/usr/share/texmf/fonts/map/dvips/lm/lm.map')]
        maps+=list(Path('/usr/share/texlive/texmf-dist/fonts/map/dvips/amsfonts').glob('*.map'))
        (runtime/'pdftex.map').write_bytes(b'\n'.join(p.read_bytes() for p in maps))
    return env


def compile_documents(runtime=None):
    env=environment(runtime); report={'documents':{},'pdf_compiled':False,'layout_verified':False}
    for stem in ['manuscript','supplementary']:
        name='EO_'+stem
        commands=[['pdflatex','-interaction=nonstopmode','-halt-on-error',name+'.tex']]
        commands.append(['bibtex',name])
        commands.extend([commands[0]]*3)
        for i,cmd in enumerate(commands):
            p=subprocess.run(cmd,cwd=OUT,env=env,capture_output=True,text=True)
            (OUT/(name+f'_pass_{i+1}.txt')).write_text(p.stdout+p.stderr)
            if p.returncode:
                raise RuntimeError(f'{cmd[0]} failed for {name}: '+(p.stdout+p.stderr)[-1800:])
        log=(OUT/(name+'.log')).read_text(errors='replace')
        warnings=re.findall(r'Overfull \\[hv]box.*',log)
        unresolved=bool(re.search(r'Citation.*undefined|There were undefined|undefined references',log))
        if unresolved: raise RuntimeError('Unresolved citations/references in '+name)
        report['documents'][stem]={'sha256':hashlib.sha256((OUT/(name+'.pdf')).read_bytes()).hexdigest(),
            'pages':len(PdfReader(OUT/(name+'.pdf')).pages),
            'overfull_warnings':warnings, 'unresolved_citations_or_references':unresolved}
    report['source_hashes']={name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in ['EO_manuscript.tex','EO_supplementary.tex','EO_references.bib']}
    report['pdf_compiled']=True
    (OUT/'pdf_build_status.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repair-runtime',type=Path)
    print(json.dumps(compile_documents(p.parse_args().repair_runtime),indent=2))
