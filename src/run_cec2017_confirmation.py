"""Eight-slot resumable CEC2017 scheduler with two GP-EI reservations."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
import random
import subprocess
from pathlib import Path
from queue import Empty, Queue
from threading import Event, Lock
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/cec2017_confirmation.json"


def main():
    config = json.loads(CONFIG.read_text("utf-8"))
    out = ROOT / config["out"]
    out.mkdir(parents=True, exist_ok=True)
    jobs = [(m, f, d, r) for m in config["methods"] for f in config["functions"]
            for d in config["dimensions"] for r in range(config["repeats"])]
    expected = len(jobs)
    assert expected == 10440
    random.Random(config["order_seed"]).shuffle(jobs)
    gp_queue, other_queue = Queue(), Queue()
    completed = 0
    for method, fid, dim, rep in jobs:
        budget = config["budget_multiplier"] * dim
        runid = f"{method}_f{fid:02}_d{dim}_i1_r{rep}_b{budget}"
        summary = out / method / runid / "summary.json"
        if summary.exists():
            completed += 1
        else:
            (gp_queue if method == "gp_ei" else other_queue).put((method, fid, dim, rep))

    lock, stop = Lock(), Event()
    failures = []
    start = perf_counter()
    python_default = ROOT / ".venv312/Scripts/python.exe"
    python_gp = ROOT / ".venv-baselines/Scripts/python.exe"

    def save(stage):
        payload = {"stage": stage, "pid": os.getpid(), "completed": completed,
                   "expected": expected, "failed": len(failures),
                   "elapsed_seconds": perf_counter() - start,
                   "remaining_gp_ei": gp_queue.qsize(),
                   "remaining_other": other_queue.qsize(),
                   "workers": config["workers"],
                   "gp_ei_reserved_workers": config["gp_ei_reserved_workers"]}
        temporary = out / "status.json.tmp"
        temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        temporary.replace(out / "status.json")
        (out / "failures.json").write_text(json.dumps(failures, indent=2), encoding="utf-8")

    def execute(job):
        nonlocal completed
        method, fid, dim, rep = job
        python = python_gp if method in {"gp_ei", "turbo_1"} else python_default
        result = subprocess.run([str(python), "-m", "src.cec2017_worker",
                                 "--method", method, "--fid", str(fid),
                                 "--dim", str(dim), "--rep", str(rep)],
                                cwd=ROOT, capture_output=True, text=True,
                                encoding="utf-8", errors="replace")
        log = out / f"{method}_f{fid:02}_d{dim}_r{rep}.log"
        log.write_text(result.stdout + result.stderr, encoding="utf-8")
        if result.returncode:
            raise RuntimeError(f"worker exit {result.returncode}; see {log.name}")
        with lock:
            completed += 1
            save("running")

    def worker(reserved_gp=False):
        while not stop.is_set():
            source = gp_queue if reserved_gp else other_queue
            try:
                job = source.get_nowait()
            except Empty:
                if reserved_gp:
                    return
                source = gp_queue
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
    with ThreadPoolExecutor(max_workers=config["workers"]) as pool:
        futures = [pool.submit(worker, True) for _ in range(config["gp_ei_reserved_workers"])]
        futures += [pool.submit(worker, False) for _ in range(config["workers"] - config["gp_ei_reserved_workers"])]
        for future in futures:
            future.result()
    save("complete" if completed == expected and not failures else "failed")
    if failures or completed != expected:
        raise RuntimeError("CEC2017 batch stopped; inspect retained logs")


if __name__ == "__main__":
    main()
