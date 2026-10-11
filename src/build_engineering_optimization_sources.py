"""Build Interact-CAD review sources from the evidence-preserving Markdown draft.

The official class and bibliography style are installed separately by the pinned
publisher-template fetcher. Markdown reference numbers are stable source IDs;
LaTeX citations are generated in author-date style using those same records.
"""
from __future__ import annotations
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'paper/engineering_optimization'


def pandoc(text, output='latex'):
    return subprocess.run(['pandoc', '--from=markdown+pipe_tables+tex_math_dollars+raw_tex',
                           '--to=' + output, '--wrap=none'], input=text, text=True,
                          encoding='utf-8', capture_output=True, check=True).stdout


def bibliography(text):
    records = []
    for number, line in re.findall(r'^\[(\d+)\] (.+)$', text, re.M):
        authors, title, tail = re.match(r'(.+?), "(.+?)," (.+)', line).groups()
        authorlist = re.split(r', and | and |, ', authors)
        fields = {'author': ' and '.join(authorlist), 'title': '{' + title + '}'}
        fields['author'] = fields['author'].replace('J. E. Dennis Jr.', 'Dennis, Jr., J. E.')
        fields['author'] = fields['author'].replace('J. Zatarain Salazar', 'Zatarain Salazar, J.')
        fields['author'] = fields['author'].replace('et al.', 'and others')
        year = re.search(r'\b(19\d\d|20\d\d)\b', tail)
        fields['year'] = year.group(1)
        doi = re.search(r'doi:\s*(\S+)', tail)
        if doi: fields['doi'] = doi.group(1).rstrip('.')
        url = re.search(r'https://\S+', tail)
        if url: fields['url'] = url.group(0).rstrip('.')
        entrytype = 'article'
        if tail.startswith('in '):
            entrytype = 'inproceedings'
            fields['booktitle'] = tail[3:].split(',')[0]
        elif tail.startswith('arXiv:'):
            entrytype = 'misc'
            fields['howpublished'] = tail.split(',')[0]
            fields['url'] = 'https://arxiv.org/abs/' + tail.split(':',1)[1].split(',')[0]
        else:
            fields['journal'] = tail.split(', vol.')[0].split(', Art.')[0]
        volume = re.search(r'(?:vol\.|LNCS)\s*(\d+)', tail)
        issue = re.search(r', no\.\s*(\d+)', tail)
        pages = re.search(r'pp\.\s*([\d:/-]+)', tail)
        eid = re.search(r'Art\. no\.\s*(\d+)', tail)
        if volume: fields['volume'] = volume.group(1)
        if issue: fields['number'] = issue.group(1)
        if pages: fields['pages'] = pages.group(1).replace('-', '--')
        elif eid: fields['pages'] = eid.group(1)
        if number=='23': fields['booktitle']='Advances in Neural Information Processing Systems'
        records.append('@'+entrytype+'{ref'+number.zfill(2)+',\n'+
                       '\n'.join('  '+k+' = {'+v+'},' for k,v in fields.items())+'\n}\n')
    if len(records) != 38: raise ValueError('Expected 38 bibliography records')
    return '\n'.join(records)


def citations(text):
    def replace(match):
        ids=[]
        for part in match.group(1).split(','):
            if '-' in part:
                lo,hi=map(int,part.split('-')); ids.extend(range(lo,hi+1))
            else: ids.append(int(part))
        return r'\citep{' + ','.join(f'ref{i:02d}' for i in ids) + '}'
    return re.sub(r'\[([1-9]\d*(?:\s*[-,]\s*[1-9]\d*)*)\]',replace,text)


def flatten(value):
    if isinstance(value,dict):
        if value.get('t')=='Str': return value['c']
        if value.get('t') in ('Space','SoftBreak'): return ' '
        if value.get('t')=='Code': return value['c'][1]
        if value.get('t')=='RawInline': return value['c'][1]
        return flatten(value.get('c',[]))
    if isinstance(value,list): return ''.join(flatten(v) for v in value)
    return ''


