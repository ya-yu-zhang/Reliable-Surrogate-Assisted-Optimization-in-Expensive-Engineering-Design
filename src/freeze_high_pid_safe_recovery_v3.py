import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DEST=ROOT/"docs/frozen_high_pid_safe_recovery_v3"
FILES=["src/build_integrated_manuscripts_pid_safe.py","src/high_method_resource_worker_pid_safe.py","src/high_method_resource_driver_pid_safe.py","src/finish_high_extension_pid_safe_v3.py","src/archive_high_method_prerequisite_pid_reuse_failure.py","tests/test_integrated_pid_safe.py","results/high_method_prerequisite_pid_reuse_failure_20260922_v1/archive_manifest.json","results/application_high_precheck_analysis_v1/audit.json"]
def main():
 assert not DEST.exists();DEST.mkdir();rows={}
 for n in FILES:
  s=ROOT/n;t=DEST/n;t.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(s,t);rows[n]=hashlib.sha256(s.read_bytes()).hexdigest()
 (DEST/"sha256.json").write_text(json.dumps(rows,indent=2),encoding="utf-8")
if __name__=="__main__":main()
