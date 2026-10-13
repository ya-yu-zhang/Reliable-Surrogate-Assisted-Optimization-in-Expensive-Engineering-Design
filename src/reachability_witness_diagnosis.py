"""Separately frozen two-witness diagnosis; never retries physical attempts."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
import time
from pathlib import Path

import numpy as np

from .physical_bound_screen import future_pool, sha, write

ROOT = Path(__file__).resolve().parents[1]
CONFIG = "configs/engineering_optimization_gp_reachability.json"


def verify_sources(plan):
    for name, digest in {**plan["source_hashes"], **plan["witness_frozen_hashes"]}.items():
        if sha((ROOT / name).read_bytes()) != digest:
            raise ValueError("Changed frozen source: " + name)


def prepare():
    from engibench.problems.beams2d import backend, v0, v1
    cfg = json.loads((ROOT / CONFIG).read_text())
    out = ROOT / cfg["out"]
    if out.exists():
        raise FileExistsError("Do not replace a prepared/executed protocol")
    previous = ROOT / "results/engineering_optimization_physical_bound_screen_v1"
    old = json.loads((previous / "plan.json").read_text())
    from .physical_bound_screen import check_plan
    check_plan(old)
    rows = list(csv.DictReader((previous / "candidate_bounds.csv").open()))
    thresholds = list(csv.DictReader((ROOT / "paper/engineering_optimization/physical_bound_screen_20261013/state_sharpness.csv").open()))
    witnesses = []
    for dataset in sorted({c["dataset"] for c in old["cases"]}):
        case = next(c for c in old["cases"] if c["dataset"] == dataset and len(c["classes"]) > 1)
        r = min((r for r in rows if (r["dataset"], r["state"]) == (dataset, case["state"])),
                key=lambda r: float(r["span_two_lower"]))
        pool, seed = future_pool(case, int(r["step"]), old["configs"])
        x = pool[int(r["pool_index"])]
        from .analyze_monotone_development import point_key
        if point_key(x) != r["point_key"]:
            raise AssertionError("Witness pool changed under the current runtime")
        t = next(t for t in thresholds if (t["dataset"], t["state"], t["continuation"], t["method"])
                 == (dataset, case["state"], "mean", "span_two_lower"))
        witnesses.append({"dataset": dataset, "state": case["state"], "block": case["block"],
                          "source": case["source"], "step": int(r["step"]), "pool_index": int(r["pool_index"]),
                          "pool_seed": seed, "point_key": point_key(x), "x": x.tolist(),
                          "stored_trial_lower": float(r["span_two_lower"]),
                          "required_root_tie_lower": float(t["required_tie_lower_bound"]),
                          "witness_true_response_read": False})
    sources = dict(old["known_source_files_sha256"])
    for p in previous.iterdir():
        if p.is_file():
            sources[p.relative_to(ROOT).as_posix()] = sha(p.read_bytes())
    for p in ["paper/engineering_optimization/physical_bound_screen_20261013/state_sharpness.csv",
              "src/physical_bound_screen.py", "src/reduced_compliance_bounds.py",
              "src/engineering_beam_adapter.py", "src/engineering_optimization_paired_mesh.py"]:
        sources[p] = sha((ROOT / p).read_bytes())
    frozen = [CONFIG, "src/reachability_witness_diagnosis.py",
              "paper/engineering_optimization/gp_reachability_20261013/PROTOCOL.md"]
    versions = {}
    for name in ["numpy", "scipy", "scikit-learn", "cvxopt", "engibench"]:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    plan = {"config": cfg, "witnesses": witnesses, "source_hashes": sources,
            "witness_frozen_hashes": {p: sha((ROOT / p).read_bytes()) for p in frozen},
            "engine_hashes": {name: sha(Path(module.__file__).read_bytes())
                              for name, module in [("backend", backend), ("v0", v0), ("v1", v1)]},
            "runtime_versions": versions,
            "runtime_version_difference_from_historical_experiments": True,
            "mean_states": old["cases"], "pool_configs": old["configs"],
            "new_physics_attempts": 0, "new_independent_samples": 0}
    verify_sources(plan)
    write(out / "plan.json", plan)
    print(json.dumps({"prepared": True, "witnesses": witnesses, "runtime_versions": versions}))


def run(protocol_commit):
    from engibench.problems.beams2d.v1 import Beams2D
    from engibench.problems.beams2d import backend, v0, v1
    from .engineering_beam_adapter import density_field
    from .engineering_optimization_paired_mesh import solve
    cfg = json.loads((ROOT / CONFIG).read_text())
    out = ROOT / cfg["out"]
    plan = json.loads((out / "plan.json").read_text())
    verify_sources(plan)
    if len(protocol_commit) != 40:
        raise ValueError("Published protocol commit required")
    for name, module in [("backend", backend), ("v0", v0), ("v1", v1)]:
        if sha(Path(module.__file__).read_bytes()) != plan["engine_hashes"][name]:
            raise ValueError("Changed physical engine")
    attempts, results = 0, []
    journal = (out / "witness_events.jsonl").open("x")
    def log(row):
        journal.write(json.dumps(row, separators=(",", ":"), allow_nan=False) + "\n")
        journal.flush(); os.fsync(journal.fileno())
    start = time.perf_counter()
    log({"event": "start", "protocol_commit": protocol_commit})
    try:
        problem = Beams2D(seed=0)
        for witness in plan["witnesses"]:
            if attempts >= cfg["max_new_physics_attempts"]:
                raise RuntimeError("Two-witness cap exceeded")
            field = density_field(witness["x"])
            attempts += 1
            log({"event": "pre_true_response", "attempt": attempts, **witness,
                 "density_sha256": sha(np.asarray(field, dtype='<f8').tobytes())})
            started = time.perf_counter()
            value, checks = solve(problem, field, 100, 50)
            row = {**witness, "y": value, "attempt": attempts, "physical_seconds": time.perf_counter() - started,
                   **checks, "residual_flag": checks["equilibrium_relative_residual"] > cfg["physical_residual_flag"]}
            row["actual_witness_disqualifies_full_pool_superset"] = value < witness["required_root_tie_lower"]
            row["trial_point_bound_is_loose_at_witness"] = value >= witness["required_root_tie_lower"] > witness["stored_trial_lower"]
            results.append(row)
            write(out / ("witness_" + witness["dataset"] + ".json"), row)
            log({"event": "true_response", **row})
            if row["residual_flag"]:
                raise RuntimeError("Residual gate failed; no replacement or retry")
        log({"event": "complete", "new_physics_attempts": attempts})
        write(out / "witness_status.json", {"complete": True, "protocol_commit": protocol_commit,
              "new_physics_attempts": attempts, "new_independent_samples": 0,
              "new_optimization_attempts": 0, "recovery_attempts": 0,
              "end_to_end_seconds": time.perf_counter() - start, "results": results})
    except Exception as e:
        log({"event": "failure", "new_physics_attempts": attempts, "error": repr(e)})
        write(out / "witness_status.json", {"complete": False, "new_physics_attempts": attempts,
              "new_independent_samples": 0, "replacement_or_recovery": False, "error": repr(e)})
        raise
    finally:
        journal.close()
    print(json.dumps({"complete": True, "new_physics_attempts": attempts,
                      "witness_results": [{k: v for k, v in r.items() if k != 'x'} for r in results]}))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["prepare", "run"])
    p.add_argument("--protocol-commit")
    a = p.parse_args()
    prepare() if a.mode == "prepare" else run(a.protocol_commit or "")