def normalize(text, supplementary=False):
    # Convert manuscript-level and supplement-level headings to class counters.
    lines=[]
    for line in text.splitlines():
        m=re.match(r'^(#+)\s+(.+)',line)
        if m:
            title=m.group(2)
            numeric=re.match(r'(S?\d+(?:\.\d+)*)\s+(.+)',title)
            if numeric:
                level=numeric.group(1).count('.')+1
                line='#'*level+' '+numeric.group(2)
            else:
                line=r'\section*{'+pandoc(title).strip()+'}'
        lines.append(line)
    ast=json.loads(pandoc(citations('\n'.join(lines)),'json'))
    new=[]; counts={'tables':0,'figures':0}; heading='Supplementary evidence'
    for block in ast['blocks']:
        if block['t']=='Table':
            counts['tables']+=1
            special_label=None
            caption=block['c'][1][1][0]['c'] if block['c'][1][1] else None
            if new and new[-1]['t']=='Para':
                raw=flatten(new[-1]['c'])
                m=re.match(r'(?:Table\s+(S?\d+[a-z]?)\.\s+|Table:\s*)(.*)',raw,re.S)
                if m:
                    prev=new.pop(); caption=prev['c']
                    if len(caption)==1 and caption[0]['t']=='Strong': caption=caption[0]['c']
                    # Strip label text without discarding links/citations in caption.
                    captext=flatten(caption)
                    captext=re.sub(r'^(?:Table\s+S?\d+[a-z]?\.?\s*|Table:\s*)','',captext)
                    caption=json.loads(pandoc(captext,'json'))['blocks'][0]['c']
                    if m.group(1) and m.group(1)[-1].isalpha():
                        special_label=m.group(1)
                        new.append({'t':'RawBlock','c':['latex',r'\begingroup\renewcommand\thetable{'+special_label+'}']})
            if caption is None:
                caption=[{'t':'Str','c':heading+'.'}]
            block['c'][1]=[None,[{'t':'Plain','c':caption}]]
            # Stable full-width columns; avoid unbounded l/r columns on numeric tables.
            specs=block['c'][2]; n=len(specs)
            for spec in specs: spec[1]={'t':'ColWidth','c':1/n}
            new.append({'t':'RawBlock','c':['latex',r'\FloatBarrier\begingroup\fontsize{8.5}{10.5}\selectfont\setlength\tabcolsep{3pt}']})
            new.append(block)
            new.append({'t':'RawBlock','c':['latex',r'\endgroup']})
            if special_label:
                new.append({'t':'RawBlock','c':['latex',r'\addtocounter{table}{-1}\endgroup']})
        else:
            if block['t']=='Header': heading=flatten(block['c'][2])
            new.append(block)
    ast['blocks']=new
    body=subprocess.run(['pandoc','-f','json','-t','latex','--wrap=none'],input=json.dumps(ast),
                        text=True,capture_output=True,check=True).stdout
    body=re.sub(r'(?:Pan|Deshpande|Hanawa) et al\.\s*\\citep\{(ref\d+)\}', lambda m:r'\citet{'+m.group(1)+'}',body)
    if supplementary: body=body.replace(r'\begin{figure}',r'\begin{figure}[H]')
    body=body.replace('∎',r'$\square$').replace(r'\_',r'\_\allowbreak ')
    # Official class handles figure captions. Keep all graphics within the text block.
    body=body.replace('Wins/ties/losses',r'Wins/\allowbreak ties/\allowbreak losses')
    body=body.replace(r'\includegraphics{',r'\includegraphics[width=\linewidth,height=.65\textheight,keepaspectratio]{')
    # Longtable continuation caption must not consume a new table number.
    body=body.replace(r'\caption[]{',r'\caption[]{')
    return body,counts


PREAMBLE=r'''% Built from the evidence-preserving draft using the official publisher class.
% Author review draft: unresolved affiliations and AI-use review remain.
\documentclass[%s]{interact}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\usepackage{natbib}
\bibpunct[, ]{(}{)}{;}{a}{}{,}
\renewcommand\bibfont{\fontsize{10}{11.5}\selectfont}
\setlength\bibsep{0pt}
\usepackage{longtable,array,calc,etoolbox,placeins,float,needspace}
\usepackage[hidelinks,breaklinks]{hyperref}
\urlstyle{same}
\usepackage{microtype}
\providecommand{\tightlist}{\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}
\newcommand{\pandocbounded}[1]{#1}
\setlength\emergencystretch{2em}
\makeatletter
\patchcmd\longtable{\par}{\if@noskipsec\mbox{}\fi\par}{}{}
\def\LT@makecaption#1#2#3{%
  \LT@mcol\LT@cols c{\hbox to\z@{\hss\parbox[t]\LTcapwidth{%
    \tablecaptionfont\noindent{\tablenumfont#2}\hskip7pt#3\par\vskip6pt}\hss}}}
\makeatother
\setlength\LTcapwidth{\textwidth}
\begin{document}
'''


