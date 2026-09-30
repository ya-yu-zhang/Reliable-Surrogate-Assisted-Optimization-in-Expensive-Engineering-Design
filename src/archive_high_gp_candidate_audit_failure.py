import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ARCHIVE=ROOT/"results/high_gp_candidate_audit_failure_20260922_v1"
def main():
    assert not ARCHIVE.exists();completion=ROOT/"results/high_extension_completion_v1";resource=ROOT/"results/application_high_method_resource_v1"
    cs=json.loads((completion/"status.json").read_text("utf-8"));rs=json.loads((resource/"status.json").read_text("utf-8"));gp=json.loads((resource/"gp_ei/summary.json").read_text("utf-8"))
    assert cs["stage"]==rs["stage"]=="failed" and rs["completed"]==6 and rs["failed"]==1
    assert gp["algorithm_evaluations"]==1000 and gp["test_method_calls"]==0 and gp["resource_only"]
    ARCHIVE.mkdir();shutil.move(str(completion),str(ARCHIVE/completion.name))
    for source,name in ((resource/"status.json","resource_status.json"),(resource/"gp_ei.log","gp_ei_console.log"),(ROOT/"results/twentysecond_high_extension_stdout.log","launcher_stdout.log"),(ROOT/"results/twentysecond_high_extension_stderr.log","launcher_stderr.log")):
        assert source.exists();shutil.copy2(source,ARCHIVE/name) if source.parent==resource else shutil.move(str(source),str(ARCHIVE/name))
    evidence=[resource/"gp_ei"/n for n in ("summary.json","events.jsonl","candidate_pools.npz","timing.jsonl")]
    manifest={"schema":"high_gp_candidate_audit_failure_archive_v1","gp_ei_paid_calls_preserved":1000,"test_calls":0,"turbo_calls":0,
              "evidence_sha256":{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in evidence}}
    files=sorted(p for p in ARCHIVE.rglob("*") if p.is_file());manifest["archive_sha256"]={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    (ARCHIVE/"archive_manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
if __name__=="__main__":main()
