"""Resumable eight-slot scheduler for the frozen engineering beam study."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
import subprocess
from pathlib import Path
from queue import Empty, Queue
from threading import Event, Lock
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/engineering_beam_formal.json"


def main():
    cfg = json.loads(CONFIG.read_text("utf-8"))
    out = ROOT / cfg["out"]
    out.mkdir(parents=True, exist_ok=True)
    jobs = [(method, rep) for method in cfg["methods"] for rep in range(cfg["repeats"])]
    gp, other = Queue(), Queue()
    completed = 0
    for method, rep in jobs:
        runid = f"{method}_f01_d{cfg['dimension']}_i1_r{rep}_b{cfg['budget']}"
        summary = out / method / runid / "summary.json"
        if summary.exists():
            completed += 1
        else:
            (gp if method == "gp_ei" else other).put((method, rep))
    expected = len(jobs)
    failures, lock, stop = [], Lock(), Event()
    started = perf_counter()

    def save(stage):
        payload = {"stage": stage, "pid": os.getpid(), "completed": completed,
                   "expected": expected, "failed": len(failures),
                   "remaining_gp_ei": gp.qsize(), "remaining_other": other.qsize(),
                   "elapsed_seconds": perf_counter() - started,
                   "workers": cfg["workers"],
                   "gp_ei_reserved_workers": cfg["gp_ei_reserved_workers"]}
        tmp = out / "status.json.tmp"
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp.replace(out / "status.json")
        (out / "failures.json").write_text(json.dumps(failures, indent=2), encoding="utf-8")

    def execute(job):
        nonlocal completed
        method, rep = job
        python = ROOT / (".venv-baselines/Scripts/python.exe" if method in {"gp_ei", "turbo_1"}
                         else ".venv312/Scripts/python.exe")
        result = subprocess.run([str(python), "-m", "src.engineering_beam_worker",
                                 "--method", method, "--rep", str(rep)], cwd=ROOT,
                                capture_output=True, text=True, encoding="utf-8", errors="replace")
        log = out / f"{method}_r{rep}.log"
        log.write_text(result.stdout + result.stderr, encoding="utf-8")
        if result.returncode:
            raise RuntimeError(f"worker exit {result.returncode}; see {log.name}")
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
        futures += [pool.submit(worker, False) for _ in range(cfg["workers"] - cfg["gp_ei_reserved_workers"])]
        for future in futures:
            future.result()
    save("complete" if completed == expected and not failures else "failed")
    if failures or completed != expected:
        raise RuntimeError("engineering beam batch stopped; inspect retained logs")


if __name__ == "__main__":
    main()
