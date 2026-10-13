"""Prospective limited-cost DEVELOPMENT screen of trial-space compliance bounds.

Samples give an UPPER bound on the attainable full-pool lower envelope. They
can disqualify this operator's sharpness; they cannot certify early outcomes.
All original seed groups remain in the record. No future true response is used
to select the references, sampled points or inclusion rule.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import qmc

from .analyze_monotone_development import load_sources, point_key
from .budgeted_decision_audit import classify
from .reduced_compliance_bounds import TrialSpace

ROOT = Path(__file__).resolve().parents[1]
CONFIG = "configs/engineering_optimization_physical_bound_screen.json"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w") as f:
        f.write(json.dumps(value, separators=(",", ":"), allow_nan=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(path)


def future_pool(case, step, configs):
    cfg = configs[case["dataset"]]
    if case["dataset"] == "previous_holdout":
        namespace = [cfg["master_seed"], case["block"], cfg["source_controls"].index(case["source"]), 5, step]
    else:
        namespace = [cfg["master_seed"], cfg["source_methods"].index(case["source"]), case["block"], step]
    seed = int(np.random.SeedSequence(namespace).generate_state(1)[0])
    return qmc.Sobol(19, scramble=True, seed=seed).random_base2(cfg["pool_power"]), seed


def metadata_cases(cases):
    unique = {}
    for case in cases:
        k = case["dataset"], case["state"]
        unique.setdefault(k, {key: case[key] for key in ["dataset", "block", "state", "source", "classes", "baseline", "initial", "X"]})
    return sorted(unique.values(), key=lambda r: (r["dataset"], r["block"], r["source"], r["state"]))


def prepare():
    cfg = json.loads((ROOT / CONFIG).read_text())
    out = ROOT / cfg["out"]
    if out.exists():
        raise FileExistsError("Existing screen: do not overwrite or replace references")
    cases, sources = load_sources(ROOT)
    cases = metadata_cases(cases)
    configs = {
        "previous_holdout": json.loads((ROOT / "configs/engineering_optimization_budget_audit.json").read_text()),
        "archived_common_mean": json.loads((ROOT / "results/engineering_optimization_common_continuation_v1/manifest.json").read_text())["config"]}
    reference_case = next(c for c in cases if c["dataset"] == "previous_holdout")
    # The first state's initial incumbent is chosen from its already observed
    # X/y only, not any first-action/continuation response or positive class.
    s = json.loads((ROOT / f"results/engineering_optimization_budget_audit_v1/block_{reference_case['block']}/{reference_case['state']}_summary.json").read_text())
    index = int(np.argmin(s["y"]))
    reference = {"state": s["state"], "block": s["block"], "training_index": index,
                 "x": s["X"][index], "stored_y": s["y"][index]}
    planned = []
    candidate_count = 0
    for case in cases:
        record = {k: case[k] for k in ["dataset", "block", "state", "source", "classes", "baseline", "initial"]}
        record["pools"] = []
        if len(case["classes"]) > 1:
            observed = {point_key(x) for x in case["X"]}
            for step in range(1, cfg["horizon"] + 1):
                pool, seed = future_pool(case, step, configs)
                indices = [i for i, x in enumerate(pool) if point_key(x) not in observed][:cfg["samples_per_future_pool"]]
                candidate_count += len(indices)
                record["pools"].append({"step": step, "seed": seed,
                    "full_pool_sha256": sha(pool.tobytes()), "indices": indices,
                    "sample_points_sha256": sha(pool[indices].tobytes())})
        planned.append(record)
    if candidate_count > cfg["max_candidate_bound_evaluations"]:
        raise ValueError("Planned bound cap exceeded")
    frozen = [CONFIG, "src/reduced_compliance_bounds.py", "src/physical_bound_screen.py",
              "paper/engineering_optimization/physical_bound_screen_20261013/PROTOCOL.md",
              "tests/test_reduced_compliance_bounds.py", "tests/test_physical_bound_screen.py"]
    from engibench.problems.beams2d import backend, v0
    versions, missing = {}, []
    for package in ["numpy", "scipy", "engibench", "cvxopt"]:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
            missing.append(package)
    plan = {"config": cfg, "cases": planned, "configs": configs, "training_reference": reference,
            "known_source_files_sha256": sources,
            "frozen_files_sha256": {p: sha((ROOT / p).read_bytes()) for p in frozen},
            "engine_sha256": {"backend": sha(Path(backend.__file__).read_bytes()), "v0": sha(Path(v0.__file__).read_bytes())},
            "versions": versions, "distribution_metadata_unavailable": missing,
            "stored_states": len(cases), "candidate_designs": candidate_count,
            "alias_only_states": sum(len(c["classes"]) == 1 for c in cases),
            "new_physics_attempts": 0, "future_true_labels_used_for_plan": False,
            "new_independent_validation": False}
    write(out / "plan.json", plan)
    print(json.dumps({"prepared": True, "stored_states": len(cases), "candidate_designs": candidate_count,
                      "alias_only_states": plan["alias_only_states"], "new_physics_attempts": 0}))


def check_plan(plan):
    for p, digest in {**plan["known_source_files_sha256"], **plan["frozen_files_sha256"]}.items():
        if sha((ROOT / p).read_bytes()) != digest:
            raise ValueError("Changed frozen input: " + p)


def run(protocol_commit):
    from engibench.problems.beams2d.v1 import Beams2D
    from engibench.problems.beams2d import backend, v0
    from .engineering_beam_adapter import density_field
    from .engineering_optimization_paired_mesh import solve
    cfg = json.loads((ROOT / CONFIG).read_text())
    out = ROOT / cfg["out"]
    plan = json.loads((out / "plan.json").read_text())
    check_plan(plan)
    if len(protocol_commit) != 40:
        raise ValueError("Verified repository protocol commit required")
    if (sha(Path(backend.__file__).read_bytes()) != plan["engine_sha256"]["backend"] or
            sha(Path(v0.__file__).read_bytes()) != plan["engine_sha256"]["v0"]):
        raise ValueError("Changed physical engine")
    if (out / "events.jsonl").exists():
        raise FileExistsError("Existing physical execution; no automatic recovery")
    vectors, reference_rows = [], []
    attempts = 0
    queries = 0
    started_total = time.perf_counter()
    journal = (out / "events.jsonl").open("x")

    def log(row):
        journal.write(json.dumps(row, separators=(",", ":"), allow_nan=False) + "\n")
        journal.flush()
        os.fsync(journal.fileno())

    log({"event": "start", "protocol_commit": protocol_commit, "new_independent_validation": False})
    try:
        problem = Beams2D(seed=0)
        for name in ["all_solid", "training_incumbent"]:
            field = np.ones((50, 100)) if name == "all_solid" else density_field(plan["training_reference"]["x"])
            if attempts >= cfg["max_new_physics_attempts"]:
                raise RuntimeError("Reference attempt cap reached")
            attempts += 1
            log({"event": "pre_reference", "reference": name, "attempt": attempts,
                 "density_sha256": sha(np.asarray(field, dtype='<f8').tobytes()),
                 "purpose": "trial displacement; all-solid is not a feasible .35-volume design"})
            started = time.perf_counter()
            value, checks = solve(problem, field, 100, 50)
            elapsed = time.perf_counter() - started
            st = problem._Beams2D__st
            vector = st.u.ravel().copy()
            if not np.array_equal(vector[st.fixed], np.zeros(len(st.fixed))):
                raise AssertionError("Inadmissible trial boundary values")
            record = {"reference": name, "y": value, "u": vector.tolist(),
                      "density_sha256": sha(np.asarray(field, dtype='<f8').tobytes()),
                      "physical_seconds": elapsed, **checks}
            if name == "training_incumbent":
                record["relative_stored_response_difference"] = abs(value - plan["training_reference"]["stored_y"]) / plan["training_reference"]["stored_y"]
                record["source_agreement_flag"] = record["relative_stored_response_difference"] > cfg["source_repeat_relative_tolerance"]
            record["residual_flag"] = checks["equilibrium_relative_residual"] > cfg["reference_residual_flag"]
            write(out / f"reference_{name}.json", record)
            reference_rows.append({k: v for k, v in record.items() if k != "u"})
            vectors.append(vector)
            log({"event": "label_reference", "reference": name, "attempt": attempts,
                 **reference_rows[-1]})
            if record["residual_flag"] or record.get("source_agreement_flag", False):
                raise RuntimeError("Reference numerical/source-agreement gate failed; raw response retained")
        started = time.perf_counter()
        columns = np.stack(vectors, axis=-1)
        # Single unit load makes each work value exactly a negated stored float.
        space = TrialSpace(columns[st.edofMat], st.KE, -columns[1, :], emin=st.Emin, emax=st.Emax)
        gram_seconds = time.perf_counter() - started
        write(out / "trial_space.json", {"grams": space.grams.tolist(), "errors": space.errors.tolist(),
              "load_work": space.q.tolist(), "Emin": st.Emin, "Emax": st.Emax,
              "gram_seconds": gram_seconds, "arithmetic_scope": "Conditional discrete SPD/IEEE model; not a PDE or oracle-output error certificate"})
        rows = []
        mapping_seconds = 0.
        bound_seconds = 0.
        for case in plan["cases"]:
            for item in case["pools"]:
                pool, seed = future_pool(case, item["step"], plan["configs"])
                if seed != item["seed"] or sha(pool.tobytes()) != item["full_pool_sha256"] or sha(pool[item["indices"]].tobytes()) != item["sample_points_sha256"]:
                    raise AssertionError("Planned future-pool mismatch")
                for index in item["indices"]:
                    if queries >= cfg["max_candidate_bound_evaluations"]:
                        raise RuntimeError("Bound-design cap reached")
                    x = pool[index]
                    started = time.perf_counter()
                    rho = density_field(x).T.reshape(-1)
                    mapping_time = time.perf_counter() - started
                    mapping_seconds += mapping_time
                    started = time.perf_counter()
                    bounds = space.evaluate(rho)
                    bound_time = time.perf_counter() - started
                    bound_seconds += bound_time
                    queries += 1
                    row = {"dataset": case["dataset"], "state": case["state"], "block": case["block"],
                           "source": case["source"], "step": item["step"], "pool_index": index,
                           "point_key": point_key(x), "initial_incumbent": case["initial"],
                           **{k: v for k, v in bounds.items() if k != "coefficients"},
                           "mapping_seconds": mapping_time, "bound_seconds": bound_time}
                    rows.append(row)
            log({"event": "state_bound_complete", "state": case["state"], "dataset": case["dataset"],
                 "candidate_queries_so_far": queries, "alias_only": not bool(case["pools"])})
            print(json.dumps({"state": case["state"], "queries": queries, "reference_attempts": attempts}), flush=True)
        with (out / "candidate_bounds.csv").open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
        log({"event": "complete", "new_physics_attempts": attempts, "candidate_queries": queries})
        journal.close()
        status = {"complete": True, "protocol_commit": protocol_commit,
                  "new_physics_attempts": attempts, "new_optimization_oracle_attempts": 0,
                  "new_independent_states": 0, "recovery_attempts": 0,
                  "candidate_bound_design_queries": queries, "reduced_2x2_system_attempts": queries,
                  "full_linear_system_solves": attempts, "oracle_cache_reads": 0,
                  "reference_physical_seconds": sum(r["physical_seconds"] for r in reference_rows),
                  "trial_gram_seconds": gram_seconds, "density_mapping_seconds": mapping_seconds,
                  "candidate_bound_seconds": bound_seconds, "end_to_end_run_seconds": time.perf_counter() - started_total,
                  "journal_sha256": sha((out / "events.jsonl").read_bytes()),
                  "files_sha256": {p.name: sha(p.read_bytes()) for p in out.iterdir() if p.is_file() and p.name != "run_status.json"},
                  "early_outcomes_certified": 0, "sampling_is_falsification_only": True}
        write(out / "run_status.json", status)
        print(json.dumps(status))
    except Exception as exc:
        log({"event": "failure", "new_physics_attempts": attempts, "candidate_queries": queries, "error": repr(exc)})
        journal.close()
        write(out / "run_status.json", {"complete": False, "new_physics_attempts": attempts,
              "candidate_bound_design_queries": queries, "error": repr(exc), "replacement_reference_used": False,
              "journal_sha256": sha((out / "events.jsonl").read_bytes())})
        raise


def analyze():
    cfg = json.loads((ROOT / CONFIG).read_text())
    out, dest = ROOT / cfg["out"], ROOT / cfg["report"]
    status = json.loads((out / "run_status.json").read_text())
    plan = json.loads((out / "plan.json").read_text())
    check_plan(plan)
    if not status["complete"]:
        raise ValueError("Failed screen: report failure, no recovery or favorable replacement")
    for name, digest in status["files_sha256"].items():
        if sha((out / name).read_bytes()) != digest:
            raise ValueError("Changed physical record: " + name)
    cases, source_hashes = load_sources(ROOT)
    rows = list(csv.DictReader((out / "candidate_bounds.csv").open()))
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["dataset"], row["state"]].append(row)
    detail = []
    for case in cases:
        baseline = case["curves"][case["baseline"]][5]["incumbent"]
        margin = cfg["original_dataset_margins"][case["dataset"]]
        required = max(0., baseline - margin * case["initial"])
        counts = Counter(classify((baseline - rr[5]["incumbent"]) / case["initial"], margin)
                         for b, rr in case["curves"].items() if b != case["baseline"])
        sample_rows = grouped[case["dataset"], case["state"]]
        for method in ["all_solid_trial_lower", "training_trial_lower", "two_trial_max_lower", "span_two_lower"]:
            witness = min(sample_rows, key=lambda r: float(r[method])) if sample_rows else None
            cap = float(witness[method]) if witness else None
            detail.append({"dataset": case["dataset"], "state": case["state"], "block": case["block"],
                "continuation": case["continuation"], "method": method,
                "classes": len(case["classes"]), "tie_contrasts": counts["tie"],
                "nonbaseline_contrasts": len(case["classes"]) - 1,
                "completed_baseline_endpoint": baseline, "required_tie_lower_bound": required,
                "sample_minimum_upper_cap_on_full_envelope": cap,
                "upper_cap_percent_of_required_bound": 100 * cap / required if cap is not None and required else None,
                "witness_disqualifies_root_tie_sharpness": cap is not None and cap < required,
                "early_tie_certified": False,
                "witness_step": int(witness["step"]) if witness else None,
                "witness_pool_index": int(witness["pool_index"]) if witness else None,
                "witness_point_key": witness["point_key"] if witness else None})
    aggregates = defaultdict(list)
    for row in detail:
        aggregates[row["dataset"], row["continuation"], row["method"]].append(row)
    summary = []
    for key, rr in sorted(aggregates.items()):
        eligible = [r for r in rr if r["nonbaseline_contrasts"]]
        ratios = sorted(r["upper_cap_percent_of_required_bound"] for r in eligible)
        summary.append({"dataset": key[0], "continuation": key[1], "method": key[2],
                       "seed_groups": len({r["block"] for r in rr}), "dependent_states": len(rr),
                       "nontrivial_states": len(eligible),
                       "states_disqualified_for_root_tie_sharpness": sum(r["witness_disqualifies_root_tie_sharpness"] for r in eligible),
                       "unique_tie_contrasts": sum(r["tie_contrasts"] for r in rr),
                       "tie_contrasts_disqualified": sum(r["tie_contrasts"] for r in rr if r["witness_disqualifies_root_tie_sharpness"]),
                       "minimum_upper_cap_percent_of_required": min(ratios),
                       "median_upper_cap_percent_of_required": float(np.median(ratios)),
                       "maximum_upper_cap_percent_of_required": max(ratios), "early_ties_certified": 0})
    physical_sources = {str((out / name).relative_to(ROOT)): digest for name, digest in status["files_sha256"].items()}
    physical_sources[str((out / "run_status.json").relative_to(ROOT))] = sha((out / "run_status.json").read_bytes())
    report = {"analysis_type": "development necessary-sharpness screen; not independent validation or full-envelope certification",
              "source_files_sha256": {**source_hashes, **physical_sources},
              "protocol_commit": status["protocol_commit"], "cost_ledger": status,
              "states": 60, "state_continuation_contexts": 90, "alias_only_states": plan["alias_only_states"],
              "samples_can_falsify_but_never_certify": True,
              "candidate_point_bound_scope": "Conditional SPD discrete model and documented float arithmetic; no oracle-output or continuous-physics error certificate",
              "new_optimization_oracle_labels": 0, "new_independent_samples": 0,
              "new_theory_or_prior_work_superiority_claimed": False, "summary": summary,
              "start_independent_validation": False,
              "reason": "This limited sample screen cannot pass a complete sharpness, numerical-validity and end-to-end cost gate; inspect reported disqualification counts before investing in full envelopes.",
              "submission_ready": False}
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "analysis.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    for name, records in [("state_sharpness.csv", detail), ("summary.csv", summary)]:
        with (dest / name).open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(records[0]), lineterminator="\n")
            w.writeheader()
            w.writerows(records)
    print(json.dumps({"summary": summary, "new_physics_attempts": status['new_physics_attempts'], "independent_validation": False}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--analyze", action="store_true")
    parser.add_argument("--protocol-commit")
    args = parser.parse_args()
    if args.prepare:
        prepare()
    elif args.run:
        run(args.protocol_commit or "")
    elif args.analyze:
        analyze()
    else:
        parser.error("Select prepare, run or analyze")
