"""Auditable CEC2017 objective adapter for the existing strict-budget runners."""
from dataclasses import dataclass
import numpy as np
from opfunu.cec_based import cec2017


@dataclass
class _Bounds:
    lb: np.ndarray
    ub: np.ndarray


@dataclass
class _Optimum:
    y: float


@dataclass
class _State:
    evaluations: int = 0


class CEC2017Objective:
    def __init__(self, fid: int, dim: int):
        if fid == 2 or fid < 1 or fid > 30:
            raise ValueError(f"CEC2017 function {fid} is not in the corrected 29-function suite")
        cls = getattr(cec2017, f"F{fid}2017")
        self.function = cls(ndim=dim)
        self.bounds = _Bounds(np.asarray(self.function.lb, dtype=float),
                              np.asarray(self.function.ub, dtype=float))
        self.optimum = _Optimum(float(self.function.f_bias))
        self.state = _State()

    def __call__(self, x):
        value = float(self.function.evaluate(np.asarray(x, dtype=float)))
        self.state.evaluations += 1
        return value


def make_problem(fid, dimension=None, dim=None, **_ignored):
    actual_dim = dimension if dimension is not None else dim
    return CEC2017Objective(int(fid), int(actual_dim))
