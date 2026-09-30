"""Finish in-flight work, archive partials, then run dynamic CPU allocation and audit."""
import json, os, shutil, subprocess, time
from pathlib import Path
from time import perf_counter
from .run_solo_cost import process_inventory

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/budget_performance_sensitivity_completion_v3"
ARCH = ROOT / "results/budget_dynamic_switch_20260923_v1"
SOURCE = ROOT / "results/budget_performance_sensitivity_v1"


def save(stage, start, **extra):
    OUT.mkdir(exist_ok=True)
    (OUT / "status.json").write_text(json.dumps({
        "stage": stage, "pid": os.getpid(), "elapsed": perf_counter()-start,
        "failure": None, **extra}, indent=2), encoding="utf-8")


def call(module, log):
    result = subprocess.run([str(ROOT / ".venv312/Scripts/python.exe"), "-m", module],
                            cwd=ROOT, capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    (OUT / log).write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"{module} exited {result.returncode}")


def main():
    assert not OUT.exists() and not ARCH.exists()
    start = perf_counter()
    save("waiting_for_eight_inflight_units", start)
    while any("-m src.budget_sensitivity_worker" in (p["CommandLine"] or "")
              for p in process_inventory()):
        time.sleep(10)
    (ARCH / "partial_runs").mkdir(parents=True)
    partial = []
    for directory in SOURCE.glob("budget_*D/*/*"):
        if directory.is_dir() and not (directory / "summary.json").exists():
            rel = directory.relative_to(SOURCE)
            partial.append(rel.as_posix())
            target = ARCH / "partial_runs" / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(directory), str(target))
    completed = sum(1 for _ in SOURCE.glob("budget_*D/*/*/summary.json"))
    record = {
        "schema": "budget_dynamic_switch_v1",
        "completed_before_dynamic_switch": completed,
        "partial_runs_archived": partial,
        "total_workers": 8,
        "gp_workers_before_other_queue_empty": 2,
        "gp_workers_after_other_queue_empty": 8,
        "scientific_design_changed": False,
        "timing_comparability": "mixed_concurrency_not_for_speed_claims",
    }
    (ARCH / "switch.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    save("formal_dynamic_8x2_then_8gp", start, **record)
    call("src.run_budget_performance_sensitivity_dynamic", "runs.log")
    save("full_raw_audit", start, **record)
    call("src.analyze_budget_performance_sensitivity", "audit.log")
    save("complete", start, runs=2700, **record)


if __name__ == "__main__":
    main()
