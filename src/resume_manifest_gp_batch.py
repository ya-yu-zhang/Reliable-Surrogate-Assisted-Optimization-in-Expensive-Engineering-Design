"""Reusable exact-prefix GP batch recovery driven by an interruption manifest."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter

from .resume_interrupted_gp_batch_v5_parallel import (
    PYTHON_MODULE, digest, expected_signature, validate_cached,
)
from .run_solo_cost import process_inventory


ROOT = Path(__file__).resolve().parents[1]


def matching_inventory(rows: list[dict], config: str, module_name: str) -> list[dict]:
    normalized = str(Path(config)).lower().replace("/", "\\")
    basename = Path(config).name.lower()
    selected = []
    for row in rows:
        command = row["CommandLine"] or ""
        match = PYTHON_MODULE.search(command)
        if match and match.group(1).lower() == module_name.lower():
            lowered = command.lower().replace("/", "\\")
            if normalized in lowered or basename in lowered:
                selected.append(row)
    return selected


def run(config_arg: str, archive_relative: str, module_name: str, driver_name: str, log_suffix: str) -> None:
    archive = ROOT / archive_relative
    manifest = json.loads((archive / "recovery_manifest.json").read_text("utf-8"))
    assert manifest["objective_calls_by_archiver"] == 0
    assert manifest["all_pre_label_pairs_complete"] and manifest["no_pending_physical_return"]
    assert all(digest(ROOT / name) == value for name, value in manifest["recovery_sources"].items())
    config = json.loads((ROOT / config_arg).read_text("utf-8"))
    out = ROOT / config["out"]
    eligible = {row["runid"]: row for row in manifest["partial_runs"]}
    assert len(eligible) == 4 and all((ROOT / row["archive"]).is_dir() for row in eligible.values())
    inventory = process_inventory()
    old = json.loads((out / "status.json").read_text("utf-8"))
    assert old["pid"] not in {row["ProcessId"] for row in inventory}
    current = {os.getpid(), os.getppid()}
    assert not [row for row in matching_inventory(inventory, config_arg, module_name) if row["ProcessId"] not in current]
    target = str(out.resolve()).lower().replace("/", "\\")
    for row in inventory:
        if row["ProcessId"] in current:
            continue
        command = (row["CommandLine"] or "").lower().replace("/", "\\")
        match = PYTHON_MODULE.search(command)
        if match and match.group(1).lower() in ["src.gp_references", "src.recover_interrupted_run"]:
            assert target not in command, f"worker already targets {out}: {row['ProcessId']}"

    jobs = [
        (fid, dim, instance, rep, method)
        for fid in config["functions"] for dim in config["dimensions"]
        for instance in config["instances"] for rep in range(config["repeats"])
        for method in config["methods"]
    ]
    assert len(jobs) == 648
    pid = os.getpid()
    started = perf_counter()
    completed = 0
    failed: list[dict] = []
    (out / driver_name).write_text(json.dumps({
        "driver_sha256": digest(Path(__file__)),
        "launcher_sha256": digest(ROOT / (module_name.replace(".", "/") + ".py")),
        "interruption_archive": archive_relative,
        "eligible_partial_runs": sorted(eligible),
        "cached_console_logs_preserved": True,
        "scientific_parameters_unchanged": True,
        "configuration_isolated_process_guard": True,
    }, indent=2), encoding="utf-8")

    def save(stage: str) -> None:
        (out / "status.json").write_text(json.dumps({
            "stage": stage, "pid": pid, "completed": completed, "expected": len(jobs),
            "failed": len(failed), "elapsed": perf_counter() - started,
        }, indent=2), encoding="utf-8")

    def command_for(job: tuple) -> tuple[str, list[str] | None]:
        fid, dim, instance, rep, method = job
        budget = 10 * dim
        runid = f"{method}_f{fid:02}_d{dim}_i{instance}_r{rep}_b{budget}"
        directory = out / runid
        signature = expected_signature(fid, dim, instance, rep, method, budget)
        if (directory / "summary.json").exists():
            validate_cached(directory, signature)
            return runid, None
        if directory.exists():
            raise RuntimeError(runid + ": unarchived incomplete directory; refuse overwrite")
        if runid in eligible:
            row = eligible[runid]
            command = [
                sys.executable, "-m", "src.recover_interrupted_run", "--kind", "gp",
                "--archive", str(ROOT / row["archive"]), "--method", method,
                "--fid", str(fid), "--dim", str(dim), "--instance", str(instance),
                "--rep", str(rep), "--budget", str(budget), "--out", str(out),
            ]
        else:
            command = [
                sys.executable, "-m", "src.gp_references", "--method", method,
                "--fid", str(fid), "--dim", str(dim), "--instance", str(instance),
                "--rep", str(rep), "--out", str(out),
            ]
        return runid, command

    def execute(job: tuple) -> dict | None:
        runid, command = command_for(job)
        if command is None:
            return None
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        log = out / (runid + ".log")
        if log.exists():
            log = out / (runid + log_suffix + ".log")
        with log.open("x", encoding="utf-8") as stream:
            stream.write(result.stdout + result.stderr)
        if result.returncode:
            return {"job": job, "exit_code": result.returncode, "log": log.name}
        validate_cached(out / runid, expected_signature(*job, 10 * job[1]))
        return None

    save("running")
    print(f"{len(jobs)} jobs; {config['workers']} workers; {len(eligible)} paid prefixes eligible", flush=True)
    with ThreadPoolExecutor(max_workers=config["workers"]) as pool:
        futures = {pool.submit(execute, job): job for job in jobs}
        for future in as_completed(futures):
            completed += 1
            try:
                error = future.result()
                if error:
                    failed.append(error)
            except Exception as error:
                failed.append({"job": futures[future], "error_type": type(error).__name__, "error": str(error)})
            save("running")
            if completed % 10 == 0 or completed == len(jobs):
                print(f"{completed}/{len(jobs)}; failed={len(failed)}", flush=True)
    (out / "failures.json").write_text(json.dumps(failed, indent=2), encoding="utf-8")
    save("failed" if failed else "complete")
    if failed:
        raise SystemExit(1)
