"""Small independent identities for direct EI integration, without GP inputs."""
from fractions import Fraction
import json
import math
import numpy as np
from scipy.integrate import quad
from scipy.special import ndtr
from .compute_direct_rollout import whole_line, cells, integrate


def run():
    # Exact crossing on both half-lines, and positive-probability identical ties.
    parts = list(cells(whole_line(([1., -1.], [0., 0.], [1., -1.], [0., 0.]))))
    assert parts == [(None, Fraction(0), [0]), (Fraction(0), None, [1])]
    tied = list(cells(whole_line(([0., 0.], [1., 1.], [0., 0.], [1., 1.]))))
    assert all(min(active) == 0 for _, _, active in tied)
    checks = []
    for mz, sz, mu, sigma, m0 in [(0., 1., 0., 1., 1.), (2., .7, -1., 3., .5),
                                (-3., 4., 2., .2, 2.)]:
        args = ([(None, None, 0)], mz, sz, np.array([mu]), np.array([0.]), np.array([sigma]), m0)
        V = integrate(*args, 'value', True)[0]
        N = integrate(*args, 'negative', True)[0]
        P = integrate(*args, 'clipped', True)[0]
        # Independent survival identity for two independent Gaussian responses.
        lo = min(mz-14*sz, mu-14*sigma)
        oracle = quad(lambda t: 1-float(ndtr((mz-t)/sz)*ndtr((mu-t)/sigma)),
                      lo, m0, epsabs=1e-11, epsrel=1e-11)[0]
        clipped_oracle = m0-quad(lambda t: float(ndtr((mz-t)/sz)*ndtr((mu-t)/sigma)),
                                0., m0, epsabs=1e-12, epsrel=1e-12)[0]
        assert math.isclose(V, oracle, rel_tol=1e-10, abs_tol=1e-10)
        assert math.isclose(P, clipped_oracle, rel_tol=1e-10, abs_tol=1e-10)
        assert math.isclose(V-N, P, rel_tol=1e-10, abs_tol=1e-10)
        checks.append(dict(value_abs_error=abs(V-oracle), clipped_abs_error=abs(P-clipped_oracle),
                           decomposition_abs_error=abs(V-N-P)))
    return dict(exact_partition_checks=2, independent_gaussian_identity_cases=checks,
                new_root_systems=0, new_physical_evaluations=0)


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
