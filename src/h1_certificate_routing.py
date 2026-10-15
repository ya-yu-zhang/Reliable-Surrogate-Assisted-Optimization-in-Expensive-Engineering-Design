"""Route a scalar H1 lower-certificate request using a domain-cover identity.

This returns a certificate predicate, never an optimizer's actual performance
or the full action set. The reference requests that need sets must still build
them. All bounds are previously acquired inputs; this module acquires none.
"""
from fractions import Fraction
import math


def binary(value):
    value=float(value)
    if not math.isfinite(value):raise ValueError('Finite input required')
    return Fraction.from_float(value)


def pending_cap(initial,pending_lower,response_lower):
    if response_lower < 0:raise ValueError('Nonnegative closed domain required')
    return min(initial,max(pending_lower,response_lower))


def no_better_certificate(initial,threshold,pending_lower,response_lower,exact_next_lower):
    """Return the same Boolean as J >= threshold, with lazy next-bound reader.

    Preconditions: retained closed response intervals cover the entire declared
    half-line and exact_next_lower returns the minimum bound over that set.
    If the cheap cap fails, the callback (including action-set construction)
    is not evaluated. False means failure of this particular certificate.
    """
    cap=pending_cap(initial,pending_lower,response_lower)
    if cap < threshold:
        return {'certified':False,'route':'pending-cap rejection',
                'action_set_reader_called':False,'cap':cap}
    value=exact_next_lower()
    return {'certified':min(cap,value) >= threshold,'route':'exact next-bound reader',
            'action_set_reader_called':True,'cap':cap}
