import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DEST=ROOT/"docs/frozen_high_pid_safe_recovery_v2"
FILES=["src/build_integrated_manuscripts_pid_safe.py","src/high_resource_gate_pid_safe.py","src/finish_high_extension_pid_safe_v2.py",
"src/archive_high_precheck_self_overlap_failure.py","tests/test_integrated_pid_safe.py","results/high_precheck_self_overlap_failure_20260922_v1/archive_manifest.json"]
def main():
    assert not DEST.exists();DEST.mkdir();rows={}
    for name in FILES:
        s=ROOT/name;t=DEST/name;t.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(s,t);rows[name]=hashlib.sha256(s.read_bytes()).hexdigest()
    (DEST/"sha256.json").write_text(json.dumps(rows,indent=2),encoding="utf-8")
if __name__=="__main__":main()
