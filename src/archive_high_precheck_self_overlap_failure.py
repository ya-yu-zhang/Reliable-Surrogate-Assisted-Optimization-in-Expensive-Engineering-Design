import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; SOURCE=ROOT/"results/high_extension_completion_v1"; ARCHIVE=ROOT/"results/high_precheck_self_overlap_failure_20260922_v1"
def main():
    assert not ARCHIVE.exists();status=json.loads((SOURCE/"status.json").read_text("utf-8"))
    assert status["stage"]=="failed" and status["resource_point_calls"]==0 and not (ROOT/"results/application_high_precheck_v1").exists()
    ARCHIVE.mkdir();shutil.move(str(SOURCE),str(ARCHIVE/SOURCE.name))
    for name in ("twentieth_high_extension_stdout.log","twentieth_high_extension_stderr.log"):
        path=ROOT/"results"/name;assert path.exists();shutil.move(str(path),str(ARCHIVE/name))
    files=sorted(p for p in ARCHIVE.rglob("*") if p.is_file());manifest={"schema":"high_precheck_self_overlap_failure_archive_v1","objective_calls":0,
        "files":{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
    (ARCHIVE/"archive_manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
if __name__=="__main__":main()
