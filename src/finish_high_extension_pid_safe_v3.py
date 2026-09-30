"""Resume high extension from the audited six-point resource checkpoint."""
import hashlib,json,os,subprocess
from pathlib import Path
from time import perf_counter
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"results/high_extension_completion_v1"
def verify(path):
 rows=json.loads(path.read_text("utf-8"));assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==v for n,v in rows.items())
def main():
 assert not OUT.exists()
 for n in ("docs/frozen_high_evidence_export_v1/sha256.json","docs/frozen_application_high_formal_v1/sha256.json","docs/frozen_high_pid_safe_recovery_v3/sha256.json"):verify(ROOT/n)
 checkpoint=json.loads((ROOT/"results/application_high_precheck_analysis_v1/audit.json").read_text("utf-8"));assert checkpoint["objective_calls"]==6 and checkpoint["source_hashes_verified"]
 OUT.mkdir();start=perf_counter();stage="eight_full_method_resource_runs";failure=None
 def save():
  def runs(p):return json.loads(p.read_text("utf-8"))["runs"] if p.exists() else 0
  (OUT/"status.json").write_text(json.dumps(dict(stage=stage,pid=os.getpid(),elapsed=perf_counter()-start,failure=failure,resource_point_calls=6,
  full_method_resource_runs=runs(ROOT/"results/application_high_method_resource_analysis_v1/audit.json"),formal_runs=runs(ROOT/"results/application_high_analysis_v1/audit.json")),indent=2),encoding="utf-8")
 def execute(python,module,log):
  r=subprocess.run([str(python),"-m",module],cwd=ROOT,capture_output=True,text=True,encoding="utf-8",errors="replace");(OUT/log).write_text(r.stdout+r.stderr,encoding="utf-8")
  if r.returncode:raise RuntimeError(f"{module} exited {r.returncode}; retained {log}")
 try:
  save();app=ROOT/".venv-app/Scripts/python.exe";core=ROOT/".venv312/Scripts/python.exe"
  execute(app,"src.high_method_resource_driver_pid_safe","method_resource.log")
  stage="full_method_resource_audit";save();execute(core,"src.analyze_application_high_method_resource","method_resource_audit.log")
  stage="formal_160_runs";save();execute(app,"src.run_application_high_formal","formal_runs.log")
  stage="formal_raw_audit";save();execute(core,"src.analyze_application_high_formal","formal_audit.log")
  stage="complete";save()
 except Exception as e:
  failure=dict(error_type=type(e).__name__,error=str(e));stage="failed";save();raise
if __name__=="__main__":main()
