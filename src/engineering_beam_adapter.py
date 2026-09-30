"""Low-dimensional, volume-preserving wrapper for EngiBench Beams2D v1."""
from dataclasses import dataclass
import numpy as np
from scipy.ndimage import zoom
from engibench.problems.beams2d.v1 import Beams2D


@dataclass
class _Bounds:
    lb: np.ndarray
    ub: np.ndarray


@dataclass
class _Optimum:
    y: float = 0.0


@dataclass
class _State:
    evaluations: int = 0


def density_field(x, shape=(50, 100), volume_fraction=0.35):
    """Map 19 effective variables to a smooth field with exact mean volume."""
    x = np.asarray(x, dtype=float)
    if x.shape != (19,) or not np.isfinite(x).all() or np.any(x < 0) or np.any(x > 1):
        raise ValueError("beam parameters must be 19 finite values in [0,1]")
    # Exact volume preservation removes a common-logit shift. Anchor the final
    # coarse value at zero so the reported dimension equals the effective rank.
    coarse = np.concatenate((8.0 * (x - 0.5), [0.0])).reshape(4, 5)
    field = zoom(coarse, (shape[0] / 4, shape[1] / 5), order=3, mode="nearest")
    field = field[: shape[0], : shape[1]]
    lo, hi = -30.0, 30.0
    for _ in range(80):
        mid = (lo + hi) / 2
        mean = np.mean(1.0 / (1.0 + np.exp(-(field + mid))))
        if mean < volume_fraction:
            lo = mid
        else:
            hi = mid
    density = 1.0 / (1.0 + np.exp(-(field + (lo + hi) / 2)))
    if abs(float(density.mean()) - volume_fraction) > 1e-12:
        raise AssertionError("volume-preserving parameterization drift")
    return density


class EngineeringBeamObjective:
    dimension = 19

    def __init__(self):
        self.problem = Beams2D(seed=0)
        self.bounds = _Bounds(np.zeros(self.dimension), np.ones(self.dimension))
        self.optimum = _Optimum()
        self.state = _State()

    def __call__(self, x):
        density = density_field(x)
        value = float(self.problem.simulate(density)[0])
        self.state.evaluations += 1
        if not np.isfinite(value) or value <= 0:
            raise FloatingPointError(f"invalid compliance: {value}")
        return value


def make_problem(*_args, **_kwargs):
    return EngineeringBeamObjective()
