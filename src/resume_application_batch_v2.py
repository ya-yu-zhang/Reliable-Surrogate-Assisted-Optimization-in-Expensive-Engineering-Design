"""Recover four application prefixes, then resume the unchanged frozen scheduler."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import os
import subprocess
import time


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "results/application_interruption_20260921_v1/partial_runs"
OUT = ROOT / "results/application_formal_v1"
APP = ROOT / ".venv-app/Scripts/python.exe"
CORE = ROOT / ".venv312/Scripts/python.exe"
COMPLETION = ROOT / "results/application_completion_v1"
JOBS = [
    ("gp_ei_DNA_r11_b500", "DNA", 11, "gp_ei"),
    ("PEM_T_DNA_r01_b500", "DNA", 1, "PEM_T"),
    ("turbo_1_synt_simple_r14_b500", "synt_simple", 14, "turbo_1"),
    ("turbo_1_DNA_r05_b500", "DNA", 5, "turbo_1"),
]


def recover(job: tuple[str, str, int, str]) -> dict:
    runid, dataset, rep, method = job
    command = [
        str(APP), "-m", "src.recover_interrupted_application_run",
        "--dataset", dataset, "--rep", str(rep), "--method", method,
        "--archive", str(ARCHIVE / runid),
    ]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    (OUT / (runid + "_recovery.log")).write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"Recovery failed: {runid}")
    return json.loads((OUT / runid / "recovery.json").read_text("utf-8"))


def main() -> None:
    assert ARCHIVE.is_dir()
    assert sum((OUT / name / "summary.json").is_file() for name in OUT.iterdir() if name.is_dir()) == 285
    assert not COMPLETION.exists()
    COMPLETION.mkdir()
    started = time.time()

    def save(stage: str, failure: str | None = None) -> None:
        payload = {
            "stage": stage, "pid": os.getpid(),
            "recovery_protocol": "application_paid_prefix_recovery_v1",
            "elapsed": time.time() - started, "failure": failure,
        }
        (COMPLETION / "status.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def execute(module: str, log_name: str) -> None:
        result = subprocess.run(
            [str(CORE), "-m", module], cwd=ROOT, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
        (COMPLETION / log_name).write_text(result.stdout + result.stderr, encoding="utf-8")
        if result.returncode:
            raise RuntimeError(f"{module} failed with exit code {result.returncode}")

    try:
        save("recovering_paid_prefixes")
        records = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(recover, job): job[0] for job in JOBS}
            for future in as_completed(futures):
                records.append(future.result())
                print(f"Recovered {futures[future]}", flush=True)
        assert sum(row["old_paid_calls"] for row in records) == 1368
        assert sum(row["new_paid_calls"] for row in records) == 632
        driver = {
            "schema": "application_recovery_driver_v2",
            "archive_manifest_sha256": hashlib.sha256(
                (ARCHIVE.parent / "archive_manifest.json").read_bytes()
            ).hexdigest(),
            "recovered": sorted(row["runid"] for row in records),
            "old_paid_calls": 1368,
            "new_paid_calls": 632,
        }
        (OUT / "recovery_driver_v2.json").write_text(json.dumps(driver, indent=2), encoding="utf-8")
        save("resuming_formal_application_batch")
        execute("src.application_batch_venv_entry", "recovery_batch_v2.log")
        save("full_raw_application_audit")
        execute("src.analyze_application", "full_raw_audit.log")
        save("paid_prefix_recovery_audit")
        execute("src.audit_application_recovery", "paid_prefix_recovery_audit.log")
        save("complete")
    except Exception as exc:
        save("failed", f"{type(exc).__name__}: {exc}")
        raise


if __name__ == "__main__":
    main()
