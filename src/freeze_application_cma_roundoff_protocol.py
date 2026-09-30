"""Freeze bounded CMA replay protocol before any CMA suffix objective call."""
from __future__ import annotations
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/frozen_application_cma_roundoff_protocol_v1'
FILES=['docs/应用CMA回放浮点边界修正协议20260922.md','src/recover_interrupted_application_run_v2.py',
       'src/audit_application_recovery_v3.py','src/archive_application_cma_strict_replay_failure.py',
       'src/resume_application_after_cma_roundoff_v5.py','src/freeze_application_cma_roundoff_protocol.py',
       'tests/test_application_cma_numeric_replay.py','src/application_methods.py','src/application_experiment.py',
       'configs/application_formal.json','results/application_cma_strict_replay_failure_v1/archive_manifest.json',
       'docs/frozen_application_second_interruption_protocol_v1/sha256.json']
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not OUT.exists();m={n:digest(ROOT/n) for n in FILES}
    for n in FILES:
        q=OUT/n;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/n,q)
    (OUT/'sha256.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
    assert all(digest(OUT/n)==v for n,v in m.items());print(json.dumps({'files':len(m),'manifest':digest(OUT/'sha256.json')},indent=2))
if __name__=='__main__':main()
