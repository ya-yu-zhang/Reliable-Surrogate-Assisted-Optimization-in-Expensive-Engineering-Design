"""Eight-worker scheduler: two GP-EI reservations, then work stealing into GP-EI."""
from concurrent.futures import ThreadPoolExecutor
import hashlib, json, os, random, subprocess
from pathlib import Path
from queue import Empty, Queue
from threading import Event, Lock
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
CONFIG = "configs/budget_performance_sensitivity.json"


def main():
    config = json.loads((ROOT / CONFIG).read_text("utf-8"))
    frozen = json.loads((ROOT / config["freeze_manifest"]).read_text("utf-8"))
    assert all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
               for name, digest in frozen.items())
    out = ROOT / config["out"]
    out.mkdir(parents=True, exist_ok=True)

    amendment = {
        "schema": "budget_sensitivity_dynamic_concurrency_v1",
        "total_worker_limit": 8,
        "gp_ei_reserved_workers_while_other_queue_nonempty": 2,
        "gp_ei_worker_limit_after_other_queue_empty": 8,
        "scientific_design_changed": False,
        "timing_comparability": "mixed_concurrency_not_for_speed_claims",
    }
    (out / "operational_amendment_dynamic.json").write_text(
        json.dumps(amendment, indent=2), encoding="utf-8")

    all_jobs = [(m, f, d, i, r, b)
                for m in config["methods"] for f in config["functions"]
                for d in config["dimensions"] for i in config["instances"]
                for r in range(3) for b in config["budget_multipliers"]]
    assert len(all_jobs) == 2700
    random.Random(config["order_seed"]).shuffle(all_jobs)
    gp_queue, other_queue = Queue(), Queue()
    completed = 0
    for job in all_jobs:
        method, fid, dim, instance, rep, multiplier = job
        runid = f"{method}_f{fid:02}_d{dim}_i{instance}_r{rep}_b{multiplier * dim}"
        summary = out / f"budget_{multiplier}D" / method / runid / "summary.json"
        if summary.exists():
            completed += 1
        else:
            (gp_queue if method == "gp_ei" else other_queue).put(job)

    stop, lock = Event(), Lock()
    failures = []
    start = perf_counter()
    initial_completed = completed

    def save(stage):
        payload = dict(stage=stage, pid=os.getpid(), completed=completed,
                       expected=2700, failed=len(failures), elapsed=perf_counter()-start,
                       initial_completed=initial_completed, **amendment)
        (out / "status.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        (out / "failures.json").write_text(json.dumps(failures, indent=2), encoding="utf-8")

    def execute(job):
        nonlocal completed
        method, fid, dim, instance, rep, multiplier = job
        runid = f"{method}_f{fid:02}_d{dim}_i{instance}_r{rep}_b{multiplier * dim}"
        directory = out / f"budget_{multiplier}D" / method / runid
        if directory.exists() and not (directory / "summary.json").exists():
            raise RuntimeError("Incomplete directory retained")
        python = ROOT / (".venv-baselines/Scripts/python.exe"
                         if method in ["gp_ei", "turbo_1"] else ".venv312/Scripts/python.exe")
        result = subprocess.run(
            [str(python), "-m", "src.budget_sensitivity_worker", "--method", method,
             "--fid", str(fid), "--dim", str(dim), "--instance", str(instance),
             "--rep", str(rep), "--multiplier", str(multiplier)],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        log = out / f"{multiplier}D_{runid}.dynamic.log"
        if log.exists():
            log = out / f"{multiplier}D_{runid}.dynamic-{os.getpid()}.log"
        log.write_text(result.stdout + result.stderr, encoding="utf-8")
        if result.returncode:
            raise RuntimeError(f"exit {result.returncode}; retained {log.name}")
        summary = json.loads((directory / "summary.json").read_text("utf-8"))
        assert summary["algorithm_evaluations"] == multiplier * dim
        with lock:
            completed += 1
            save("running_dynamic_8x2_then_8gp")

    def worker(gp_reserved=False):
        while not stop.is_set():
            source = gp_queue
            if not gp_reserved:
                try:
                    job = other_queue.get_nowait()
                    source = other_queue
                except Empty:
                    source = gp_queue
                    try:
                        job = gp_queue.get_nowait()
                    except Empty:
                        return
            else:
                try:
                    job = gp_queue.get_nowait()
                except Empty:
                    return
            try:
                execute(job)
            except Exception as error:
                with lock:
                    failures.append(dict(job=job, error_type=type(error).__name__, error=str(error)))
                    stop.set()
                    save("stopping_after_failure")
            finally:
                source.task_done()

    save("running_dynamic_8x2_then_8gp")
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(worker, True) for _ in range(2)]
        futures += [pool.submit(worker, False) for _ in range(6)]
        for future in futures:
            future.result()
    save("complete" if completed == 2700 and not failures else "failed")
    if failures or completed != 2700:
        raise RuntimeError("Budget sensitivity stopped; no automatic rerun")


if __name__ == "__main__":
    main()
