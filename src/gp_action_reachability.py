"""One-unknown-response mean-action outer sets, conditional on binary GP kernels.

Linear GP algebra and affine envelopes are established tools. No H5, EI,
hyperparameter-refit, PDE or native floating-prediction certificate is claimed.
Each pruned action additionally needs an exact rational infeasibility witness.
"""
from __future__ import annotations

import math
from fractions import Fraction

import numpy as np
from scipy.linalg import cho_solve

from .reduced_compliance_bounds import gamma


def upper(x):
    return np.nextafter(x, np.inf)


def coefficient_enclosures(matrix, cross, known_y, *, condition_limit=0.5):
    """Enclose exact affine coefficients for the supplied binary linear system.

    matrix includes the noise diagonal. cross has candidates by training points;
    the last training point's response is unknown. No labels for it are accepted.
    Residual bounds include finite normal IEEE dot/reduction arithmetic; kernel
    evaluations are treated as input binary numbers, not exact transcendental
    functions. Failure must cause a caller to retain the entire candidate pool.
    """
    a, k, y = map(lambda v: np.asarray(v, dtype=float), (matrix, cross, known_y))
    n = len(a)
    if (a.shape != (n, n) or k.ndim != 2 or k.shape[1] != n
            or y.shape != (n - 1,) or not np.array_equal(a, a.T)
            or not all(np.isfinite(v).all() for v in [a, k, y])):
        raise ValueError("Invalid fixed binary-kernel system")
    chol = np.linalg.cholesky(a)
    inv = cho_solve((chol, True), np.eye(n))
    weights = cho_solve((chol, True), k.T).T
    g = gamma(4 * n + 32)
    abs_product = upper((np.abs(a) @ np.abs(inv)) / (1 - g))
    residual_abs_upper = upper(np.abs(np.eye(n) - a @ inv)
                               + upper(g * upper(abs_product + np.eye(n))))
    residual_norm = float(np.max(upper(residual_abs_upper.sum(axis=1) / (1 - g))))
    if not math.isfinite(residual_norm) or residual_norm >= condition_limit:
        raise FloatingPointError("Inverse residual gate failed")
    inv_norm = float(np.max(upper(np.abs(inv).sum(axis=1) / (1 - g))))
    inv_norm = math.nextafter(inv_norm / math.nextafter(1 - residual_norm, -math.inf), math.inf)
    absolute = upper((np.abs(a) @ np.abs(weights.T) + np.abs(k.T)) / (1 - g))
    residual = k.T - a @ weights.T
    residual_upper = upper(np.abs(residual) + upper(g * absolute))
    weight_error = upper(inv_norm * residual_upper.max(axis=0))
    absolute_weight_sum = upper(np.abs(weights).sum(axis=1) / (1 - g))
    offset = (1 - weights.sum(axis=1)) / n
    effective = weights + offset[:, None]
    # Each exact effective weight differs by <=2*weight_error, plus the
    # explicitly bounded normalization, sum, subtraction and addition work.
    calculation_error = upper(g * upper((1 + absolute_weight_sum) / n
                                  + np.abs(weights).max(axis=1) + np.abs(offset)))
    effective_error = upper(upper(2 * weight_error) + calculation_error)
    slope = effective[:, -1]
    intercept = effective[:, :-1] @ y
    sum_y = math.nextafter(float(np.abs(y).sum()) / (1 - g), math.inf)
    dot_absolute = upper((np.abs(effective[:, :-1]) @ np.abs(y)) / (1 - g))
    intercept_error = upper(upper(effective_error * sum_y) + upper(g * dot_absolute))
    if not all(np.isfinite(v).all() for v in [slope, intercept, effective_error, intercept_error]):
        raise FloatingPointError("Coefficient enclosure overflow")
    return {"slope": slope, "intercept": intercept, "slope_error": effective_error,
            "intercept_error": intercept_error, "inverse_residual_norm_upper": residual_norm,
            "inverse_norm_upper": inv_norm}


def rational_infeasible(low_a, low_b, up_a, up_b, index, constraints, response_lower):
    """Exact certificate: a subset of necessary pair inequalities is infeasible."""
    f = Fraction.from_float
    lo, hi = f(float(response_lower)), None
    for j in sorted(set(constraints)):
        if j < 0:
            continue
        m = f(float(low_a[index])) - f(float(up_a[j]))
        c = f(float(up_b[j])) - f(float(low_b[index]))
        if m == 0:
            if c < 0:
                return True
        elif m > 0:
            value = c / m
            hi = value if hi is None else min(hi, value)
        else:
            lo = max(lo, c / m)
    return hi is not None and lo > hi


