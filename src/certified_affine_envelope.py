"""Exact response-domain outer sets with a shared affine-envelope certificate.

Inputs are finite binary coefficient bands, not future responses. Geometry of
affine envelopes is classical. This operator preserves closed ties, returns
exact rational feasible intervals, and uses at most two rival indices to
certify each exclusion. Arithmetic-operation count is O(M log M); rational bit
cost is separate. No GP, physical engine or bound evaluator is imported.
"""
from __future__ import annotations

from bisect import bisect_right
from fractions import Fraction
import math


def _fraction(x):
    return Fraction.from_float(float(x))


def coefficient_bands(slope, intercept, slope_error=None, intercept_error=None):
    n = len(slope)
    ea = [0.]*n if slope_error is None else slope_error
    eb = [0.]*n if intercept_error is None else intercept_error
    if not n or any(len(x) != n for x in (intercept, ea, eb)):
        raise ValueError('Incompatible coefficient dimensions')
    out = [[], [], [], []]
    for a, b, x, y in zip(slope, intercept, ea, eb, strict=True):
        a, b, x, y = map(float, (a, b, x, y))
        if not all(math.isfinite(v) for v in (a, b, x, y)) or min(x, y) < 0:
            raise ValueError('Invalid coefficient/error')
        values = (a if x == 0 else math.nextafter(a-x, -math.inf),
                  b if y == 0 else math.nextafter(b-y, -math.inf),
                  a if x == 0 else math.nextafter(a+x, math.inf),
                  b if y == 0 else math.nextafter(b+y, math.inf))
        if not all(math.isfinite(v) for v in values):
            raise ValueError('Band overflow: caller must retain the full pool')
        for row, value in zip(out, values, strict=True):
            row.append(value)
    return out


def _upper_line_lower_envelope(a, b, domain):
    # Minimum of upper lines: active slopes decrease as the response increases.
    ordered = sorted(range(len(a)), key=lambda j: (-a[j], b[j], j))
    unique = []
    for j in ordered:
        if not unique or a[j] != a[unique[-1]]:
            unique.append(j)
    hull, starts = [], []
    for j in unique:
        while hull:
            old = hull[-1]
            start = (b[j]-b[old])/(a[old]-a[j])
            if len(hull) == 1 or start > starts[-1]:
                break
            hull.pop(); starts.pop()
        else:
            start = None
        hull.append(j); starts.append(start)
    active = bisect_right(starts[1:], domain)
    return hull[active:], [domain]+starts[active+1:]


def _first_true(start, stop, predicate):
    """First true index in a monotone false/true sequence, stop if absent."""
    while start < stop:
        middle = (start+stop)//2
        if predicate(middle):
            stop = middle
        else:
            start = middle+1
    return start


def exact_outer_from_bands(low_a, low_b, up_a, up_b, *, response_lower=0.):
    """Solve all necessary band inequalities exactly on a closed half-line.

    Candidate i is retained iff low_a[i]*z+low_b[i] <= min_j U_j(z)
    somewhere on z >= response_lower. This is an outer set for the uncertain
    affine decisions, not a claim that every retained action is realizable by
    a coupled GP coefficient vector.
    """
    n = len(low_a)
    if not n or any(len(x) != n for x in (low_b, up_a, up_b)):
        raise ValueError('Incompatible band dimensions')
    if not math.isfinite(float(response_lower)) or response_lower < 0:
        raise ValueError('Invalid nonnegative response domain')
    arrays = (low_a, low_b, up_a, up_b)
    if not all(math.isfinite(float(v)) for x in arrays for v in x):
        raise ValueError('Nonfinite coefficient band')
    la, lb, ua, ub = ([ _fraction(v) for v in x ] for x in arrays)
    if any(la[i] > ua[i] or lb[i] > ub[i] for i in range(n)):
        raise ValueError('Reversed coefficient band')
    domain = _fraction(response_lower)
    hull, starts = _upper_line_lower_envelope(ua, ub, domain)
    size = len(hull)
    kept, intervals, proofs = [], {}, []
    for i in range(n):
        # E(z)-L_i(z) is concave. Its slope changes sign at most once.
        peak = _first_true(0, size, lambda k: ua[hull[k]] <= la[i])
        def gap(k):
            j = hull[k]
            return (ua[j]-la[i])*starts[k]+ub[j]-lb[i]
        if peak == size:
            feasible = True  # Strictly increasing affine tail tends to +inf.
        else:
            feasible = gap(peak) >= 0
        if not feasible:
            j = hull[peak]
            if peak == 0 or ua[j] == la[i]:
                rivals = [j]
            else:
                rivals = sorted({hull[peak-1], j})
            proofs.append([i, *rivals])
            continue
        kept.append(i)
        if gap(0) >= 0:
            lower = domain
        else:
            stop = size if peak == size else peak+1
            first = _first_true(1, stop, lambda k: gap(k) >= 0)
            j = hull[first-1]
            lower = (ub[j]-lb[i])/(la[i]-ua[j])
        last = hull[-1]
        if ua[last] >= la[i]:
            upper = None
        else:
            start = min(peak, size-1)
            first = _first_true(start, size, lambda k: gap(k) < 0)
            j = hull[first-1] if first < size else last
            upper = (ub[j]-lb[i])/(la[i]-ua[j])
        assert lower >= domain and (upper is None or lower <= upper)
        intervals[i] = (lower, upper)
    assert kept
    return {'indices': kept, 'exact_intervals': intervals,
            'excluded_proofs': proofs, 'upper_envelope_indices': hull,
            'upper_envelope_starts': starts,
            'arithmetic_complexity': 'O(M log M), excluding rational bit costs'}


def exact_outer_actions(slope, intercept, *, slope_error=None, intercept_error=None,
                        response_lower=0.):
    return exact_outer_from_bands(*coefficient_bands(slope, intercept, slope_error,
                                                   intercept_error),
                                  response_lower=response_lower)


def check_exclusion(low_a, low_b, up_a, up_b, proof, response_lower=0.):
    """Small independent certificate checker, without building an envelope."""
    i, *rivals = proof
    lower, upper = _fraction(response_lower), None
    for j in rivals:
        m = _fraction(low_a[i])-_fraction(up_a[j])
        c = _fraction(up_b[j])-_fraction(low_b[i])
        if m == 0:
            if c < 0:
                return True
        elif m > 0:
            value = c/m
            upper = value if upper is None else min(upper, value)
        else:
            lower = max(lower, c/m)
    return upper is not None and lower > upper
