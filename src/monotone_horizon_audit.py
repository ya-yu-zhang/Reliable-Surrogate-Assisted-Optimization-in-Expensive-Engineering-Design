"""Prefix-only certificates for a nonincreasing minimization incumbent.

This is an elementary deterministic bound, not a GP confidence interval or a
new optimization theorem. It certifies a terminal CATEGORY, not an unobserved
terminal effect. A supplied lower bound must hold for every reachable response.
The frozen v1 full-depth audit is left unchanged.
"""
from __future__ import annotations

import math

from .budgeted_decision_audit import classify


def effect_interval(base, alternative, initial, *, measured=False):
    """Enclose (base_H - alternative_H) / initial using outward rounding.

    Complete pairs retain the original recorded-float classifier. Partial
    certificates are conservative relative to exact arithmetic on stored floats.
    """
    if measured:
        effect = (base[0] - alternative[0]) / initial
        return effect, effect
    low = math.nextafter(base[0] - alternative[1], -math.inf)
    high = math.nextafter(base[1] - alternative[0], math.inf)
    return (math.nextafter(low / initial, -math.inf),
            math.nextafter(high / initial, math.inf))


def certify(interval, margin):
    low, high = interval
    if low > margin:
        return "better"
    if high < -margin:
        return "worse"
    if low >= -margin and high <= margin:
        return "tie"
    return "abstain"


def selection_certificate(bounds, branch_order, initial, margin):
    """A branch whose worst endpoint is within tau of every other's best.

    This proves the selected branch is tau-optimal IF continued to H. It does
    not finish that branch or establish its terminal objective value.
    """
    chosen = min(branch_order, key=lambda b: (bounds[b][1], branch_order.index(b)))
    eps = margin * initial
    # The lower sum bound avoids falsely accepting a near-boundary selection.
    eps_lower = math.nextafter(eps, -math.inf) if eps else 0.0
    proved = all(
        bounds[chosen][1] <= (math.nextafter(bounds[b][0] + eps_lower, -math.inf)
                             if eps else bounds[b][0])
        for b in branch_order if b != chosen)
    return {"branch": chosen, "certified": proved,
            "reason": "bounded_tau_optimal_if_completed" if proved else "insufficient_terminal_bounds"}


