import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT/"results/high_extension_completion_v1";ARCHIVE=ROOT/"results/high_method_prerequisite_pid_reuse_failure_20260922_v1"
def main():
    assert not ARCHIVE.exists();s=json.loads((SOURCE/"status.json").read_text("utf-8"));a=json.loads((ROOT/"results/application_high_precheck_analysis_v1/audit.json").read_text("utf-8"))
    assert s["stage"]=="failed" and s["resource_point_calls"]==6 and s["full_method_resource_runs"]==0
    assert a["objective_calls"]==6 and a["test_method_calls"]==0 and a["source_hashes_verified"]
    assert not (ROOT/"results/application_high_method_resource_v1").exists()
    ARCHIVE.mkdir();shutil.move(str(SOURCE),str(ARCHIVE/SOURCE.name))
    for name in ("twentyfirst_high_extension_stdout.log","twentyfirst_high_extension_stderr.log"):
        p=ROOT/"results"/name;assert p.exists();shutil.move(str(p),str(ARCHIVE/name))
    files=sorted(p for p in ARCHIVE.rglob("*") if p.is_file());m={"schema":"high_method_prerequisite_pid_reuse_failure_archive_v1","preserved_resource_calls":6,"new_method_resource_runs":0,
    "files":{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
    (ARCHIVE/"archive_manifest.json").write_text(json.dumps(m,indent=2),encoding="utf-8")
if __name__=="__main__":main()
