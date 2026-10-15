"""Post-process frozen v2 leaves using the positive terminal-reward range.

No GP reconstruction, conditional-reward evaluation, fit or physical call.
The v2 arithmetic module and all original scientific files remain unchanged.
Input leaves must come from the already accepted, hash-identified v2 record.
"""
import math

from .rollout_v2_intervals import I, probability, exp_times_cdf
from .rollout_v2_solver import transformed


def capped_first_moment(model, low=-math.inf, high=math.inf):
    """Enclose E[min(m0,exp(m+sX)) 1_{low<X<high}], X~N(0,1).

    Interval m/s are enclosed uniformly. Split the uncertain incumbent crossing
    rather than substitute its midpoint. The central strip uses [0,m0].
    """
    if low >= high:
        return I(0)
    m0 = float(model['initial'])
    m, s = I(model['first_mean']), I(model['first_sd'])
    if m0 <= 0 or s.lo <= 0:
        raise ArithmeticError('Positive incumbent and nondegenerate marginal required')
    crossing = (I(m0).log()-m)/s
    result = I(0)
    below_end = min(high, crossing.lo)
    if low < below_end:
        logmoment = m+s.square()/2
        below = (exp_times_cdf(logmoment, I(below_end)-s)
                 -exp_times_cdf(logmoment, I(low)-s))
        cap = (m0*probability(low, below_end)).hi
        result += below.clipped(0, cap)
    strip_low, strip_high = max(low, crossing.lo), min(high, crossing.hi)
    if strip_low < strip_high:
        result += I(0, (m0*probability(strip_low, strip_high)).hi)
    above_start = max(low, crossing.hi)
    if above_start < high:
        result += m0*probability(above_start, high)
    return result.clipped(0, (m0*probability(low, high)).hi)


def baseline(model, low=-math.inf, high=math.inf):
    """First-evaluation improvement on a fixed standard-normal interval."""
    p = probability(low, high)
    return (model['initial']*p-capped_first_moment(model, low, high)).clipped(
        0, (model['initial']*p).hi)


def stable_inner_window(model, domain):
    """A common inner stable interval for every enclosed marginal parameter."""
    if domain is None:
        return None
    lo, hi = domain
    left = max(-8., transformed(lo, model).hi)
    right = min(8., transformed(hi, model).lo)
    return None if left >= right else (left, right)


def regional_enclosure(model, domain, cert, old_interval):
    """Enclose V with existing fixed-j leaf integrals and positive rewards.

    Within a leaf, W=q_j-(m0-h) is in [0,h]. A partial stable restriction J
    satisfies W_J >= W_cell^- - H_outside_J^+ and
    W_J <= min(W_cell^+, H_J^+). No new q_j evaluation is performed.
    """
    if cert['fixed'] is None:
        raise ValueError('Regional conversion requires a fixed-action certificate')
    m0 = float(model['initial'])
    base = baseline(model)
    inner = stable_inner_window(model, domain)
    leaves = sorted(cert['leaves'], key=lambda x:x['low'])
    if not leaves or leaves[0]['low'] != -8 or leaves[-1]['high'] != 8:
        raise ArithmeticError('Missing original integration window')
    added, last = I(0), -8.
    stable_cells = 0
    for leaf in leaves:
        low, high = leaf['low'], leaf['high']
        if low != last or not low < high:
            raise ArithmeticError('Invalid original leaf cover')
        last = high
        if leaf['active'] != [cert['fixed']]:
            raise ArithmeticError('Wrong fixed-action identity')
        if inner is None:
            continue
        a, b = max(low, inner[0]), min(high, inner[1])
        if a >= b:
            continue
        stable_cells += 1
        h_cell = capped_first_moment(model, low, high)
        w_cell = (I(leaf['interval'])-baseline(model, low, high)).clipped(0, h_cell.hi)
        h_part = capped_first_moment(model, a, b)
        h_complement = (capped_first_moment(model, low, a)
                        +capped_first_moment(model, b, high))
        added += I(max(0., (I(w_cell.lo)-h_complement).lo),
                   min(w_cell.hi, h_part.hi))
    if inner is None:
        unknown = capped_first_moment(model)
    else:
        unknown = (capped_first_moment(model, -math.inf, inner[0])
                   +capped_first_moment(model, inner[1], math.inf))
    region = (base+added+I(0, unknown.hi)).clipped(0, m0)
    narrowed = region.intersect(I(old_interval))
    return dict(interval=narrowed.pair(), regional_interval=region.pair(),
                baseline=base.pair(), retained_additional_improvement=added.pair(),
                unknown_capped_first_moment=unknown.pair(),
                stable_inner_window=None if inner is None else list(inner),
                reused_stable_leaf_cells=stable_cells)


def weighted_stability_radius(model, domain, old_radius):
    """A capped-first-response radius on the full response domain.

    A conservative common X interval is enough; intersect with the already
    checked old event radius so parameter wrapping cannot weaken the result.
    """
    if domain is None:
        value = capped_first_moment(model)
    else:
        lo, hi = domain
        left, right = transformed(lo, model).hi, transformed(hi, model).lo
        if left >= right:
            value = capped_first_moment(model)
        else:
            value = capped_first_moment(model, -math.inf, left)+capped_first_moment(model, right, math.inf)
    return min(float(old_radius), value.hi)
