"""Eight-slot resumable scheduler for matched-history GP-PI and GP-UCB."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import platform
import subprocess
from time import perf_counter

from .engineering_beam_shared_init import audit_shared_sources, code_hash, file_sha256

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/engineering_beam_acquisition_refs.json"


def main():
    cfg = json.loads(CONFIG.read_text("utf-8"))
    out = ROOT / cfg["out"]
    out.mkdir(parents=True, exist_ok=True)
    audit = audit_shared_sources(cfg)
    (out / "shared_source_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    hashes = {str(path.relative_to(ROOT)).replace("\\", "/"): file_sha256(path) for path in [
        CONFIG, ROOT / "src/engineering_beam_shared_init.py",
        ROOT / "src/engineering_beam_acquisition_worker.py", Path(__file__),
        ROOT / "src/core.py", ROOT / "src/engineering_beam_adapter.py",
        ROOT / "src/gp_references.py"]}
    hashes.update({f"shared_archive_rep_{row['rep']}": row["archive_sha256"] for row in audit})
    (out / "source_hashes_at_launch.json").write_text(json.dumps(hashes, indent=2), encoding="utf-8")
    environment = {"platform": platform.platform(), "python": platform.python_version(),
                   "logical_processors": os.cpu_count(), "code_hash": code_hash()}
    (out / "environment_at_launch.json").write_text(json.dumps(environment, indent=2), encoding="utf-8")
    jobs = []
    for method in cfg["methods"]:
        for rep in range(cfg["repeats"]):
            runid = f"{method}_f01_d{cfg['dimension']}_i1_r{rep}_b{cfg['budget']}"
            if not (out / method / runid / "summary.json").exists():
                jobs.append((method, rep))
    started = perf_counter()
    state = {"stage": "running", "pid": os.getpid(), "completed": 20 - len(jobs),
             "expected": 20, "failed": [], "remaining": len(jobs), "workers": cfg["workers"]}

    def save():
        state["elapsed_seconds"] = perf_counter() - started
        tmp = out / "status.json.tmp"
        tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
        tmp.replace(out / "status.json")

    def execute(method, rep):
        python = ROOT / ".venv-baselines/Scripts/python.exe"
        result = subprocess.run([str(python), "-m", "src.engineering_beam_acquisition_worker",
                                 "--method", method, "--rep", str(rep)], cwd=ROOT,
                                capture_output=True, text=True, encoding="utf-8", errors="replace")
        (out / f"{method}_r{rep}.log").write_text(result.stdout + result.stderr, encoding="utf-8")
        if result.returncode:
            raise RuntimeError(f"{method} repeat {rep} exited {result.returncode}")
        return method, rep

    save()
    with ThreadPoolExecutor(max_workers=cfg["workers"]) as pool:
        futures = {pool.submit(execute, *job): job for job in jobs}
        for future in as_completed(futures):
            try:
                future.result()
                state["completed"] += 1
            except Exception as error:
                state["failed"].append({"job": futures[future], "error": str(error)})
            state["remaining"] -= 1
            save()
    state["stage"] = "complete" if state["completed"] == state["expected"] and not state["failed"] else "failed"
    save()
    if state["stage"] != "complete":
        raise RuntimeError("one or more acquisition-reference units failed")


if __name__ == "__main__":
    main()
