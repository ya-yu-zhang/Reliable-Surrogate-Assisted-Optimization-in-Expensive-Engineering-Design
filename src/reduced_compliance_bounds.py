"""Small trial-space compliance lower bounds for a fixed discrete stiffness.

For SPD K, every kinematically admissible v gives (f.T v)^2/(v.T K v)
<= f.T inv(K) f. This classical variational bound is not new theory. The
reduced solve only chooses a trial vector; it is not trusted as a certificate.
Element-energy and material upper enclosures make its Rayleigh ratio conservative
under the documented finite, normal IEEE float64 arithmetic assumptions.
No PDE/mesh-convergence or stored-solver-output error certificate is supplied.
"""
from __future__ import annotations

import math
import numpy as np

EPS = 2.0 ** -53


def gamma(n):
    if n * EPS >= 1:
        raise ValueError("Invalid rounding-operation count")
    return math.nextafter(n * EPS / (1 - n * EPS), math.inf)


def up(value):
    return np.nextafter(value, np.inf)


def material_upper(rho, emin=1e-9, emax=1.0):
    rho = np.asarray(rho, dtype=float)
    if not np.isfinite(rho).all() or np.any(rho < 0) or np.any(rho > 1) or not 0 < emin < emax:
        raise ValueError("Invalid SIMP material")
    power = up(up(rho * rho) * rho)
    return up(emin + up(power * math.nextafter(emax - emin, math.inf)))


class TrialSpace:
    """Two admissible displacement columns and the single-load work vector.

    element_vectors has shape (elements, local_dofs, 2). load_work contains the
    exact binary-float work of each column for the single unit load used here.
    Dirichlet admissibility and SPD assumptions belong to the caller.
    """

    def __init__(self, element_vectors, ke, load_work, *, emin=1e-9, emax=1.0):
        v, ke, q = np.asarray(element_vectors, dtype=float), np.asarray(ke, dtype=float), np.asarray(load_work, dtype=float)
        if (v.ndim != 3 or v.shape[2] != 2 or ke.shape != (v.shape[1], v.shape[1])
                or q.shape != (2,) or not all(np.isfinite(a).all() for a in [v, ke, q])
                or not np.array_equal(ke, ke.T) or not 0 < emin < emax):
            raise ValueError("Invalid trial space")
        self.emin, self.emax, self.q = emin, emax, q
        self.grams = np.empty((v.shape[0], 2, 2))
        self.errors = np.empty_like(self.grams)
        # A conservative count covers both products and the reduction for each
        # local quadratic form (8x8 in the beam; no large BLAS reduction).
        rounding = gamma(8 * v.shape[1] ** 2)
        for i in range(2):
            for j in range(i, 2):
                raw = np.einsum("ei,ij,ej->e", v[:, :, i], ke, v[:, :, j], optimize=False)
                absolute = np.einsum("ei,ij,ej->e", np.abs(v[:, :, i]), np.abs(ke), np.abs(v[:, :, j]), optimize=False)
                absolute_upper = up(absolute / (1 - rounding))
                error = up(rounding * absolute_upper + np.finfo(float).tiny)
                self.grams[:, i, j] = self.grams[:, j, i] = raw
                self.errors[:, i, j] = self.errors[:, j, i] = error
        if not all(np.isfinite(a).all() for a in [self.grams, self.errors]):
            raise FloatingPointError("Trial-space overflow")

    def rayleigh_lower(self, rho, coefficients):
        c, rho = np.asarray(coefficients, dtype=float), np.asarray(rho, dtype=float)
        if c.shape != (2,) or rho.shape != (len(self.grams),) or not np.isfinite(c).all():
            raise ValueError("Invalid trial coefficients/density")
        products = c[:, None] * c[None, :]
        energy = np.einsum("ij,eij->e", products, self.grams, optimize=False)
        absolute = np.einsum("ij,eij->e", np.abs(products), np.abs(self.grams), optimize=False)
        error = np.einsum("ij,eij->e", up(np.abs(products)), self.errors, optimize=False)
        rounding = gamma(64)
        error_upper = up((error + rounding * up(absolute / (1 - rounding))) / (1 - rounding))
        energy_upper = up(np.maximum(0., up(energy + error_upper)))
        terms_upper = up(material_upper(rho, self.emin, self.emax) * energy_upper)
        # Positive reduction guard; floating zero/subnormal contributions are
        # covered conservatively by the positive tiny floor above.
        denominator = math.nextafter(float(terms_upper.sum()) / (1 - gamma(2 * len(rho) + 4)), math.inf)
        work = float(c @ self.q)
        work_absolute = float(np.abs(c * self.q).sum())
        work_error = math.nextafter(gamma(16) * work_absolute / (1 - gamma(16)), math.inf)
        work_abs_lower = max(0., math.nextafter(abs(work) - work_error, -math.inf))
        square_lower = max(0., math.nextafter(work_abs_lower * work_abs_lower, -math.inf))
        if not math.isfinite(denominator) or denominator <= 0:
            raise FloatingPointError("Invalid trial energy upper bound")
        return max(0., math.nextafter(square_lower / denominator, -math.inf))

    def evaluate(self, rho):
        rho = np.asarray(rho, dtype=float)
        first = self.rayleigh_lower(rho, [1., 0.])
        second = self.rayleigh_lower(rho, [0., 1.])
        material = self.emin + rho ** 3 * (self.emax - self.emin)
        reduced = np.einsum("e,eij->ij", material, self.grams, optimize=False)
        try:
            condition = float(np.linalg.cond(reduced))
            if not math.isfinite(condition) or condition > 1e12:
                raise np.linalg.LinAlgError("Ill-conditioned trial space")
            coeff = np.linalg.solve(reduced, self.q)
            combined = self.rayleigh_lower(rho, coeff)
            solved = True
        except (np.linalg.LinAlgError, FloatingPointError):
            coeff, combined, solved = np.array([0., 0.]), 0., False
        return {"all_solid_trial_lower": first, "training_trial_lower": second,
                "two_trial_max_lower": max(first, second),
                "span_two_lower": max(first, second, combined),
                "reduced_system_attempts": 1, "reduced_system_success": solved,
            "coefficients": coeff.tolist()}
