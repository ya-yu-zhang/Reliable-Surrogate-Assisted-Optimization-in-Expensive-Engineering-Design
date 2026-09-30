"""Remove stale phase text and compile the audited high-extension papers safely."""
from __future__ import annotations
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/high_evidence_export_safe_v1'
PAIRS=[('english_high_extension_manuscript','english-paper-template.tex'),('论文高维扩展机制稿','paper-template.tex')]
REPLACEMENTS={
 'english_high_extension_manuscript.md':[
  ('Reliable competitive SAEA reproduction and the predefined high-dimensional extension remain unfinished.',
   'The predefined 300-dimensional extension is reported in Section 11; reliable competitive SAEA reproduction remains unfinished.'),
  ('The 300-dimensional synt_high extension requires 620 internal initialization evaluations, so it cannot use the original 500 budget unchanged; its separate resource/budget protocol remains unfinished.',
   'The 300-dimensional synt_high extension therefore uses its separately frozen 1,000-evaluation protocol, reported in Section 11.'),
  ('reliable competitive SAEA and the high-dimensional extension remain gaps. Formal external comparisons cannot be inferred from partial live batches.',
   'the predefined high-dimensional extension is reported in Section 11, while reliable competitive SAEA reproduction remains a gap.')],
 '论文高维扩展机制稿.md':[
  ('可靠关键SAEA复现与预定300维扩展仍待补齐。','预定300维扩展见第11节；可靠关键SAEA复现仍待补齐。'),
  ('300维synt_high启动需要620次，无法直接使用原500预算；独立扩展资源与预算仍未完成。','300维synt_high因此采用独立冻结的1,000次评价协议，结果见第11节。')]
}
def run(args,log,cwd=ROOT):
 r=subprocess.run(args,cwd=cwd,capture_output=True,text=True,encoding='utf-8',errors='replace');(OUT/log).write_text(r.stdout+r.stderr,encoding='utf-8');assert r.returncode==0,(log,r.returncode)
def main():
 assert not OUT.exists();OUT.mkdir(parents=True)
 audit=json.loads((ROOT/'results/application_high_analysis_v1/audit.json').read_text('utf-8'));assert audit['complete_design'] and audit['runs']==160
 record_path=ROOT/'paper/high_extension_manuscripts_source_hashes.json';record=json.loads(record_path.read_text('utf-8'))
 changes=[]
 for name,_ in PAIRS:
  path=ROOT/'paper'/(name+'.md');text=path.read_text('utf-8');before=hashlib.sha256(path.read_bytes()).hexdigest()
  for old,new in REPLACEMENTS[path.name]:
   if old in text: assert text.count(old)==1,(path.name,old);text=text.replace(old,new,1)
   else: assert text.count(new)==1,(path.name,new)
  path.write_text(text,encoding='utf-8');after=hashlib.sha256(path.read_bytes()).hexdigest();record[path.relative_to(ROOT).as_posix()]=after
  changes.append(dict(path=path.relative_to(ROOT).as_posix(),before_sha256=before,after_sha256=after,scientific_results_changed=False))
 record_path.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
 for name,template in PAIRS:
  run(['pandoc',name+'.md','--standalone','--template','../configs/'+template,'--lua-filter','../configs/keep-math-mechanism.lua','-o',name+'.tex'],name+'_pandoc.log',ROOT/'paper')
  tex=ROOT/'paper'/(name+'.tex');body=tex.read_text('utf-8')
  needle='\\usepackage{longtable,booktabs,array,hyperref}' if 'longtable,booktabs,array,hyperref' in body else '\\usepackage{longtable,booktabs,array}'
  assert body.count(needle)==1;body=body.replace(needle,needle+'\n\\usepackage{calc}',1);tex.write_text(body,encoding='utf-8')
  for i in (1,2):run(['xelatex','--disable-installer','-interaction=nonstopmode','-halt-on-error','-output-directory=pdf',name+'.tex'],name+f'_xelatex_{i}.log',ROOT/'paper')
  assert (ROOT/'paper/pdf'/(name+'.pdf')).stat().st_size>10000
 result={'stage':'compiled_pending_visual_review','papers':2,'semantic_changes':changes,'scientific_results_changed':False,'failure':None,'visual_quality_verified':False}
 (OUT/'status.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
