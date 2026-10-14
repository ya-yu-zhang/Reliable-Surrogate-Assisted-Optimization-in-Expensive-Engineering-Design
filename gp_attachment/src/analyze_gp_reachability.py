"""Execute the frozen H1 development comparison without acquiring physics.

Construction reads only response-free initial plans. Grading reads trajectories
only after a complete construction manifest exists. All exclusions are retained
with binary coefficient bands and exact rational witnesses. No H5 extension,
native prediction certificate, or deployed cost saving is inferred.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import time
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

import numpy as np
from sklearn.gaussian_process.kernels import ConstantKernel, Matern

from .analyze_monotone_development import point_key
from .engineering_beam_adapter import density_field
from .engineering_optimization_common_continuation import model
from .gp_action_reachability import (category_from_interval,
    coefficient_enclosures, joint_two_response_lower, outer_actions,
    rational_infeasible)
from .physical_bound_screen import future_pool, sha, write
from .reachability_witness_diagnosis import verify_sources
from .reduced_compliance_bounds import TrialSpace

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "58f539c2d0738b20c7d0d4889fe8d808a03a3019"
OUT = ROOT / "results/engineering_optimization_gp_reachability_v1"
REPORT = ROOT / "paper/engineering_optimization/gp_reachability_20261013"
MODES = ("nonnegative", "trial_lower")


def gate():
    plan = json.loads((OUT / "plan.json").read_text())
    verify_sources(plan)
    if plan["config"] != json.loads((ROOT / "configs/engineering_optimization_gp_reachability.json").read_text()):
        raise ValueError("Configuration differs from the frozen plan")
    status = json.loads((OUT / "witness_status.json").read_text())
    events = [json.loads(s) for s in (OUT / "witness_events.jsonl").read_text().splitlines()]
    pres = [s for s in events if s["event"] == "pre_true_response"]
    if (not status["complete"] or status["protocol_commit"] != BASELINE
            or status["new_physics_attempts"] != 2 or len(pres) != 2
            or any(r["residual_flag"] for r in status["results"])
            or status["new_independent_samples"] != 0):
        raise ValueError("Both successful once-only witness diagnoses are required")
    for w, r, pre in zip(plan["witnesses"], status["results"], pres, strict=True):
        if any(w[k] != r[k] or w[k] != pre[k] for k in w):
            raise ValueError("A witness differs from its published selection")
    return plan


def initial_record(meta):
    """The source plans contain initial training responses, no future labels."""
    if meta["dataset"] == "archived_common_mean":
        path = ROOT / "results/engineering_optimization_common_continuation_v1/plans" / (meta["state"] + ".json")
    else:
        path = ROOT / f"results/engineering_optimization_budget_audit_v1/block_{meta['block']}" / (meta["state"] + "_plan.json")
    raw = json.loads(path.read_text())
    forbidden = {"trajectories", "calibration", "branch_records", "control_curves"}
    if forbidden.intersection(raw):
        raise ValueError("A response-bearing summary was supplied to construction")
    classes = raw.get("classes", raw.get("decision_classes"))
    classes = {b: [n for n in names if n != "mean_common_shift"] for b, names in classes.items()}
    if classes != meta["classes"] or raw["initial_best"] != meta["initial"]:
        raise ValueError("Initial source metadata differs from frozen plan")
    return {k: raw[k] for k in ("X", "y", "theta", "actions")}


def restored_trial_space():
    stored = json.loads((ROOT / "results/engineering_optimization_physical_bound_screen_v1/trial_space.json").read_text())
    # Reuse the published Gram enclosures. Never regenerate displacement solves.
    space = TrialSpace.__new__(TrialSpace)
    space.grams, space.errors = np.array(stored["grams"]), np.array(stored["errors"])
    space.q = np.array(stored["load_work"])
    space.emin, space.emax = stored["Emin"], stored["Emax"]
    if space.grams.shape != (5000, 2, 2) or space.errors.shape != space.grams.shape:
        raise ValueError("Invalid stored trial space")
    if not np.isfinite(space.grams).all() or not np.isfinite(space.errors).all() or (space.errors < 0).any():
        raise ValueError("Invalid stored Gram enclosures")
    return space


def safe_action_sets(matrix, cross, known_y, pending_lower):
    """A failed inverse gate retains every eligible action in both ranges."""
    try:
        coefficients = coefficient_enclosures(matrix, cross, known_y)
    except (np.linalg.LinAlgError, FloatingPointError) as error:
        n = len(cross)
        sets = {mode: {"indices": np.arange(n),
                      "response_lower": np.full(n, 0. if mode == "nonnegative" else pending_lower),
                      "response_upper": np.full(n, np.inf), "excluded_proofs": [],
                      "unresolved_exclusions_retained": 0} for mode in MODES}
        return None, sets, repr(error)
    sets = {mode: outer_actions(coefficients["slope"], coefficients["intercept"],
                slope_error=coefficients["slope_error"], intercept_error=coefficients["intercept_error"],
                response_lower=0. if mode == "nonnegative" else pending_lower) for mode in MODES}
    return coefficients, sets, None


def save_set(result):
    ids = result["indices"]
    row = {"indices": ids.tolist(), "response_lower": result["response_lower"][ids].tolist(),
           "response_upper": [None if math.isinf(x) else float(x) for x in result["response_upper"][ids]],
           "excluded_proofs": result["excluded_proofs"],
           "unresolved_exclusions_retained": result["unresolved_exclusions_retained"]}
    for key, value in result.items():
        if key.startswith("coefficient_band_"):
            row[key] = value.tolist()
    return row


def verify_set(row, eligible_count, response_lower):
    ids = row["indices"]
    excluded = {p[0] for p in row["excluded_proofs"]}
    if len(set(ids)) != len(ids) or excluded.intersection(ids) or set(ids) | excluded != set(range(eligible_count)):
        raise ValueError("Set membership/exclusion coverage mismatch")
    if len(excluded) != len(row["excluded_proofs"]):
        raise ValueError("Duplicate exclusion proof")
    if row["excluded_proofs"]:
        bands = [np.array(row[k]) for k in ("coefficient_band_lower_slope",
            "coefficient_band_lower_intercept", "coefficient_band_upper_slope",
            "coefficient_band_upper_intercept")]
        for proof in row["excluded_proofs"]:
            if not rational_infeasible(*bands, proof[0], proof[1:], response_lower):
                raise ValueError("Invalid exact rational exclusion proof")
    if len(ids) != len(row["response_lower"]) or len(ids) != len(row["response_upper"]):
        raise ValueError("Feasible range count mismatch")
    return len(excluded)


def construct():
    plan = gate()
    target = OUT / "construction"
    if target.exists():
        raise FileExistsError("Construction already exists; inspect rather than overwrite")
    target.mkdir()
    start = time.perf_counter()
    journal = (OUT / "gp_construction_events.jsonl").open("x")
    def log(value):
        journal.write(json.dumps(value, separators=(",", ":"), allow_nan=False) + "\n")
        journal.flush(); os.fsync(journal.fileno())
    stats = Counter(); timings = Counter(); files = {}; exclusions = []
    witness_hashes = {p.name: sha(p.read_bytes()) for p in OUT.glob("witness_*")}
    source_paths = [Path(__file__), ROOT / "src/gp_action_reachability.py",
        ROOT / "src/reduced_compliance_bounds.py", ROOT / "src/engineering_beam_adapter.py"]
    log({"event": "start", "baseline_commit": BASELINE, "future_responses_exposed": False})
    space = restored_trial_space()
    try:
        for meta in plan["mean_states"]:
            if len(meta["classes"]) == 1:
                exclusions.append({k: meta[k] for k in ("dataset", "state", "block", "source", "classes")})
                stats["alias_only_states"] += 1
                continue
            cfg = plan["pool_configs"][meta["dataset"]]
            initial = initial_record(meta)
            X, y = np.array(initial["X"]), np.array(initial["y"])
            if X.shape != (100, 19) or y.shape != (100,) or float(y.min()) != meta["initial"]:
                raise ValueError("Invalid initial training history")
            begin = time.perf_counter()
            pool, seed = future_pool(meta, 1, plan["pool_configs"])
            promised = next(m for m in meta["pools"] if m["step"] == 1)
            if seed != promised["seed"] or sha(pool.tobytes()) != promised["full_pool_sha256"]:
                raise ValueError("Next Sobol pool differs from the published pool")
            timings["full_pool_construction_seconds"] += time.perf_counter() - begin
            pool_keys = [point_key(x) for x in pool]
            observed = {point_key(x) for x in X}
            cache = {}
            def bound(x):
                key = point_key(x)
                stats["realized_bound_requests"] += 1
                if key in cache:
                    stats["realized_bound_cache_hits"] += 1
                    return cache[key]
                if stats["unique_bound_designs"] >= plan["config"]["max_unique_bound_designs"]:
                    raise RuntimeError("Frozen bound-design cap exceeded")
                t = time.perf_counter()
                rho = density_field(x).T.reshape(-1)
                timings["density_mapping_seconds"] += time.perf_counter() - t
                t = time.perf_counter()
                value = space.evaluate(rho)
                timings["bound_evaluation_seconds"] += time.perf_counter() - t
                stats["unique_bound_designs"] += 1
                stats["reduced_2x2_system_attempts"] += value["reduced_system_attempts"]
                stats["reduced_2x2_system_successes"] += int(value["reduced_system_success"])
                cache[key] = value["span_two_lower"]
                return cache[key]
            # Acquire the strong comparator library once per state, sharing it
            # among all first actions and both response ranges.
            raw_lowers = [bound(x) if key not in observed else None for x, key in zip(pool, pool_keys, strict=True)]
            branches = {}
            for branch in meta["classes"]:
                x = np.array(initial["actions"][branch])
                if point_key(x) in observed:
                    raise ValueError("The pending action is already observed")
                t = time.perf_counter(); pending_lower = bound(x)
                timings["pending_bound_total_seconds"] += time.perf_counter() - t
                eligible = np.array([i for i, key in enumerate(pool_keys) if key not in observed and key != point_key(x)])
                xx = np.vstack((X, x))
                t = time.perf_counter()
                kernel = (ConstantKernel(1., (.05, 20)) * Matern(np.full(19, .2), (.005, 2.), nu=2.5)).clone_with_theta(np.array(initial["theta"]))
                matrix = kernel(xx); matrix[np.diag_indices_from(matrix)] += cfg["alpha"]
                cross = kernel(pool[eligible], xx)
                timings["gp_kernel_construction_seconds"] += time.perf_counter() - t
                t = time.perf_counter()
                coeff, sets, failure = safe_action_sets(matrix, cross, y, pending_lower)
                timings["gp_coefficients_and_outer_sets_seconds"] += time.perf_counter() - t
                stats["inverse_gate_failures"] += int(failure is not None)
                stats["first_action_branches"] += 1
                record = {"eligible_pool_indices": eligible.tolist(), "pending_lower": pending_lower,
                    "inverse_gate_failure": failure, "first_response_exposed": False,
                    "matrix_sha256": sha(matrix.tobytes()), "cross_sha256": sha(cross.tobytes()),
                    "sets": {m: save_set(s) for m, s in sets.items()},
                    "coefficients": None if coeff is None else {k: v.tolist() if isinstance(v, np.ndarray) else v for k, v in coeff.items()}}
                t = time.perf_counter()
                for mode, row in record["sets"].items():
                    stats["exclusion_proofs_verified"] += verify_set(row, len(eligible), 0. if mode == "nonnegative" else pending_lower)
                    stats["unresolved_exclusions_retained"] += row["unresolved_exclusions_retained"]
                timings["independent_rational_recheck_seconds"] += time.perf_counter() - t
                branches[branch] = record
            item = {"metadata": meta, "pool_seed": seed, "raw_pool_sha256": sha(pool.tobytes()),
                    "raw_pool_lowers": raw_lowers, "branches": branches, "future_responses_exposed": False}
            name = meta["dataset"] + "__" + meta["state"] + ".json"
            write(target / name, item); files[name] = sha((target / name).read_bytes())
            stats["nontrivial_states"] += 1
            log({"event": "state_constructed", "state": meta["state"], "dataset": meta["dataset"],
                 "unique_bound_designs": stats["unique_bound_designs"], "branches": len(branches),
                 "construction_sha256": files[name], "future_responses_exposed": False})
            print(json.dumps({"constructed_states": stats["nontrivial_states"], "unique_bound_designs": stats["unique_bound_designs"], "branches": stats["first_action_branches"]}), flush=True)
        if (stats["nontrivial_states"], stats["alias_only_states"], stats["first_action_branches"]) != (43, 17, 114):
            raise ValueError("Incomplete declared development groups")
        log({"event": "complete", "future_responses_exposed": False, "new_physics_attempts": 0})
        write(OUT / "construction_status.json", {"complete": True, "baseline_commit": BASELINE,
            "plan_sha256": sha((OUT / "plan.json").read_bytes()), "files_sha256": files,
            "witness_files_sha256": witness_hashes,
            "execution_sources_sha256": {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in source_paths},
            "runtime_versions": {n: importlib.metadata.version(n) for n in ("numpy", "scipy", "scikit-learn", "engibench", "cvxopt")},
            "python": platform.python_version(), "platform": platform.platform(),
            "thread_environment": {n: os.environ.get(n) for n in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")},
            "statistics": dict(stats), "timings": dict(timings), "alias_only_exclusions": exclusions,
            "end_to_end_seconds": time.perf_counter() - start, "new_physics_attempts": 0,
            "new_independent_samples": 0, "future_responses_exposed": False})
    except Exception as error:
        log({"event": "failure", "error": repr(error), "new_physics_attempts": 0})
        write(OUT / "construction_status.json", {"complete": False, "error": repr(error), "statistics": dict(stats), "new_physics_attempts": 0})
        raise
    finally:
        journal.close()


def stored_truth(plan):
    """Called exclusively after every response-blind construction is durable."""
    common = defaultdict(dict); pending = None
    path = ROOT / "results/engineering_optimization_common_continuation_v1/events.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row["event"] == "pre":
            if pending is not None:
                raise ValueError("Unpaired source prediction")
            pending = row
        elif row["event"] == "label":
            if pending is None or any(pending[k] != row[k] for k in ("state", "branch", "step")):
                raise ValueError("Unpaired source response")
            if row["step"] <= 1:
                common[pending["state"]][pending["branch"], pending["step"]] = {**pending, "y": row["y"]}
            pending = None
    if pending is not None:
        raise ValueError("Unpaired final source prediction")
    result = {}
    for meta in plan["mean_states"]:
        if len(meta["classes"]) == 1:
            continue
        if meta["dataset"] == "archived_common_mean":
            records = {b: [common[meta["state"]][b, h] for h in (0, 1)] for b in meta["classes"]}
        else:
            path = ROOT / f"results/engineering_optimization_budget_audit_v1/block_{meta['block']}" / (meta["state"] + "_summary.json")
            raw = json.loads(path.read_text())
            records = {b: raw["trajectories"]["mean"][b][:2] for b in meta["classes"]}
        result[meta["dataset"], meta["state"]] = records
    return result


def exact_truth_category(base, terminal, initial, margin):
    f = Fraction.from_float
    effect = f(float(base)) - f(float(terminal))
    epsilon = f(float(initial)) * f(float(margin))
    return "better" if effect > epsilon else "worse" if effect < -epsilon else "tie"


def conditional_joint_lower(initial, pending_lower, point_lowers, saved_set):
    ids = np.array(saved_set["indices"])
    lower_response = np.zeros(len(point_lowers))
    lower_response[ids] = np.maximum(pending_lower, saved_set["response_lower"])
    return joint_two_response_lower(initial, point_lowers,
        {"indices": ids, "response_lower": lower_response})


def grade():
    plan = gate()
    status = json.loads((OUT / "construction_status.json").read_text())
    if not status["complete"] or status["future_responses_exposed"]:
        raise ValueError("A complete response-blind construction is required")
    for name, digest in status["files_sha256"].items():
        if sha((OUT / "construction" / name).read_bytes()) != digest:
            raise ValueError("Construction changed before grading")
    for name, digest in status["witness_files_sha256"].items():
        if sha((OUT / name).read_bytes()) != digest:
            raise ValueError("Witness record changed")
    if (REPORT / "analysis.json").exists():
        raise FileExistsError("Completed grading exists; do not overwrite")
    start = time.perf_counter(); truth = stored_truth(plan)
    rows, proof_count = [], 0
    query_sets = {m: defaultdict(set) for m in (*MODES, "full_pool")}
    requests = Counter(); times = Counter(); state_selection = []
    for name in status["files_sha256"]:
        item = json.loads((OUT / "construction" / name).read_text())
        meta = item["metadata"]; initial = initial_record(meta)
        cfg = plan["pool_configs"][meta["dataset"]]; margin = plan["config"]["original_dataset_margins"][meta["dataset"]]
        key = meta["dataset"], meta["state"]
        records = truth[key]
        baseline = min(meta["initial"], *(r["y"] for r in records[meta["baseline"]]))
        pool, _ = future_pool(meta, 1, plan["pool_configs"])
        lower_by_mode = {m: {} for m in (*MODES, "full_pool")}
        for branch, rec in item["branches"].items():
            eligible = np.array(rec["eligible_pool_indices"])
            lower = np.array([item["raw_pool_lowers"][int(i)] for i in eligible])
            future = records[branch]; z, next_y = (float(r["y"]) for r in future)
            terminal = min(meta["initial"], z, next_y)
            point = np.array(initial["actions"][branch])
            if not np.array_equal(point, np.array(future[0]["x"])):
                raise ValueError("Stored first-action coordinate changed")
            matches = np.flatnonzero(np.all(pool[eligible] == np.array(future[1]["x"]), axis=1))
            if len(matches) != 1:
                raise ValueError("Actual next action is absent from its declared eligible pool")
            actual = int(matches[0]); pending_lower = rec["pending_lower"]
            if z < pending_lower or next_y < lower[actual]:
                raise ValueError("Stored true response violates a used discrete trial bound")
            t = time.perf_counter()
            X, y = np.array(initial["X"]), np.array(initial["y"])
            root = model(X, y, initial["theta"], cfg)
            root_mu, root_sd = root.predict(point[None], return_std=True)
            native = model(np.vstack((X, point)), np.append(y, z), initial["theta"], cfg)
            mu, sd = native.predict(pool[eligible], return_std=True)
            times["post_construction_native_gp_replay_seconds"] += time.perf_counter() - t
            tol = dict(rtol=plan["config"]["gp_replay_relative_tolerance"], atol=plan["config"]["gp_replay_absolute_tolerance"])
            root_replay = bool(np.allclose([root_mu[0], root_sd[0]], [future[0]["mu"], future[0]["sd"]], **tol))
            next_replay = bool(np.allclose([mu[actual], sd[actual]], [future[1]["mu"], future[1]["sd"]], **tol))
            coeff = rec["coefficients"]
            affine_replay = None if coeff is None else bool(np.allclose(mu, np.array(coeff["slope"]) * z + np.array(coeff["intercept"]), **tol))
            for mode in (*MODES, "full_pool"):
                query_sets[mode][key].add(point_key(point)); requests[mode] += 1
            query_sets["full_pool"][key].update(point_key(x) for x in pool[eligible]); requests["full_pool"] += len(eligible)
            full_lower = min(meta["initial"], pending_lower, float(lower.min()))
            lower_by_mode["full_pool"][branch] = full_lower
            full_category = category_from_interval(baseline, meta["initial"], full_lower, meta["initial"], margin)
            for mode, action_set in rec["sets"].items():
                t = time.perf_counter()
                proof_count += verify_set(action_set, len(eligible), 0. if mode == "nonnegative" else pending_lower)
                times["post_serialization_proof_verification_seconds"] += time.perf_counter() - t
                ids = np.array(action_set["indices"])
                # Both readers get the identical pending-point bound. The
                # nonnegative set is the wider set constructed on [0,infinity).
                joint = conditional_joint_lower(meta["initial"], pending_lower, lower, action_set)
                lower_by_mode[mode][branch] = joint
                envelope = float(lower[ids].min())
                category = category_from_interval(baseline, meta["initial"], joint, meta["initial"], margin)
                actual_included = actual in set(ids.tolist())
                native_included = int(np.argmin(mu)) in set(ids.tolist())
                requests[mode] += len(ids)
                query_sets[mode][key].update(point_key(x) for x in pool[eligible[ids]])
                true_category = exact_truth_category(baseline, terminal, meta["initial"], margin)
                interval_valid = joint <= terminal <= meta["initial"]
                row = {"dataset": meta["dataset"], "block": meta["block"], "state": meta["state"],
                    "source": meta["source"], "branch": branch, "range": mode, "baseline_branch": branch == meta["baseline"],
                    "eligible_pool_size": len(eligible), "outer_set_size": len(ids),
                    "excluded_actions": len(action_set["excluded_proofs"]), "actual_next_action_included": actual_included,
                    "native_next_action_included": native_included, "root_source_prediction_replay": root_replay,
                    "next_source_prediction_replay": next_replay, "affine_native_replay": affine_replay,
                    "pending_bound": pending_lower, "full_pool_next_lower_envelope": float(lower.min()),
                    "reachable_next_lower_envelope": envelope, "full_pool_joint_lower": full_lower,
                    "reachable_joint_lower": joint, "completed_H1_baseline": baseline,
                    "initial": meta["initial"], "margin": margin, "full_pool_category": full_category,
                    "reachable_category": category, "actual_H1_category": true_category,
                    "terminal_interval_valid_at_stored_responses": interval_valid,
                    "category_error": category not in ("abstain", true_category),
                    "inverse_gate_fallback": rec["inverse_gate_failure"] is not None}
                rows.append(row)
            # A paid completed baseline's own category is structurally tie;
            # its response-blind interval above is not counted as coverage.
        for mode, lowers in lower_by_mode.items():
            others = [b for b in lowers if b != meta["baseline"]]
            f = Fraction.from_float
            certified = all(f(float(baseline)) <= f(float(lowers[b])) + f(float(margin)) * f(float(meta["initial"])) for b in others)
            state_selection.append({"dataset": meta["dataset"], "state": meta["state"], "reader": mode,
                "baseline_selection_certified": certified, "selected_branch": meta["baseline"],
                "fallback_is_not_a_selection_certificate": not certified,
                "selected_completion_requests_after_paid_H1_baseline": 0})
    summaries = []
    for dataset in sorted({r["dataset"] for r in rows}):
        for mode in MODES:
            rr = [r for r in rows if r["dataset"] == dataset and r["range"] == mode]
            others = [r for r in rr if not r["baseline_branch"]]
            summaries.append({"dataset": dataset, "range": mode, "seed_groups": len({r["block"] for r in rr}),
                "nontrivial_states": len({r["state"] for r in rr}), "first_action_branches": len(rr),
                "eligible_pool_size_median": float(np.median([r["eligible_pool_size"] for r in rr])),
                "outer_set_size_min": min(r["outer_set_size"] for r in rr),
                "outer_set_size_median": float(np.median([r["outer_set_size"] for r in rr])),
                "outer_set_size_max": max(r["outer_set_size"] for r in rr),
                "actual_action_inclusion_failures": sum(not r["actual_next_action_included"] for r in rr),
                "source_prediction_replay_flags": sum(not (r["root_source_prediction_replay"] and r["next_source_prediction_replay"]) or r["affine_native_replay"] is False for r in rr),
                "envelope_improved_branches": sum(r["reachable_next_lower_envelope"] > r["full_pool_next_lower_envelope"] for r in rr),
                "joint_lower_improved_branches": sum(r["reachable_joint_lower"] > r["full_pool_joint_lower"] for r in rr),
                "nonbaseline_contrasts": len(others), "full_pool_category_coverage": sum(r["full_pool_category"] != "abstain" for r in others),
                "reachable_category_coverage": sum(r["reachable_category"] != "abstain" for r in others),
                "category_errors": sum(r["category_error"] for r in others),
                "full_pool_baseline_selection_certified": sum(r["baseline_selection_certified"] for r in state_selection if r["dataset"] == dataset and r["reader"] == "full_pool"),
                "reachable_baseline_selection_certified": sum(r["baseline_selection_certified"] for r in state_selection if r["dataset"] == dataset and r["reader"] == mode)})
    validity = all(r["actual_next_action_included"] and r["native_next_action_included"] and r["terminal_interval_valid_at_stored_responses"] and not r["category_error"] and r["root_source_prediction_replay"] and r["next_source_prediction_replay"] and r["affine_native_replay"] is not False for r in rows)
    useful = any(s["reachable_category_coverage"] > s["full_pool_category_coverage"] or s["reachable_baseline_selection_certified"] > s["full_pool_baseline_selection_certified"] for s in summaries)
    query_accounting = {m: {"logical_bound_queries": requests[m], "unique_designs_within_state_cache": sum(len(v) for v in query_sets[m].values()),
        "within_state_cache_hits": requests[m] - sum(len(v) for v in query_sets[m].values()), "counterfactual_not_realized_savings": m != "full_pool"} for m in query_sets}
    analysis = {"baseline_commit": BASELINE, "protocol_commit": BASELINE, "complete": True,
        "analysis_type": "development on all previously observed complete seed groups",
        "H1_definition": "first action plus one posterior-mean continuation; comparator baseline completed at the identical H1 horizon",
        "H5_reachable_history_extension": False, "all_states_retained": 60, "alias_only_exclusions": 17,
        "nontrivial_mean_contexts": 43, "first_action_branches": 114, "new_gp_hyperparameter_fits": 0,
        "validation_passed_at_stored_responses": validity, "proofs_rechecked_after_serialization": proof_count,
        "group_summaries": summaries, "counterfactual_query_accounting": query_accounting,
        "construction_statistics": status["statistics"], "construction_timings": status["timings"],
        "construction_end_to_end_seconds": status["end_to_end_seconds"], "grading_timings": dict(times),
        "grading_end_to_end_seconds": time.perf_counter() - start,
        "new_physics_attempts_GP_phase": 0, "new_physics_attempts_witness_phase": 2,
        "total_new_physics_attempts_this_protocol": 2, "project_cumulative_physics_attempts": 55309,
        "new_independent_samples": 0, "new_optimization_samples": 0, "retries": 0, "replacements": 0,
        "historical_first_and_next_response_record_reads": 228,
        "full_pool_library_acquired_in_this_study": True,
        "complete_cost_benefit_demonstrated": False,
        "complete_cost_reason": "Both readers share the same acquired full-pool bound library; GP construction and proof work are additional executed costs. Offline subset counts do not demonstrate a deployment saving. The H1 baseline is already paid; fallback completes no extra selected responses and does not certify selection.",
        "engineering_or_PDE_error_certified": False,
        "native_predictions_for_all_possible_responses_certified": False,
        "transcendental_kernel_error_certified": False,
        "useful_downstream_judgment_increment": useful,
        "start_new_independent_optimization_experiment": False, "submission_ready": False,
        "independent_gate": {"stored_response_validation": validity, "downstream_judgment_increment": useful,
            "complete_cost_benefit": False, "H5_reachable_history_extension": False, "passed": False},
        "construction_status_sha256": sha((OUT / "construction_status.json").read_bytes()),
        "frozen_plan_sha256": sha((OUT / "plan.json").read_bytes()),
        "runtime_versions": status["runtime_versions"]}
    REPORT.mkdir(exist_ok=True)
    for name, data in (("branch_results.csv", rows), ("summary.csv", summaries), ("state_selection.csv", state_selection)):
        with (REPORT / name).open("x", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(data[0]), lineterminator="\n")
            writer.writeheader(); writer.writerows(data)
    write(REPORT / "analysis.json", analysis)
    print(json.dumps({"validation_passed": validity, "groups": summaries,
        "query_accounting": query_accounting, "independent_study_gate_passed": False}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("construct", "grade"))
    args = parser.parse_args()
    construct() if args.mode == "construct" else grade()