def outer_actions(slope, intercept, *, slope_error=None, intercept_error=None, response_lower=0.):
    """Necessary outer feasible ranges for every possibly minimal affine action.

    The response has no finite upper cap. Pair inequalities are relaxed outwards;
    the exact certificate checks the original coefficient-band endpoints. Ties
    remain. The returned intervals are conservative, not observed future labels.
    """
    a, b = np.asarray(slope, dtype=float), np.asarray(intercept, dtype=float)
    ea = np.zeros_like(a) if slope_error is None else np.asarray(slope_error, dtype=float)
    eb = np.zeros_like(b) if intercept_error is None else np.asarray(intercept_error, dtype=float)
    if (a.ndim != 1 or not len(a) or any(v.shape != a.shape for v in [b, ea, eb])
            or not all(np.isfinite(v).all() for v in [a, b, ea, eb])
            or np.any(ea < 0) or np.any(eb < 0) or not math.isfinite(response_lower) or response_lower < 0):
        raise ValueError("Invalid affine bands/nonnegative response range")
    al = np.where(ea == 0, a, np.nextafter(a - ea, -np.inf))
    au = np.where(ea == 0, a, np.nextafter(a + ea, np.inf))
    bl = np.where(eb == 0, b, np.nextafter(b - eb, -np.inf))
    bu = np.where(eb == 0, b, np.nextafter(b + eb, np.inf))
    keep = np.ones(len(a), dtype=bool)
    lo, hi = np.full(len(a), response_lower), np.full(len(a), np.inf)
    proofs, unresolved = [], 0
    for i in range(len(a)):
        m = np.nextafter(al[i] - au, -np.inf)
        c = np.nextafter(bu - bl[i], np.inf)
        # Equal binary operands subtract exactly to zero. Artificially turning
        # that zero into a subnormal slope would retain dominated parallel
        # lines at astronomical z on the unbounded response interval.
        m[al[i] == au] = 0.
        c[bu == bl[i]] = 0.
        m[i], c[i] = -1., 0.
        bad = np.flatnonzero((m == 0) & (c < 0))
        lower_values, upper_values = np.full(len(a), -np.inf), np.full(len(a), np.inf)
        with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
            neg, pos = m < 0, m > 0
            lower_values[neg] = np.nextafter(c[neg] / m[neg], -np.inf)
            upper_values[pos] = np.nextafter(c[pos] / m[pos], np.inf)
        jl, ju = int(np.argmax(lower_values)), int(np.argmin(upper_values))
        lo[i], hi[i] = max(response_lower, lower_values[jl]), upper_values[ju]
        tentative = bool(len(bad)) or lo[i] > hi[i]
        if tentative:
            js = [int(bad[0])] if len(bad) else [jl, ju]
            if rational_infeasible(al, bl, au, bu, i, js, response_lower):
                keep[i] = False
                proofs.append([i, *sorted(set(js))])
            else:
                unresolved += 1
                lo[i], hi[i] = response_lower, np.inf
    if not keep.any():
        raise AssertionError("Finite affine minimum must have an action")
    return {"indices": np.flatnonzero(keep), "response_lower": lo, "response_upper": hi,
            "excluded_proofs": proofs, "unresolved_exclusions_retained": unresolved,
            "coefficient_band_lower_slope": al, "coefficient_band_lower_intercept": bl,
            "coefficient_band_upper_slope": au, "coefficient_band_upper_intercept": bu}


def joint_two_response_lower(initial, point_lowers, action_set):
    ids = action_set["indices"]
    return float(min(initial, np.min(np.minimum(action_set["response_lower"][ids],
                                               np.asarray(point_lowers)[ids]))))


def category_from_interval(baseline, initial, terminal_lower, terminal_upper, margin):
    """Conditional category, using exact binary-input arithmetic at boundaries."""
    f = Fraction.from_float
    low_effect = f(float(baseline)) - f(float(terminal_upper))
    high_effect = f(float(baseline)) - f(float(terminal_lower))
    eps = f(float(margin)) * f(float(initial))
    if low_effect > eps:
        return "better"
    if high_effect < -eps:
        return "worse"
    if low_effect >= -eps and high_effect <= eps:
        return "tie"
    return "abstain"
