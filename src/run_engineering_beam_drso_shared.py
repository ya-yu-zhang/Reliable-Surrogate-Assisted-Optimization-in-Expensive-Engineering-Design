"""Eight-slot resumable scheduler for the author-code DRSO comparison."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import platform
import subprocess
from time import perf_counter

from .engineering_beam_drso_shared import CONFIG, ROOT, adapter_hash, tree_hash
from .engineering_beam_shared_init import audit_shared_sources


def main():
    cfg = json.loads(CONFIG.read_text("utf-8")); out = ROOT / cfg["out"]; out.mkdir(parents=True, exist_ok=True)
    (out / "shared_source_audit.json").write_text(json.dumps(audit_shared_sources(cfg), indent=2), encoding="utf-8")
    launch = {"config": cfg, "platform": platform.platform(), "python": platform.python_version(),
              "logical_processors": os.cpu_count(), "adapter_hash": adapter_hash(),
              "author_tree_hash": tree_hash(ROOT / "literature/source-code/Relation")}
    (out / "launch.json").write_text(json.dumps(launch, indent=2), encoding="utf-8")
    jobs=[]
    for rep in range(cfg["repeats"]):
        runid=f"drso_shared_init_f01_d{cfg['dimension']}_i1_r{rep}_b{cfg['budget']}"
        if not (out / "drso_shared_init" / runid / "summary.json").exists(): jobs.append(rep)
    state={"stage":"running","pid":os.getpid(),"completed":cfg["repeats"]-len(jobs),
           "expected":cfg["repeats"],"remaining":len(jobs),"failed":[],"workers":cfg["workers"]}
    started=perf_counter()
    def save():
        state["elapsed_seconds"]=perf_counter()-started
        tmp=out/"status.json.tmp"; tmp.write_text(json.dumps(state,indent=2),encoding="utf-8"); tmp.replace(out/"status.json")
    def execute(rep):
        python=ROOT/".venv-baselines/Scripts/python.exe"
        proc=subprocess.run([str(python),"-m","src.engineering_beam_drso_shared","--rep",str(rep)],
                            cwd=ROOT,capture_output=True,text=True,encoding="utf-8",errors="replace")
        (out/f"drso_shared_init_r{rep}.log").write_text(proc.stdout+proc.stderr,encoding="utf-8")
        if proc.returncode: raise RuntimeError(f"repeat {rep} exit {proc.returncode}")
    save()
    with ThreadPoolExecutor(max_workers=cfg["workers"]) as pool:
        futures={pool.submit(execute,rep):rep for rep in jobs}
        for future in as_completed(futures):
            try: future.result(); state["completed"]+=1
            except Exception as error: state["failed"].append({"rep":futures[future],"error":str(error)})
            state["remaining"]-=1; save()
    state["stage"]="complete" if state["completed"]==state["expected"] and not state["failed"] else "failed"; save()
    if state["stage"]!="complete": raise RuntimeError("DRSO batch failed")


if __name__ == "__main__": main()
