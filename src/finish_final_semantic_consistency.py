"""Apply the frozen semantic correction and recompile the two final working PDFs."""

import hashlib, json, os, subprocess
from pathlib import Path
from time import perf_counter

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"results/final_semantic_consistency_v1"
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 assert not OUT.exists();status=json.loads((ROOT/"results/budget_evidence_export_v1/status.json").read_text("utf-8"));assert status["stage"]=="compiled_pending_visual_review" and status["failure"] is None
 frozen=json.loads((ROOT/"docs/frozen_final_semantic_consistency_v1/sha256.json").read_text("utf-8"));assert all(digest(ROOT/n)==v for n,v in frozen.items())
 OUT.mkdir();start=perf_counter();stage="revising_semantic_consistency";failure=None
 def save():(OUT/"status.json").write_text(json.dumps(dict(stage=stage,pid=os.getpid(),elapsed=perf_counter()-start,failure=failure,visual_quality_verified=False),indent=2),encoding="utf-8")
 def execute(command,log,cwd=ROOT):
  r=subprocess.run(command,cwd=cwd,capture_output=True,text=True,encoding="utf-8",errors="replace");(OUT/log).write_text(r.stdout+r.stderr,encoding="utf-8")
  if r.returncode:raise RuntimeError(f"exit {r.returncode}; retained {log}")
 try:
  save();execute([str(ROOT/".venv312/Scripts/python.exe"),"-m","src.revise_final_semantic_consistency"],"revision.log")
  stage="recompiling_final_working_pdfs";save()
  for name,template in (("english_budget_complete_manuscript","english-paper-template.tex"),("论文预算完整机制稿","paper-template.tex")):
   execute(["pandoc",name+".md","--standalone","--template","../configs/"+template,"--lua-filter","../configs/keep-math-mechanism.lua","-o",name+".tex"],name+"_pandoc.log",ROOT/"paper")
   for i in (1,2):execute(["xelatex","--disable-installer","-interaction=nonstopmode","-halt-on-error","-output-directory=pdf",name+".tex"],name+f"_xelatex_{i}.log",ROOT/"paper")
  stage="compiled_pending_visual_review";save()
 except Exception as e:
  failure=dict(error_type=type(e).__name__,error=str(e));stage="failed";save();raise
if __name__=="__main__":main()
