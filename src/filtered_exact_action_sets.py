"""Exact band action sets: integer envelope and independent filtered all-pairs.

The numerical geometry is classical. Both readers return the complete closed
relaxed-band set, exact intervals and at most two rival indices per exclusion.
No model fitting, physical response or physical-bound acquisition is imported.
"""
from fractions import Fraction
import math
import numpy as np


def prepare_bands(low_a, low_b, up_a, up_b, domain):
    arrays = [[float(v) for v in row] for row in (low_a, low_b, up_a, up_b)]
    n = len(arrays[0])
    if not n or any(len(row) != n for row in arrays):
        raise ValueError('Incompatible band dimensions')
    if not all(math.isfinite(v) for row in arrays for v in row):
        raise ValueError('Nonfinite coefficient band')
    if any(arrays[0][i] > arrays[2][i] or arrays[1][i] > arrays[3][i]
           for i in range(n)):
        raise ValueError('Reversed coefficient band')
    domain = float(domain)
    if not math.isfinite(domain) or domain < 0:
        raise ValueError('Invalid nonnegative response domain')
    ratios = [[v.as_integer_ratio() for v in row] for row in arrays]
    power = max(q.bit_length()-1 for row in ratios for _,q in row)
    ints = [[p << (power-(q.bit_length()-1)) for p,q in row] for row in ratios]
    return ints, domain.as_integer_ratio(), max(abs(v).bit_length() for row in ints for v in row)


def _lt(left, right):
    return left[0]*right[1] < right[0]*left[1]


def _root(numerator, denominator):
    return (numerator,denominator) if denominator > 0 else (-numerator,-denominator)


def _first_true(start, stop, predicate):
    while start < stop:
        mid = (start+stop)//2
        if predicate(mid):
            stop = mid
        else:
            start = mid+1
    return start


def _constraint_scan(i, rivals, arrays, domain):
    la,lb,ua,ub = arrays
    lo,hi,lo_j,hi_j = domain,None,None,None
    for j in rivals:
        m,c = la[i]-ua[j],ub[j]-lb[i]
        if m == 0:
            if c < 0:
                return None,[i,j]
            continue
        point = _root(c,m)
        if m < 0 and _lt(lo,point):
            lo,lo_j = point,j
        elif m > 0 and (hi is None or _lt(point,hi)):
            hi,hi_j = point,j
        if hi is not None and _lt(hi,lo):
            proof = [i]+sorted({j for j in (lo_j,hi_j) if j is not None})
            return None,proof
    return (Fraction(*lo),None if hi is None else Fraction(*hi)),None


def filtered_pairwise_from_bands(low_a, low_b, up_a, up_b, *, response_lower=0., block=64):
    """Float proposals checked exactly; unresolved actions scan all constraints.

    This control does not construct an envelope. Overflow/NaN proposals can
    only cause exact fallback, never an unchecked exclusion. For fixed block
    size its proposal work is quadratic and its workspace is linear in M.
    """
    if not isinstance(block,int) or block < 1:
        raise ValueError('Positive integer block size required')
    arrays,domain,bits = prepare_bands(low_a,low_b,up_a,up_b,response_lower)
    la,lb,ua,ub = (np.asarray(row,dtype=float) for row in (low_a,low_b,up_a,up_b))
    n = len(la)
    kept,intervals,proofs = [],{},[]
    for begin in range(0,n,block):
        end = min(begin+block,n)
        with np.errstate(over='ignore',divide='ignore',invalid='ignore',under='ignore'):
            m = la[begin:end,None]-ua[None,:]
            c = ub[None,:]-lb[begin:end,None]
            quotients = c/m
            lower = np.argmax(np.where(m < 0,quotients,-np.inf),axis=1)
            upper = np.argmin(np.where(m > 0,quotients,np.inf),axis=1)
            parallel = (m == 0)&(c < 0)
        for k,i in enumerate(range(begin,end)):
            contradiction = np.flatnonzero(parallel[k])
            result,proof = (None,None)
            if len(contradiction):
                result,proof = _constraint_scan(i,[int(contradiction[0])],arrays,domain)
            if proof is None:
                proposed = sorted({int(lower[k]),int(upper[k])})
                result,proof = _constraint_scan(i,proposed,arrays,domain)
            if proof is None:
                result,proof = _constraint_scan(i,range(n),arrays,domain)
            if proof is not None:
                proofs.append(proof)
            else:
                kept.append(i);intervals[i] = result
    return {'indices':kept,'exact_intervals':intervals,'excluded_proofs':proofs,
            'scaled_coefficient_max_bits':bits,
            'arithmetic_complexity':'O(M^2) float proposals and exact fallback; fixed-block O(M) storage'}


def integer_envelope_from_bands(low_a, low_b, up_a, up_b, *, response_lower=0.):
    """Sorted upper-band lower envelope with unreduced integer predicates.

    Every original candidate is checked, including candidates whose upper line
    disappears from the envelope. Reduced fractions are output, not predicates.
    """
    arrays,domain,bits = prepare_bands(low_a,low_b,up_a,up_b,response_lower)
    la,lb,ua,ub = arrays
    n = len(la)
    ordered = sorted(range(n),key=lambda j:(-ua[j],ub[j],j))
    unique = []
    for j in ordered:
        if not unique or ua[j] != ua[unique[-1]]:
            unique.append(j)
    hull,starts = [],[]
    for j in unique:
        while hull:
            old = hull[-1]
            point = (ub[j]-ub[old],ua[old]-ua[j])
            if len(hull) == 1 or _lt(starts[-1],point):
                break
            hull.pop();starts.pop()
        else:
            point = None
        hull.append(j);starts.append(point)
    active = 0
    while active+1 < len(hull) and not _lt(domain,starts[active+1]):
        active += 1
    hull,starts = hull[active:],[domain]+starts[active+1:]
    size = len(hull)
    kept,intervals,proofs = [],{},[]
    for i in range(n):
        peak = _first_true(0,size,lambda k:ua[hull[k]] <= la[i])
        def gap(k):
            j = hull[k];p,q = starts[k]
            return (ua[j]-la[i])*p+(ub[j]-lb[i])*q
        feasible = peak == size or gap(peak) >= 0
        if not feasible:
            j = hull[peak]
            rivals = [j] if peak == 0 or ua[j] == la[i] else sorted({hull[peak-1],j})
            proofs.append([i,*rivals]);continue
        if gap(0) >= 0:
            lo = Fraction(*domain)
        else:
            stop = size if peak == size else peak+1
            first = _first_true(1,stop,lambda k:gap(k) >= 0)
            j = hull[first-1]
            lo = Fraction(ub[j]-lb[i],la[i]-ua[j])
        last = hull[-1]
        if ua[last] >= la[i]:
            hi = None
        else:
            first = _first_true(min(peak,size-1),size,lambda k:gap(k) < 0)
            j = hull[first-1] if first < size else last
            hi = Fraction(ub[j]-lb[i],la[i]-ua[j])
        assert lo >= Fraction(*domain) and (hi is None or lo <= hi)
        kept.append(i);intervals[i] = (lo,hi)
    return {'indices':kept,'exact_intervals':intervals,'excluded_proofs':proofs,
            'upper_envelope_indices':hull,
            'upper_envelope_starts':[Fraction(*point) for point in starts],
            'scaled_coefficient_max_bits':bits,
            'arithmetic_complexity':'O(M log M) arithmetic, O(M) storage; integer bit costs separate'}
