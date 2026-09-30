"""Wait for the frozen CPU gate, resume solo cost, audit it, and close references."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
from time import perf_counter, sleep

from .run_solo_cost import background_cpu
from .run_solo_cost_launcher_safe import find_overlaps, process_inventory_with_parents


ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / ".venv312/Scripts/python.exe"
OUT = ROOT / "results/solo_cost_idle_supervisor_v1"
REFERENCE = ROOT / "results/reference_completion_v1"
SOLO = ROOT / "results/solo_cost_v1"
THRESHOLD = 5.0


def retryable_cost_failure(status: dict) -> bool:
    failure = status.get("failure") or {}
    return (
        status.get("stage") == "failed"
        and isinstance(failure.get("error"), str)
        and failure["error"].startswith("Background CPU ")
        and failure.get("completed", 0) == status.get("completed", 0)
    )


def execute(module: str, log: Path, *arguments: str) -> None:
    result = subprocess.run(
        [str(CORE), "-m", module, *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    log.write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"{module} exited {result.returncode}; see {log.name}")


def main() -> None:
    assert not OUT.exists() and not REFERENCE.exists()
    OUT.mkdir(parents=True)
    REFERENCE.mkdir(parents=True)
    started = perf_counter()
    stage = "auditing_formal_references"
    failure = None
    attempts = 0
    cpu_samples: list[float] = []
    own_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

    def save() -> None:
        payload = {
            "stage": stage,
            "pid": os.getpid(),
            "pipeline_sha256": own_hash,
            "attempts": attempts,
            "prelaunch_cpu_samples": cpu_samples,
            "elapsed": perf_counter() - started,
            "failure": failure,
        }
        (OUT / "status.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        reference_payload = {
            "stage": stage,
            "pid": os.getpid(),
            "pipeline_sha256": own_hash,
            "recovery_protocol": "idle_supervised_portable_solo_cost_v1",
            "external_audits_completed": ["gp_ei_reference_v1", "turbo_reference_v1"],
            "elapsed": perf_counter() - started,
            "failure": failure,
        }
        (REFERENCE / "status.json").write_text(
            json.dumps(reference_payload, indent=2), encoding="utf-8"
        )

    try:
        save()
        for source, destination in [
            ("turbo_reference_v1", "turbo_reference_analysis_v1"),
            ("gp_ei_reference_v1", "gp_ei_reference_analysis_v1"),
        ]:
            batch = json.loads((ROOT / "results" / source / "status.json").read_text("utf-8"))
            assert batch["stage"] == "complete" and batch["completed"] == batch["expected"] == 648
            assert batch["failed"] == 0
            execute(
                "src.analyze_gp_references",
                REFERENCE / (source + "_audit.log"),
                "--source",
                "results/" + source,
                "--out",
                "results/" + destination,
            )

        while True:
            stage = "waiting_for_background_cpu"
            save()
            overlaps = find_overlaps(process_inventory_with_parents(), os.getpid())
            if overlaps:
                raise RuntimeError(
                    "Scientific processes active before cost launch: "
                    + ",".join(str(row["ProcessId"]) for row in overlaps)
                )
            cpu = background_cpu()
            cpu_samples.append(cpu)
            save()
            if cpu > THRESHOLD:
                sleep(30)
                continue

            attempts += 1
            stage = "serial_cost_measurement"
            save()
            result = subprocess.run(
                [str(CORE), "-m", "src.run_solo_cost_portable"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            (OUT / f"attempt_{attempts:03d}.log").write_text(
                result.stdout + result.stderr, encoding="utf-8"
            )
            status = json.loads((SOLO / "status.json").read_text("utf-8"))
            if result.returncode == 0:
                assert status["stage"] == "complete" and status["completed"] == status["expected"] == 54
                break
            if not retryable_cost_failure(status):
                raise RuntimeError(f"Non-retryable solo-cost failure in attempt {attempts}")
            sleep(30)

        stage = "serial_cost_audit"
        save()
        execute("src.analyze_solo_cost", REFERENCE / "solo_cost_audit.log")
        stage = "complete"
        save()
        print("Idle-supervised solo cost and reference completion passed.", flush=True)
    except Exception as error:
        failure = {"error": str(error)}
        stage = "failed"
        save()
        raise


if __name__ == "__main__":
    main()
