"""Archive interrupted units, resume dynamic 8-slot batch, then run the full audit."""
import json, os, shutil, subprocess
from pathlib import Path
from time import perf_counter
from .run_solo_cost import process_inventory

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "results/budget_performance_sensitivity_v1"
OUT = ROOT / "results/budget_performance_sensitivity_completion_v4"
ARCH = ROOT / "results/budget_interruption_20260924_v1"


def save(stage, start, **extra):
    OUT.mkdir(exist_ok=True)
    (OUT / "status.json").write_text(json.dumps({
        "stage": stage, "pid": os.getpid(), "elapsed": perf_counter() - start,
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
    active = [p for p in process_inventory()
              if "-m src.budget_sensitivity_worker" in (p["CommandLine"] or "")]
    assert not active, "budget workers remain active"
    start = perf_counter()
    (ARCH / "partial_runs").mkdir(parents=True)
    partial = []
    methods = {"greedy", "fixed01", "fixed03", "PEM_T", "PEM_ST",
               "pool_random", "sobol", "cma_es", "gp_ei", "turbo_1"}
    for directory in SOURCE.glob("budget_*D/*/*"):
        if directory.is_dir() and directory.parent.name in methods and not (directory / "summary.json").exists():
            rel = directory.relative_to(SOURCE)
            partial.append(rel.as_posix())
            target = ARCH / "partial_runs" / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(directory), str(target))
    completed = sum(1 for _ in SOURCE.glob("budget_*D/*/*/summary.json"))
    record = {
        "schema": "budget_interruption_recovery_20260924_v1",
        "completed_before_resume": completed,
        "partial_runs_archived": partial,
        "partial_run_count": len(partial),
        "total_workers": 8,
        "gp_workers_before_other_queue_empty": 2,
        "gp_workers_after_other_queue_empty": 8,
        "scientific_design_changed": False,
        "timing_comparability": "mixed_concurrency_not_for_speed_claims",
    }
    (ARCH / "recovery.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    save("formal_dynamic_resume_8x2_then_8gp", start, **record)
    call("src.run_budget_performance_sensitivity_dynamic", "runs.log")
    save("full_raw_audit", start, **record)
    call("src.analyze_budget_performance_sensitivity", "audit.log")
    save("complete", start, runs=2700, **record)


if __name__ == "__main__":
    main()
