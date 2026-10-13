"""Development replay of a bound operation on already observed complete blocks.

No physics or GP fit is performed. Previously independent holdout data are now
development data for this NEW rule. No new confirmatory statistical family is
created. Prefix readers are isolated from grading and completion accounting.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import struct
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

from .budgeted_decision_audit import Observation, audit as v1_audit, classify
from .monotone_horizon_audit import audit, selection_certificate

ROOT = Path(__file__).resolve().parents[1]
CONFIG = "configs/engineering_optimization_monotone_development.json"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def point_key(x):
    return struct.pack("<" + "d" * len(x), *x).hex()


def load_sources(root):
    sources, cases = {}, []

    def read(path, expected=None, *, parse=True):
        data = (root / path).read_bytes()
        digest = sha(data)
        if expected is not None and digest != expected:
            raise ValueError(f"Changed source: {path}")
        sources[path] = digest
        return json.loads(data) if parse else data

    reference = read("paper/engineering_optimization/review_revision/analysis.json")
    for path, digest in reference["source_files_sha256"].items():
        read(path, digest, parse=False)
    cfg = read("configs/engineering_optimization_budget_audit.json")
    for block in cfg["seed_blocks"]:
        folder = cfg["out"] + f"/block_{block}"
        done = read(folder + "/complete.json")
        for name in done["states"]:
            state = read(folder + f"/{name}_summary.json")
            for continuation in cfg["continuations"]:
                cases.append({"dataset": "previous_holdout", "block": block, "state": name,
                              "source": state["source"], "continuation": continuation,
                              "classes": state["classes"], "baseline": state["mapping"]["mean"],
                              "initial": state["initial_best"], "X": state["X"],
                              "curves": state["trajectories"][continuation]})

    archive = read("data/engineering_optimization_common_continuation_v1/manifest.json")
    # Verify the exact raw bytes against the published lossless-release manifest.
    for item in archive["files"]:
        path = item["path"]
        data = (root / path).read_bytes()
        if sha(data) != item["sha256"] or len(data) != item["bytes"]:
            raise ValueError(f"Changed archive source: {path}")
        sources[path] = item["sha256"]
    folder = "results/engineering_optimization_common_continuation_v1"
    manifest = read(folder + "/manifest.json")
    pending, records = None, defaultdict(list)
    for line in (root / folder / "events.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row["event"] == "pre":
            if pending is not None:
                raise ValueError("Unpaired archived prediction")
            pending = row
        elif row["event"] == "label":
            if pending is None or any(row[k] != pending[k] for k in ["state", "branch", "step"]):
                raise ValueError("Mismatched archived response")
            records[row["state"], row["branch"]].append(
                {"step": row["step"], "y": row["y"], "x": pending["x"],
                 "point_key": "archive_fixed_beam:" + point_key(pending["x"])})
            pending = None
    if pending is not None:
        raise ValueError("Unpaired final archived prediction")
    for item in manifest["plans"]:
        p = read(folder + "/" + item["path"], item["sha256"])
        summary = read(folder + f"/summaries/{p['state']}.json")
        classes = {b: [n for n in nn if n != "mean_common_shift"]
                   for b, nn in p["decision_classes"].items()}
        curves = {}
        for b in classes:
            curve = records[p["state"], b]
            if [r["step"] for r in curve] != list(range(6)):
                raise ValueError("Non-prefix archived branch")
            incumbent = p["initial_best"]
            for r in curve:
                incumbent = min(incumbent, r["y"])
                r["incumbent"] = incumbent
            if [r["incumbent"] for r in curve] != summary["branch_records"][b]["curve"]:
                raise ValueError("Archived curve mismatch")
            curves[b] = curve
        cases.append({"dataset": "archived_common_mean", "block": p["rep"], "state": p["state"],
                      "source": p["method"], "continuation": "mean", "classes": classes,
                      "baseline": str(p["decisions"]["mean"]), "initial": p["initial_best"],
                      "X": p["X"], "curves": curves})
    if len(cases) != 90:
        raise ValueError("Missing complete development cases")
    return cases, sources


def read_prefix(case, mode, budget, margin, *, horizon=5, lower_bound=0., order=None,
                target="categories"):
    exposed = {b: -1 for b in case["classes"]}

    def observe(branch, step):
        if step != exposed[branch] + 1:
            raise AssertionError("Non-prefix observation access")
        exposed[branch] = step
        record = case["curves"][branch][step]
        return Observation(record["incumbent"], record["point_key"])

    if mode == "v1_fixed_depth":
        result = v1_audit(case["classes"], case["baseline"], observe, case["initial"],
                          {b: 0. for b in case["classes"]}, mode="fixed_depth",
                          horizon=horizon, budget=budget, margin=margin)
        result["branch_labels"] = {b: result["labels"][nn[0]] for b, nn in case["classes"].items()}
        result["all_categories_certified"] = all(x != "abstain" for x in result["branch_labels"].values())
        result["terminal_bounds"] = {
            b: (case["curves"][b][horizon]["incumbent"],) * 2 if result["depth"][b] == horizon
            else (lower_bound, case["curves"][b][result["depth"][b]]["incumbent"]
                  if result["depth"][b] >= 0 else case["initial"])
            for b in case["classes"]}
        return result
    return audit(case["classes"], case["baseline"], observe, case["initial"],
                 mode=mode, horizon=horizon, budget=budget, margin=margin,
                 lower_bound=lower_bound, order=order, target=target)


def assess(case, result, margin, *, horizon=5):
    """Truth and selected completion are accessed AFTER the reader returns."""
    curves, baseline, initial = case["curves"], case["baseline"], case["initial"]
    truth = {b: classify((curves[baseline][horizon]["incumbent"] - rr[horizon]["incumbent"]) / initial, margin)
             for b, rr in curves.items()}
    others = [b for b in case["classes"] if b != baseline]
    pred = result["branch_labels"]
    branch_order = [baseline] + others
    if "selection" in result:
        selected_info = result["selection"]
        chosen = selected_info["branch"] if selected_info["certified"] else baseline
        selection_certified = selected_info["certified"]
    else:
        # The original v1 selection rule uses measured effects only.
        chosen, best = baseline, margin
        mapping = {n: b for b, nn in case["classes"].items() for n in nn}
        for name in ["ei", "pi", "lcb"]:
            if result["labels"][name] == "better" and result["effects"][name] > best:
                chosen, best = mapping[name], result["effects"][name]
        certificate = selection_certificate(result["terminal_bounds"], branch_order, initial, margin)
        selection_certified = certificate["certified"] and certificate["branch"] == chosen
    completion = [{"branch": chosen, "step": step, "point_key": curves[chosen][step]["point_key"]}
                  for step in range(result["depth"][chosen] + 1, horizon + 1)]
    training = {point_key(x) for x in case["X"]}
    observed = {r["point_key"].split(":", 1)[1] for r in result["trace"]}
    completed = observed | {r["point_key"].split(":", 1)[1] for r in completion}
    endpoint = curves[chosen][horizon]["incumbent"]
    loss = 100 * (endpoint - min(rr[horizon]["incumbent"] for rr in curves.values())) / initial
    if selection_certified and loss > margin * 100 + 1e-12:
        raise AssertionError("Invalid selected-branch certificate")
    chosen_upper = result["terminal_bounds"][chosen][1]
    if selection_certified and chosen_upper > margin * initial:
        # With lower bound zero, an unfinished competitor has L_i=0 and
        # cannot satisfy U_chosen <= L_i + tau*initial. Therefore all other
        # classes must finish; selected completion restores K*(H+1) requests.
        if any(result["depth"][b] != horizon for b in case["classes"] if b != chosen):
            raise AssertionError("Invalid zero-bound selection capacity")
        if result["requests"] + len(completion) != len(case["classes"]) * (horizon + 1):
            raise AssertionError("Selected completion accounting mismatch")
    metrics = {"contrasts": len(others),
               "classified": sum(pred[b] != "abstain" for b in others),
               "abstained": sum(pred[b] == "abstain" for b in others),
               "classification_errors": sum(pred[b] not in {"abstain", truth[b]} for b in others),
               "false_adoptions": sum(pred[b] == "better" and truth[b] != "better" for b in others),
               "false_eliminations": sum(pred[b] in {"tie", "worse"} and truth[b] == "better" for b in others),
               "abstained_positives": sum(pred[b] == "abstain" and truth[b] == "better" for b in others),
               "early_certificates": sum(pred[b] != "abstain" and
                                         (result["depth"][baseline] < horizon or result["depth"][b] < horizon)
                                         for b in others),
               "all_categories_certified": int(result["all_categories_certified"]),
               "nontrivial_state": int(bool(others)),
               "requests": result["requests"], "selected_completion_requests": len(completion),
               "audit_plus_selected_completion_requests": result["requests"] + len(completion),
               "nontrivial_audit_plus_selected_completion_requests": result["requests"] + len(completion) if others else 0,
               "alias_only_selected_execution_requests": len(completion) if not others else 0,
               "statewise_distinct_points_absent_training": len(observed - training),
               "statewise_distinct_points_after_selected_completion": len(completed - training),
               "selection_certified": int(selection_certified),
               "certified_nontrivial_selection": int(selection_certified and bool(others)),
               "chosen": chosen, "selection_loss_percent": loss,
               "truth_better": sum(truth[b] == "better" for b in others),
               "truth_tie": sum(truth[b] == "tie" for b in others),
               "truth_worse": sum(truth[b] == "worse" for b in others)}
    return metrics, truth, completion


def aggregate(rows):
    excluded = {"dataset", "continuation", "method", "target", "budget", "block", "state", "source",
                "classes", "margin", "chosen", "selection_loss_percent"}
    numeric = [k for k in rows[0] if k not in excluded]
    return {"seed_blocks": len({r["block"] for r in rows}), "dependent_states": len(rows),
            **{k: sum(r[k] for r in rows) for k in numeric},
            "mean_state_selection_loss_percent": sum(r["selection_loss_percent"] for r in rows) / len(rows),
            "max_state_selection_loss_percent": max(r["selection_loss_percent"] for r in rows)}


def csv_write(path, rows):
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    cfg = json.loads((ROOT / CONFIG).read_text())
    cases, sources = load_sources(ROOT)
    sources[CONFIG] = sha((ROOT / CONFIG).read_bytes())
    for p in ["src/monotone_horizon_audit.py", "src/analyze_monotone_development.py",
              "src/package_monotone_development.py"]:
        sources[p] = sha((ROOT / p).read_bytes())
    rows, certificate_records, oracle_rows = [], [], []
    for case in sorted(cases, key=lambda r: (r["dataset"], r["continuation"], r["block"], r["state"])):
        margin = cfg["dataset_margins"][case["dataset"]]
        for target, budget in itertools.product(cfg["targets"], cfg["budgets"]):
            for method in cfg["methods"]:
                result = read_prefix(case, method, budget, margin, horizon=cfg["horizon"],
                                     lower_bound=cfg["known_objective_lower_bound"], target=target)
                metrics, truth, completion = assess(case, result, margin, horizon=cfg["horizon"])
                row = {"dataset": case["dataset"], "continuation": case["continuation"],
                       "block": case["block"], "state": case["state"], "source": case["source"],
                       "method": method, "target": target, "budget": budget, "margin": margin,
                       "classes": len(case["classes"]), **metrics}
                rows.append(row)
                if metrics["classification_errors"]:
                    raise AssertionError("Unsound category certificate")
                if (budget == 18 and method != "v1_fixed_depth" and
                        (metrics["early_certificates"] or
                         (metrics["all_categories_certified"] and not metrics["selection_certified"]))):
                    certificate_records.append({"dataset": case["dataset"], "continuation": case["continuation"],
                        "block": case["block"], "state": case["state"], "method": method,
                        "target": target,
                        "depth": result["depth"], "terminal_bounds": result["terminal_bounds"],
                        "branch_labels": result["branch_labels"], "truth": truth,
                        "named_effect_intervals": result["effect_intervals"],
                        "named_measured_effects": result["measured_effects"],
                        "chosen": metrics["chosen"], "selection": result["selection"],
                        "requests": result["requests"], "completion_requests": len(completion),
                        "prefix_reads": [{k: r[k] for k in ["branch", "step", "incumbent"]}
                                         for r in result["trace"]]})
            # A response-informed order envelope is NOT an executable baseline.
            permutations = []
            for order in itertools.permutations(case["classes"]):
                result = read_prefix(case, "ordered_depth", budget, margin, order=order, target=target)
                metrics, _, _ = assess(case, result, margin)
                permutations.append(metrics)
            greatest = max(r["classified"] for r in permutations)
            oracle_rows.append({"dataset": case["dataset"], "continuation": case["continuation"],
                               "block": case["block"], "state": case["state"], "budget": budget,
                               "target": target,
                               "maximum_order_coverage_posthoc": greatest,
                               "minimum_requests_at_maximum_coverage_posthoc": min(r["requests"] for r in permutations if r["classified"] == greatest),
                               "minimum_audit_plus_selected_completion_at_maximum_coverage_posthoc": min(r["audit_plus_selected_completion_requests"] for r in permutations if r["classified"] == greatest)})
    grouped, blocks = defaultdict(list), defaultdict(list)
    for row in rows:
        key = row["dataset"], row["continuation"], row["method"], row["budget"], row["target"]
        grouped[key].append(row)
        blocks[key + (row["block"],)].append(row)
    summary = [{"dataset": key[0], "continuation": key[1], "method": key[2], "budget": key[3], "target": key[4], **aggregate(rr)}
               for key, rr in sorted(grouped.items())]
    block_summary = [{"dataset": key[0], "continuation": key[1], "method": key[2], "budget": key[3],
                      "target": key[4], "block": key[5], **aggregate(rr)} for key, rr in sorted(blocks.items())]
    primary = [r for r in summary if r["budget"] == 18 and r["target"] == cfg["primary_target"]]
    screening = []
    for dataset, continuation in sorted({(r["dataset"], r["continuation"]) for r in primary}):
        pool = [r for r in primary if r["dataset"] == dataset and r["continuation"] == continuation]
        candidate = next(r for r in pool if r["method"] == cfg["candidate"])
        simple = [r for r in pool if r["method"] in cfg["strong_simple_methods"]]
        most_covered = max(r["classified"] for r in simple)
        best_simple = min((r for r in simple if r["classified"] == most_covered),
                          key=lambda r: (r["audit_plus_selected_completion_requests"], r["mean_state_selection_loss_percent"], r["method"]))
        gain = 1 - candidate["audit_plus_selected_completion_requests"] / best_simple["audit_plus_selected_completion_requests"]
        screening.append({"dataset": dataset, "continuation": continuation,
                          "candidate": cfg["candidate"], "best_simple_descriptive": best_simple["method"],
                          "simple_selection_is_posthoc_descriptive_not_preregistered": True,
                          "candidate_classified": candidate["classified"], "simple_classified": best_simple["classified"],
                          "candidate_requests": candidate["requests"], "simple_requests": best_simple["requests"],
                          "candidate_audit_plus_selected_completion": candidate["audit_plus_selected_completion_requests"],
                          "simple_audit_plus_selected_completion": best_simple["audit_plus_selected_completion_requests"],
                          "relative_request_gain_after_selected_completion": gain,
                          "passes_development_screen": candidate["classified"] >= best_simple["classified"]
                            and gain >= cfg["development_screen"]["minimum_relative_request_gain_after_selected_completion"]
                            and candidate["mean_state_selection_loss_percent"] <= best_simple["mean_state_selection_loss_percent"]
                            and candidate["classification_errors"] == 0})
    holdout_screen = [r for r in screening if r["dataset"] == "previous_holdout"]
    go = all(r["passes_development_screen"] for r in holdout_screen)
    tie_bound_requirements = []
    for dataset, continuation in sorted({(r["dataset"], r["continuation"]) for r in cases}):
        ratios = []
        for case in cases:
            if (case["dataset"], case["continuation"]) != (dataset, continuation):
                continue
            base = case["curves"][case["baseline"]][cfg["horizon"]]["incumbent"]
            margin = cfg["dataset_margins"][dataset]
            for b, rr in case["curves"].items():
                if b != case["baseline"] and classify((base - rr[5]["incumbent"]) / case["initial"], margin) == "tie":
                    ratios.append(100 * max(0., base - margin * case["initial"]) / base)
        tie_bound_requirements.append({"dataset": dataset, "continuation": continuation,
            "unique_tie_contrasts": len(ratios),
            "minimum_required_lower_bound_percent_of_completed_baseline_endpoint": min(ratios),
            "median_required_lower_bound_percent_of_completed_baseline_endpoint": median(ratios),
            "maximum_required_lower_bound_percent_of_completed_baseline_endpoint": max(ratios),
            "retrospective_diagnostic_not_an_available_online_bound": True})
    report = {"analysis_type": "development replay on all previously observed seed groups",
              "new_independent_validation": False, "new_physics_attempts": 0, "new_gp_fits": 0,
              "gp_fit_count_scope": "Development replay and new experiment acquisition; legacy unit tests separately use synthetic GP fixtures.",
              "all_old_labels_and_original_primary_margins_preserved": True,
              "previous_holdout_is_development_data_for_this_rule": True,
              "independent_unit": "complete seed group; nested source states/controls remain dependent",
              "physical_error_bound_or_engineering_margin_certified": False,
              "lower_bound_assumption": "All reachable recorded deterministic compliance responses are nonnegative; incumbent is nonincreasing.",
              "certificate_is_terminal_category_not_measured_terminal_effect": True,
              "known_bound_operation_is_not_new_optimization_theory": True,
              "zero_bound_selection_capacity_scope": "If the certified selected upper bound exceeds tau*initial, all competing classes must be complete; selected completion costs K*(H+1) branch-step requests. This is not a paid-solver or general-audit lower bound.",
              "statewise_distinct_points_are_not_paid_solver_attempts": True,
              "selected_completion_includes_six_common_execution_requests_for_each_alias_only_state": True,
              "selection_fallback_when_uncertified": "baseline branch; not a selection certificate",
              "posthoc_order_envelope_is_not_deployable": True,
              "certificate_records_scope": "All B18 early category certificates and category-complete/selection-unresolved cases; complete measured pairs are reproducible from the hashed sources.",
              "source_files_sha256": sources, "primary": primary, "sensitivity": summary,
              "development_screen": screening,
              "tie_lower_bound_sharpness_diagnostic": tie_bound_requirements,
              "start_new_independent_validation": go,
              "submission_ready": False}
    dest = args.output or ROOT / cfg["out"]
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "analysis.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    csv_write(dest / "summary.csv", summary)
    csv_write(dest / "state_results.csv", rows)
    csv_write(dest / "seed_group_results.csv", block_summary)
    csv_write(dest / "posthoc_order_envelope.csv", oracle_rows)
    (dest / "certificate_records.jsonl").write_text("".join(json.dumps(r, separators=(",", ":"), allow_nan=False) + "\n" for r in certificate_records))
    print(json.dumps({"source_hashes_verified": len(sources), "development_context_states": len(cases),
                      "new_physics_attempts": 0, "screen": screening, "start_independent_validation": go}))


if __name__ == "__main__":
    main()
