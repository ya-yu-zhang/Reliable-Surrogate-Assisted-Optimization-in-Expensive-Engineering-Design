"""Third-interruption recovery with configuration-isolated process recognition."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from time import perf_counter

from .run_solo_cost import process_inventory


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "results/interruption_20260920_v3"
PACKAGES = ["numpy", "scipy", "ioh", "torch", "gpytorch", "scikit-learn"]
PYTHON_MODULE = re.compile(r'^\s*(?:"[^"]*python(?:\.exe)?"|\S*python(?:\.exe)?)\s+-m\s+([^\s]+)', re.I)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected_signature(fid, dim, instance, rep, method, budget):
    from .gp_references import code_hash
    return dict(
        fid=fid, dim=dim, instance=instance, rep=rep, method=method, budget=budget,
        seed=100000 * dim + 1000 * fid + 10 * instance + rep,
        code_hash=code_hash(), packages={name: importlib.metadata.version(name) for name in PACKAGES},
    )


def validate_cached(path, signature):
    summary = json.loads((path / "summary.json").read_text("utf-8"))
    assert summary["signature"] == signature
    assert summary["algorithm_evaluations"] == signature["budget"]
    assert summary["diagnostic_evaluations"] == 0
    events = (path / "events.jsonl").read_text("utf-8").splitlines()
    assert len(events) == 1 + 2 * signature["budget"]
    return summary


def matching_inventory(rows, config):
    normalized = str(Path(config)).lower().replace("/", "\\")
    basename = Path(config).name.lower()
    selected = []
    for row in rows:
        command = row["CommandLine"] or ""
        match = PYTHON_MODULE.search(command)
        if match and match.group(1).lower() == "src.resume_interrupted_gp_batch_v4_parallel":
            lowered = command.lower().replace("/", "\\")
            if normalized in lowered or basename in lowered:
                selected.append(row)
    return selected


def command_for(job, out, eligible):
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    manifest = json.loads((ARCHIVE / "recovery_manifest.json").read_text("utf-8"))
    assert manifest["objective_calls_by_archiver"] == 0 and manifest["old_paid_calls"] == 2514
    assert all(digest(ROOT / name) == value for name, value in manifest["recovery_sources"].items())
    config = json.loads((ROOT / args.config).read_text("utf-8"))
    out = ROOT / config["out"]
    source = Path(config["out"]).name
    eligible = {row["runid"]: row for row in manifest["partial_runs"] if row["source"] == source}
    assert len(eligible) == 4 and all((ROOT / row["archive"]).is_dir() for row in eligible.values())
    inventory = process_inventory()
    old = json.loads((out / "status.json").read_text("utf-8"))
    assert old["pid"] not in {row["ProcessId"] for row in inventory}, "Previous batch still live"
    current = {os.getpid(), os.getppid()}
    assert not [row for row in matching_inventory(inventory, args.config) if row["ProcessId"] not in current]
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
    start = perf_counter()
    completed = 0
    failed = []
    driver = dict(
        driver_sha256=digest(Path(__file__)),
        interruption_archive=ARCHIVE.relative_to(ROOT).as_posix(),
        eligible_partial_runs=sorted(eligible),
        cached_console_logs_preserved=True,
        scientific_parameters_unchanged=True,
        configuration_isolated_process_guard=True,
    )
    (out / "recovery_driver_v4.json").write_text(json.dumps(driver, indent=2), encoding="utf-8")

    def save(stage):
        (out / "status.json").write_text(
            json.dumps(
                dict(stage=stage, pid=pid, completed=completed, expected=len(jobs), failed=len(failed), elapsed=perf_counter() - start),
                indent=2,
            ),
            encoding="utf-8",
        )

    def execute(job):
        runid, command = command_for(job, out, eligible)
        if command is None:
            return None
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        log = out / (runid + ".log")
        if log.exists():
            log = out / (runid + ".recovery-v4.log")
        with log.open("x", encoding="utf-8") as stream:
            stream.write(result.stdout + result.stderr)
        if result.returncode:
            return dict(job=job, exit_code=result.returncode, log=log.name)
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
                failed.append(dict(job=futures[future], error_type=type(error).__name__, error=str(error)))
            save("running")
            if completed % 10 == 0 or completed == len(jobs):
                print(f"{completed}/{len(jobs)}; failed={len(failed)}", flush=True)
    (out / "failures.json").write_text(json.dumps(failed, indent=2), encoding="utf-8")
    save("failed" if failed else "complete")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
