"""Freeze CMA state-roundoff recovery before any suffix objective call."""
from __future__ import annotations
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/frozen_application_cma_state_roundoff_protocol_v2'
FILES=['docs/应用CMA状态浮点边界修正协议20260922.md','src/recover_interrupted_application_run_v3.py','src/audit_application_recovery_v4.py','src/archive_application_cma_state_roundoff_failure.py','src/resume_application_after_cma_state_roundoff_v6.py','src/freeze_application_cma_state_roundoff_protocol.py','tests/test_application_cma_state_numeric_replay.py','src/application_methods.py','src/application_experiment.py','configs/application_formal.json','results/application_cma_state_roundoff_failure_v2/archive_manifest.json','docs/frozen_application_cma_roundoff_protocol_v1/sha256.json']
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not OUT.exists();m={n:digest(ROOT/n) for n in FILES}
    for n in FILES:q=OUT/n;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/n,q)
    (OUT/'sha256.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8');assert all(digest(OUT/n)==v for n,v in m.items());print(json.dumps({'files':len(m),'manifest':digest(OUT/'sha256.json')},indent=2))
if __name__=='__main__':main()