def audit(classes, baseline, observe, initial, *, horizon=5, budget=18,
          margin=0.001, lower_bound=0.0, mode="baseline_depth", order=None,
          target="categories"):
    """Read only next-prefix records, checking safe categories after each read.

    Named aliases must have exactly the same state, action, GP history and
    continuation context. The caller, not numerical outcome equality, supplies
    these classes. Every observation request is charged, including cache reads.

    The h0_largest_upper schedule reads all first actions, finishes the branch
    with the largest observed incumbent, then follows baseline-first order. It
    is a development heuristic, not a certified priority score. The joint target
    continues after category certification when branch selection is unresolved.
    """
    if (not classes or baseline not in classes or not math.isfinite(initial) or initial <= 0
            or not math.isfinite(lower_bound) or lower_bound > initial
            or not math.isfinite(margin) or margin < 0
            or not isinstance(horizon, int) or horizon < 0
            or not isinstance(budget, int) or budget < 0):
        raise ValueError("Invalid audit design")
    names = [n for nn in classes.values() for n in nn]
    if any(not nn for nn in classes.values()) or len(set(names)) != len(names):
        raise ValueError("Classes must be nonempty and disjoint")
    if mode not in {"baseline_depth", "alternative_depth", "fixed_breadth",
                    "h0_largest_upper", "ordered_depth"}:
        raise ValueError("Unknown audit mode")
    if target not in {"categories", "categories_and_selection"}:
        raise ValueError("Unknown audit target")
    branches = [baseline] + [b for b in classes if b != baseline]
    others = branches[1:]
    if mode == "ordered_depth" and (order is None or len(order) != len(branches)
                                    or set(order) != set(branches)):
        raise ValueError("Ordered depth requires a complete branch permutation")
    depth = {b: -1 for b in branches}
    latest = {b: initial for b in branches}
    trace = []
    seen = set()

    def current():
        bounds = {b: (latest[b], latest[b]) if depth[b] == horizon
                  else (lower_bound, latest[b]) for b in branches}
        labels, reasons, intervals, effects = {}, {}, {}, {}
        for b in branches:
            if b == baseline:
                labels[b], reasons[b], intervals[b], effects[b] = (
                    "tie", "exact_same_action_and_continuation", (0., 0.), 0.)
                continue
            measured = depth[baseline] == horizon and depth[b] == horizon
            interval = effect_interval(bounds[baseline], bounds[b], initial, measured=measured)
            label = classify(interval[0], margin) if measured else certify(interval, margin)
            reason = ("measured_target_horizon" if measured else
                      "monotone_terminal_category_bound" if label != "abstain" else
                      "insufficient_terminal_bounds")
            labels[b], reasons[b], intervals[b] = label, reason, interval
            effects[b] = interval[0] if measured else None
        return bounds, labels, reasons, intervals, effects

    def done():
        bounds, labels, *_ = current()
        categories_done = all(labels[b] != "abstain" for b in others)
        return categories_done and (target == "categories" or
            selection_certificate(bounds, branches, initial, margin)["certified"])

    def advance(branch, requested_depth):
        while depth[branch] < requested_depth and len(trace) < budget and not done():
            # A certified alternative is no longer needed for category audit.
            # Baseline reads may still certify other alternatives.
            if ((target == "categories" or
                 selection_certificate(current()[0], branches, initial, margin)["certified"])
                    and branch != baseline
                    and current()[1][branch] != "abstain"):
                break
            step = depth[branch] + 1
            obs = observe(branch, step)
            value = obs.incumbent
            if (not math.isfinite(value) or value < lower_bound
                    or value > latest[branch]):
                raise ValueError("Response violates incumbent monotonicity/lower bound")
            depth[branch], latest[branch] = step, value
            seen.add(obs.point_key)
            _, labels, reasons, intervals, _ = current()
            trace.append({"branch": branch, "step": step, "incumbent": value,
                          "point_key": obs.point_key, "requests_so_far": len(trace) + 1,
                          "branch_labels_after_read": labels,
                          "reasons_after_read": reasons,
                          "effect_intervals_after_read": intervals})

    if mode == "fixed_breadth":
        for step in range(horizon + 1):
            for branch in branches:
                advance(branch, step)
    else:
        if mode == "h0_largest_upper":
            for branch in branches:
                advance(branch, 0)
            # Only the exposed h0 observations are used to choose this order.
            anchor = min(branches, key=lambda b: (-latest[b], branches.index(b)))
            schedule = [anchor] + [b for b in branches if b != anchor]
        elif mode == "alternative_depth":
            schedule = others + [baseline]
        elif mode == "ordered_depth":
            schedule = list(order)
        else:
            schedule = branches
        for branch in schedule:
            advance(branch, horizon)

    bounds, branch_labels, branch_reasons, branch_intervals, branch_effects = current()
    selection = selection_certificate(bounds, branches, initial, margin)
    selection["additional_requests_to_complete_selected"] = horizon - depth[selection["branch"]]
    named = lambda d: {name: d[b] for b, nn in classes.items() for name in nn}
    return {"labels": named(branch_labels), "reasons": named(branch_reasons),
            "effect_intervals": named(branch_intervals), "measured_effects": named(branch_effects),
            "branch_labels": branch_labels, "terminal_bounds": bounds,
            "depth": depth, "requests": len(trace), "distinct_points": len(seen),
            "trace": trace, "selection": selection,
            "all_categories_certified": all(branch_labels[b] != "abstain" for b in others),
            "target_satisfied": done(), "target": target, "mode": mode}
