"""Eight-slot scheduler for matched-initialization external beam references."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import platform
from queue import Empty, Queue
import subprocess
from threading import Event, Lock
from time import perf_counter

from .engineering_beam_shared_init import (CONFIG, ROOT, audit_shared_sources,
                                           code_hash, file_sha256)


def main():
    cfg = json.loads(CONFIG.read_text("utf-8"))
    out = ROOT / cfg["out"]
    out.mkdir(parents=True, exist_ok=True)
    audit = audit_shared_sources(cfg)
    (out / "shared_source_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    frozen_files = [
        CONFIG,
        ROOT / "src/engineering_beam_shared_init.py",
        ROOT / "src/engineering_beam_shared_worker.py",
        Path(__file__),
        ROOT / "src/core.py",
        ROOT / "src/engineering_beam_adapter.py",
        ROOT / "src/gp_references.py",
    ]
    hashes = {str(path.relative_to(ROOT)).replace("\\", "/"): file_sha256(path)
              for path in frozen_files}
    hashes.update({f"shared_archive_rep_{row['rep']}": row["archive_sha256"] for row in audit})
    (out / "source_hashes_at_launch.json").write_text(json.dumps(hashes, indent=2), encoding="utf-8")
    environment = {"platform": platform.platform(), "python": platform.python_version(),
                   "logical_processors": os.cpu_count(), "code_hash": code_hash()}
    (out / "environment_at_launch.json").write_text(json.dumps(environment, indent=2), encoding="utf-8")
    launch = {"config": cfg, "source_hashes_file": "source_hashes_at_launch.json",
              "shared_source_audit_file": "shared_source_audit.json",
              "algorithm_budget_per_run": cfg["budget"],
              "reused_initial_labels_per_run": cfg["shared_initial_evaluations"],
              "new_physical_calls_per_run": cfg["budget"] - cfg["shared_initial_evaluations"]}
    (out / "launch.json").write_text(json.dumps(launch, indent=2), encoding="utf-8")
    jobs = [(method, rep) for method in cfg["methods"] for rep in range(cfg["repeats"])]
    gp, other = Queue(), Queue()
    completed = 0
    for method, rep in jobs:
        runid = f"{method}_f01_d{cfg['dimension']}_i1_r{rep}_b{cfg['budget']}"
        if (out / method / runid / "summary.json").exists():
            completed += 1
        else:
            (gp if method.startswith("gp_ei") else other).put((method, rep))
    failures, lock, stop = [], Lock(), Event()
    started = perf_counter()

    def save(stage):
        payload = {"stage": stage, "pid": os.getpid(), "completed": completed,
                   "expected": len(jobs), "failed": len(failures),
                   "remaining_gp_ei": gp.qsize(), "remaining_other": other.qsize(),
                   "elapsed_seconds": perf_counter() - started,
                   "workers": cfg["workers"],
                   "gp_ei_reserved_workers": cfg["gp_ei_reserved_workers"],
                   "code_hash": code_hash()}
        tmp = out / "status.json.tmp"
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp.replace(out / "status.json")
        (out / "failures.json").write_text(json.dumps(failures, indent=2), encoding="utf-8")

    def execute(job):
        nonlocal completed
        method, rep = job
        python = ROOT / ".venv-baselines/Scripts/python.exe"
        result = subprocess.run([str(python), "-m", "src.engineering_beam_shared_worker",
                                 "--method", method, "--rep", str(rep)], cwd=ROOT,
                                capture_output=True, text=True, encoding="utf-8", errors="replace")
        (out / f"{method}_r{rep}.log").write_text(result.stdout + result.stderr, encoding="utf-8")
        if result.returncode:
            raise RuntimeError(f"worker exit {result.returncode}; see {method}_r{rep}.log")
        with lock:
            completed += 1
            save("running")

    def worker(reserved_gp=False):
        while not stop.is_set():
            source = gp if reserved_gp else other
            try:
                job = source.get_nowait()
            except Empty:
                if reserved_gp:
                    return
                source = gp
                try:
                    job = source.get_nowait()
                except Empty:
                    return
            try:
                execute(job)
            except Exception as error:
                with lock:
                    failures.append({"job": job, "type": type(error).__name__, "error": str(error)})
                    stop.set()
                    save("stopping_after_failure")
            finally:
                source.task_done()

    save("running")
    with ThreadPoolExecutor(max_workers=cfg["workers"]) as pool:
        futures = [pool.submit(worker, True) for _ in range(cfg["gp_ei_reserved_workers"])]
        futures += [pool.submit(worker, False) for _ in
                    range(cfg["workers"] - cfg["gp_ei_reserved_workers"])]
        for future in futures:
            future.result()
    save("complete" if completed == len(jobs) and not failures else "failed")
    if failures or completed != len(jobs):
        raise RuntimeError("matched-initialization beam batch stopped")


if __name__ == "__main__":
    main()
