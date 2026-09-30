import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DEST=ROOT/"docs/frozen_high_candidate_audit_recovery_v1"
FILES=["src/application_high_journal_audit_safe.py","src/high_method_resource_driver_safe_v2.py","src/analyze_application_high_method_resource_safe.py","src/analyze_application_high_formal_safe.py","src/finish_high_extension_pid_safe_v4.py","src/archive_high_gp_candidate_audit_failure.py","tests/test_high_candidate_audit_safe.py","results/high_gp_candidate_audit_failure_20260922_v1/archive_manifest.json"]
def main():
 assert not DEST.exists();DEST.mkdir();rows={}
 for n in FILES:
  s=ROOT/n;t=DEST/n;t.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(s,t);rows[n]=hashlib.sha256(s.read_bytes()).hexdigest()
 (DEST/"sha256.json").write_text(json.dumps(rows,indent=2),encoding="utf-8")
if __name__=="__main__":main()
