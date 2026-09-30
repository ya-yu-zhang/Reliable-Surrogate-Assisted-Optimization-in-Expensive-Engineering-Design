"""Recover three paid prefixes, resume the frozen scheduler, and complete audits."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import subprocess
from time import perf_counter


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "results/application_interruption_20260922_v2/partial_runs"
FORMAL = ROOT / "results/application_formal_v1"
OUT = ROOT / "results/application_completion_v1"
APP = ROOT / ".venv-app/Scripts/python.exe"
CORE = ROOT / ".venv312/Scripts/python.exe"
JOBS = [
    ("cma_es_DNA_r08_b500", "DNA", 8, "cma_es"),
    ("turbo_1_DNA_r04_b500", "DNA", 4, "turbo_1"),
    ("turbo_1_synt_simple_r07_b500", "synt_simple", 7, "turbo_1"),
]


def recover(job):
    runid, dataset, rep, method = job
    result = subprocess.run([str(APP), "-m", "src.recover_interrupted_application_run",
        "--dataset", dataset, "--rep", str(rep), "--method", method,
        "--archive", str(ARCHIVE / runid)], cwd=ROOT, capture_output=True, text=True,
        encoding="utf-8", errors="replace")
    (FORMAL / (runid + "_recovery_v2.log")).write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"Recovery failed: {runid}")
    return json.loads((FORMAL / runid / "recovery.json").read_text("utf-8"))


def main() -> None:
    assert ARCHIVE.is_dir() and not OUT.exists()
    assert sum((path / "summary.json").is_file() for path in FORMAL.iterdir() if path.is_dir()) == 376
    OUT.mkdir(); started = perf_counter(); stage = "recovering_second_interruption_prefixes"; failure = None
    def save():
        (OUT / "status.json").write_text(json.dumps({"stage": stage, "pid": os.getpid(),
            "elapsed": perf_counter() - started, "failure": failure,
            "recovery_protocol": "application_second_interruption_recovery_v2"}, indent=2), encoding="utf-8")
    def execute(module, log):
        result = subprocess.run([str(CORE), "-m", module], cwd=ROOT, capture_output=True,
                                text=True, encoding="utf-8", errors="replace")
        (OUT / log).write_text(result.stdout + result.stderr, encoding="utf-8")
        if result.returncode: raise RuntimeError(f"{module} failed with exit code {result.returncode}")
    try:
        save(); records = []
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(recover, job): job[0] for job in JOBS}
            for future in as_completed(futures):
                records.append(future.result()); print(f"Recovered {futures[future]}", flush=True)
        assert sum(row["old_paid_calls"] for row in records) == 924
        assert sum(row["new_paid_calls"] for row in records) == 576
        driver = {"schema": "application_recovery_driver_v4",
            "archive_manifest_sha256": hashlib.sha256((ARCHIVE.parent / "archive_manifest.json").read_bytes()).hexdigest(),
            "recovered": sorted(row["runid"] for row in records), "old_paid_calls": 924, "new_paid_calls": 576}
        (FORMAL / "recovery_driver_v4.json").write_text(json.dumps(driver, indent=2), encoding="utf-8")
        stage = "auditing_second_recovery"; save(); execute("src.audit_application_recovery_v2", "recovery_audit_v2.log")
        stage = "resuming_formal_application_batch"; save(); execute("src.application_batch_pid_reuse_entry", "batch.log")
        stage = "full_raw_application_audit"; save(); execute("src.analyze_application", "full_raw_audit.log")
        stage = "complete"; save()
    except Exception as exc:
        failure = {"error_type": type(exc).__name__, "error": str(exc)}; stage = "failed"; save(); raise


if __name__ == "__main__":
    main()