def build():
    if not shutil.which('pandoc'): raise RuntimeError('Pandoc is required.')
    for name in ('interact.cls','tfcad.bst'):
        if not (OUT/name).exists(): raise RuntimeError('Run src/fetch_engineering_optimization_template.py first.')
    main=(ROOT/'paper/engineering_optimization_manuscript.md').read_text()
    title=main.splitlines()[0][2:]
    abstract=main.split('## Abstract\n\n',1)[1].split('\n\n**Keywords:',1)[0]
    keywords=main.split('**Keywords:** ',1)[1].split('\n',1)[0]
    (OUT/'EO_references.bib').write_text(bibliography(main.split('## References',1)[1]))
    manifest={'format':'Official Taylor & Francis Interact-CAD class and bibliography style',
              'journal_specific_instructions_fully_verified':False,'pdf_compiled':False,
              'layout_verified':False,'sources':{},'figures':{},'document_counts':{},
              'abstract_word_count':len(abstract.split())}
    for stem,prefix in [('manuscript','main'),('supplementary','supp')]:
        source=ROOT/f'paper/engineering_optimization_{stem}.md'; text=source.read_text()
        manifest['sources'][source.relative_to(ROOT).as_posix()]=hashlib.sha256(source.read_bytes()).hexdigest()
        figures=[]
        def figure(m):
            if m.group(2).startswith('engineering_optimization/figures/'):
                path=m.group(2).removeprefix('engineering_optimization/').replace('.svg','.png')
            else:
                path=f'figures/{prefix}_figure_{len(figures)+1}.pdf'
                original=ROOT/f'paper/cmc_latex_submission/{path}'
                if not original.exists(): raise FileNotFoundError(original)
                shutil.copyfile(original,OUT/path)
            figures.append(path)
            return f'![{m.group(1)}]({path})'
        text=re.sub(r'!\[([^\]]+)\]\(([^)]+)\)',figure,text)
        if stem=='manuscript': text=text.split('## 1 Introduction',1)[1];text='## 1 Introduction'+text.split('## References',1)[0]
        else: text=text.split('# S0 ',1)[1];text='# S0 '+text
        body,counts=normalize(text,stem=='supplementary')
        front=PREAMBLE.replace('%s', 'suppldata' if stem=='supplementary' else '')
        front+=r'\articletype{'+('Supplementary material' if stem=='supplementary' else 'Research article')+'}\n'
        front+=r'\title{'+('Supplementary material: ' if stem=='supplementary' else '')+title+'}\n'
        front+=r'''\author{\name{Shu-Chuan Chu\textsuperscript{a,*}, Ya-Yu Zhang\textsuperscript{a}, Zhenyu Meng\textsuperscript{b} and Jia Zhao\textsuperscript{c}}
\affil{\textsuperscript{a}School of Computer Science, Nanjing University of Information Science and Technology, Nanjing 210044, Jiangsu, China; \textsuperscript{b}Affiliation to be confirmed; \textsuperscript{c}Affiliation to be confirmed}
\thanks{CONTACT Shu-Chuan Chu. Email: \href{mailto:100130@nuist.edu.cn}{100130@nuist.edu.cn}}
}
\maketitle
'''
        if stem=='manuscript':
            front+='\\begin{abstract}\n'+pandoc(abstract).strip()+'\n\\end{abstract}\n\\begin{keywords}\n'+keywords+'\n\\end{keywords}\n'
        else:
            front+=r'\setcounter{section}{-1}\renewcommand\thesection{S\arabic{section}}\renewcommand\thetable{S\arabic{table}}\renewcommand\thefigure{S\arabic{figure}}'+'\n'
        front+=r'\noindent{\small\textit{Author review draft. Affiliations b and c and final author approval are pending.}}'+'\n\n'
        end='\n'
        if stem=='supplementary': end+=r'\Needspace{14\baselineskip}'+'\n'
        end+=r'\bibliographystyle{tfcad}\bibliography{EO_references}'+'\n'
        end+=r'\end{document}'+'\n'
        target=OUT/f'EO_{stem}.tex';target.write_text(front+body+end)
        counts['figures']=len(figures);manifest['document_counts'][stem]=counts
        manifest['figures'][stem]=figures
        manifest['sources'][target.relative_to(ROOT).as_posix()]=hashlib.sha256(target.read_bytes()).hexdigest()
    (OUT/'source_build_status.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest

if __name__=='__main__': print(json.dumps(build(),indent=2))
