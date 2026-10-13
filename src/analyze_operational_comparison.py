"""Retrospective same-target comparators; no new physical or GP evaluations.

Named and exact-class full-horizon readers are transparent implementation
baselines, not replications of published algorithms. The strongest simple
class-aware fixed-depth comparator is exactly the frozen v1 audit. No superiority
over it is claimed. Alias-aware calibration is a post hoc cost sensitivity.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from .budgeted_decision_audit import Observation, audit, calibration_rule, classify

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "paper/engineering_optimization/submission_revision_20261013"
CONTROLS = ["mean", "ei", "pi", "lcb"]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_named(state, continuation, budget, margin):
    """Ignore first-action aliases, but retain the same target and prefix rule."""
    curves = state["trajectories"][continuation]
    exposed = {name: -1 for name in CONTROLS}

    def observe(name, step):
        if step != exposed[name] + 1:
            raise AssertionError("Non-prefix access")
        exposed[name] = step
        r = curves[state["mapping"][name]][step]
        return Observation(r["incumbent"], r["point_key"])

    return audit({name: [name] for name in CONTROLS}, "mean", observe,
                 state["initial_best"], {n: state["root_sd"][state["mapping"][n]] for n in CONTROLS},
                 mode="fixed_depth", budget=budget, margin=margin)


def read_grouped_full(state, continuation, margin):
    """Read each exact class to H, including the sole class of alias-only states."""
    curves = state["trajectories"][continuation]
    baseline = state["mapping"]["mean"]
    trace, labels, effects = [], {}, {}
    for branch, names in state["classes"].items():
        for step, r in enumerate(curves[branch]):
            trace.append({"branch": branch, "step": step, "point_key": r["point_key"]})
        effect = (curves[baseline][5]["incumbent"] - curves[branch][5]["incumbent"]) / state["initial_best"]
        for name in names:
            labels[name], effects[name] = classify(effect, margin), effect
    return {"labels": labels, "effects": effects, "requests": len(trace), "trace": trace}


def read_grouped(state, continuation, budget, margin, mode):
    curves = state["trajectories"][continuation]
    exposed = {b: -1 for b in curves}

    def observe(branch, step):
        if step != exposed[branch] + 1:
            raise AssertionError("Non-prefix access")
        exposed[branch] = step
        r = curves[branch][step]
        return Observation(r["incumbent"], r["point_key"])

    return audit(state["classes"], state["mapping"]["mean"], observe,
                 state["initial_best"], state["root_sd"], budget=budget,
                 margin=margin, mode=mode)


def calibration(state, cfg, skip_alias_only=False):
    labels = calibration_rule(state["classes"], state["mapping"]["mean"],
                              state["root_ei"], state["calibration"]["nrmse"],
                              state["calibration"]["coverage90"], cfg)
    effects = {n: state["root_ei"][b] - state["root_ei"][state["mapping"]["mean"]]
               for b, names in state["classes"].items() for n in names}
    # Alias-only outputs do not depend on probe results. This variant is post hoc.
    requests = 0 if skip_alias_only and len(state["classes"]) == 1 else cfg["calibration_points"]
    return {"labels": labels, "effects": effects, "requests": requests, "trace": []}


def assess(state, continuation, result, margin):
    curves = state["trajectories"][continuation]
    baseline = state["mapping"]["mean"]
    comparisons = []
    # Access complete truth only after each sequential reader has finished.
    for branch, names in state["classes"].items():
        if branch == baseline:
            continue
        truth = classify((curves[baseline][5]["incumbent"] - curves[branch][5]["incumbent"])
                         / state["initial_best"], margin)
        pred = result["labels"][names[0]]
        comparisons.append({"classified": pred != "abstain", "error": pred != "abstain" and pred != truth})
    chosen, best = "mean", margin
    for name in CONTROLS[1:]:
        if result["labels"][name] == "better" and result["effects"][name] > best:
            chosen, best = name, result["effects"][name]
    endpoint = curves[state["mapping"][chosen]][5]["incumbent"]
    oracle = min(c[5]["incumbent"] for c in curves.values())
    return {"contrasts": len(comparisons), "classified": sum(r["classified"] for r in comparisons),
            "errors": sum(r["error"] for r in comparisons), "requests": result["requests"],
            "selection_loss_percent": 100 * (endpoint - oracle) / state["initial_best"],
            "labels": result["labels"], "chosen": chosen}


def csv_write(path, rows):
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main():
    reference = json.loads((ROOT / "paper/engineering_optimization/review_revision/analysis.json").read_text())
    for p, digest in reference["source_files_sha256"].items():
        assert sha((ROOT / p).read_bytes()) == digest, p
    cfg = json.loads((ROOT / "configs/engineering_optimization_budget_audit.json").read_text())
    raw = ROOT / cfg["out"]
    states = []
    for block in cfg["seed_blocks"]:
        done = json.loads((raw / f"block_{block}/complete.json").read_text())
        for name in done["states"]:
            states.append(json.loads((raw / f"block_{block}/{name}_summary.json").read_text()))
    groups, detail = defaultdict(list), []
    for s in states:
        for c in cfg["continuations"]:
            margin = cfg["relative_margin"]
            measurements = {
                "named_full_horizon": read_named(s, c, 24, margin),
                "exact_class_full_horizon": read_grouped_full(s, c, margin),
                "calibration_original": calibration(s, cfg),
                "calibration_skip_alias_posthoc": calibration(s, cfg, True),
            }
            for budget in cfg["budget_sensitivity"]:
                measurements[f"named_depth_B{budget}"] = read_named(s, c, budget, margin)
                for mode in ["fixed_depth", "adaptive", "immediate"]:
                    measurements[f"{mode}_v1_B{budget}"] = read_grouped(s, c, budget, margin, mode)
            full = measurements["named_full_horizon"]
            assert full["labels"] == measurements["exact_class_full_horizon"]["labels"]
            assert full["labels"] == measurements["fixed_depth_v1_B18"]["labels"]
            assert measurements["calibration_original"]["labels"] == measurements["calibration_skip_alias_posthoc"]["labels"]
            for method, result in measurements.items():
                row = {"block": s["block"], "state": s["state"], "continuation": c,
                       "method": method, "classes": len(s["classes"]), **assess(s, c, result, margin)}
                groups[c, method].append(row)
                detail.append({k: v for k, v in row.items() if k != "labels"})
    summary = []
    for (c, method), rows in sorted(groups.items()):
        summary.append({"continuation": c, "method": method, "seed_blocks": 10, "dependent_states": 30,
                        **{k: sum(r[k] for r in rows) for k in ["contrasts", "classified", "errors", "requests"]},
                        "mean_state_selection_loss_percent": sum(r["selection_loss_percent"] for r in rows) / 30})
    primary = [r for r in summary if r["method"] in {"named_full_horizon", "exact_class_full_horizon",
               "fixed_depth_v1_B18", "adaptive_v1_B18", "immediate_v1_B18", "calibration_original", "calibration_skip_alias_posthoc"}]
    for c in cfg["continuations"]:
        get = lambda m: next(r for r in primary if r["continuation"] == c and r["method"] == m)
        assert [get(m)["requests"] for m in ["named_full_horizon", "exact_class_full_horizon", "fixed_depth_v1_B18", "calibration_original", "calibration_skip_alias_posthoc"]] == [720, 330, 252, 240, 136]
        for m in ["fixed_depth", "adaptive", "immediate"]:
            old = next(r for r in json.loads((ROOT / "paper/engineering_optimization/budget_audit/analysis.json").read_text())["primary"] if r["continuation"] == c and r["method"] == m)
            assert get(m + "_v1_B18")["classified"] == old["classified"]
            assert get(m + "_v1_B18")["requests"] == old["total_audit_requests"]
            assert get(m + "_v1_B18")["errors"] == old["classification_error"]
    DEST.mkdir(parents=True, exist_ok=True)
    report = {"analysis_type": "post hoc operational comparison, not independent validation",
              "new_physics_attempts": 0, "published_algorithm_replication": False,
              "fixed_depth_is_existing_strong_simple_baseline": True,
              "advantage_over_fixed_depth_demonstrated": False,
              "request_reuse_is_known_practice_not_new_optimization_theory": True,
              "request_reductions_are_not_paid_solver_or_deployment_savings": True,
              "all_full_target_named_labels_identical": True,
              "class_aware_calibration_skip_preserves_labels": True,
              "class_aware_calibration_variant_preregistered": False,
              "source_files_sha256": reference["source_files_sha256"], "primary": primary, "sensitivity": summary}
    (DEST / "operational_comparison.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    csv_write(DEST / "operational_comparison.csv", summary)
    csv_write(DEST / "operational_state_results.csv", detail)
    print(json.dumps({"states": len(states), "comparators": len(summary), "new_physics_attempts": 0,
                      "full_target_requests": [720, 330, 252], "calibration_requests": [240, 136]}))


if __name__ == "__main__":
    main()
