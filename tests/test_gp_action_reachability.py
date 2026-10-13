"""Independent exact arithmetic and native-GP checks of the outer-set operation."""
import unittest
from fractions import Fraction

import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel

from src.gp_action_reachability import (outer_actions, rational_infeasible,
    coefficient_enclosures, joint_two_response_lower, category_from_interval)


def exact_actions(a, b, lower):
    f = Fraction.from_float
    out = []
    for i in range(len(a)):
        lo, hi = f(float(lower)), None
        for j in range(len(a)):
            m, c = f(float(a[i])) - f(float(a[j])), f(float(b[j])) - f(float(b[i]))
            if m == 0 and c < 0:
                hi = lo - 1; break
            if m > 0:
                t = c / m; hi = t if hi is None else min(hi, t)
            elif m < 0:
                lo = max(lo, c / m)
        if hi is None or lo <= hi:
            out.append(i)
    return out


class ReachabilityTests(unittest.TestCase):
    def test_interior_action_missed_by_endpoint_reader(self):
        a, b = np.array([1., 0., -1.]), np.array([0., .5, 2.])
        r = outer_actions(a, b)
        self.assertEqual(list(r['indices']), [0, 1, 2])
        self.assertEqual(int(np.argmin(a * 0 + b)), 0)
        self.assertEqual(int(np.argmin(a * 10 + b)), 2)
        self.assertEqual(int(np.argmin(a + b)), 1)

    def test_parallel_and_identical_actions_retain_ties(self):
        r = outer_actions([0., 0., 0.], [1., 1., 2.])
        self.assertEqual(list(r['indices']), [0, 1])
        self.assertEqual(len(r['excluded_proofs']), 1)

    def test_single_boundary_action_is_retained(self):
        r = outer_actions([1., 0., -1.], [0., 1., 2.])
        self.assertIn(1, r['indices'])
        self.assertLessEqual(r['response_lower'][1], 1.)
        self.assertGreaterEqual(r['response_upper'][1], 1.)

    def test_response_lower_removes_only_proven_infeasible_actions(self):
        r = outer_actions([1., 0., -1.], [0., .5, 2.], response_lower=2.)
        self.assertEqual(list(r['indices']), [2])
        for proof in r['excluded_proofs']:
            self.assertTrue(rational_infeasible(r['coefficient_band_lower_slope'],
                r['coefficient_band_lower_intercept'], r['coefficient_band_upper_slope'],
                r['coefficient_band_upper_intercept'], proof[0], proof[1:], 2.))

    def test_uncertainty_prevents_nominal_domination(self):
        self.assertEqual(list(outer_actions([0., 0.], [0., 1.])['indices']), [0])
        r = outer_actions([0., 0.], [0., 1.], intercept_error=[0., 2.])
        self.assertEqual(list(r['indices']), [0, 1])

    def test_random_sets_include_every_exact_binary_action(self):
        rng = np.random.default_rng(9)
        for _ in range(50):
            a, b = rng.normal(size=(2, 12)); lower = float(rng.random() * 4)
            r = outer_actions(a, b, response_lower=lower)
            self.assertTrue(set(exact_actions(a, b, lower)).issubset(set(r['indices'])))

    def test_kernel_linear_system_encloses_exact_rational_coefficients(self):
        matrix = np.array([[2., .25], [.25, 1.5]])
        cross = np.array([[.5, .75], [.125, .25]])
        y = np.array([7.])
        r = coefficient_enclosures(matrix, cross, y)
        f = Fraction.from_float
        det = f(2.) * f(1.5) - f(.25) ** 2
        for i, (k0, k1) in enumerate(cross):
            w0 = (f(float(k0)) * f(1.5) - f(float(k1)) * f(.25)) / det
            w1 = (f(float(k1)) * f(2.) - f(float(k0)) * f(.25)) / det
            h = (1 - w0 - w1) / 2
            for name, exact in [('slope', w1 + h), ('intercept', (w0 + h) * 7)]:
                error = r[name + '_error'][i]
                self.assertLessEqual(abs(f(float(r[name][i])) - exact), f(float(error)))

    def test_native_normalized_gp_predictions_across_unknown_labels(self):
        x = np.array([[0.], [.25], [.8]])
        k = ConstantKernel(2.) * RBF(.3); alpha = 1e-6
        matrix = k(x); matrix[np.diag_indices(3)] += alpha
        pool = np.linspace(0, 1, 31)[:, None]
        r = coefficient_enclosures(matrix, k(pool, x), [2., 4.])
        actions = outer_actions(r['slope'], r['intercept'],
            slope_error=r['slope_error'], intercept_error=r['intercept_error'])
        for z in [0., 1., 3., 10., 1e6]:
            gp = GaussianProcessRegressor(kernel=k, alpha=alpha, optimizer=None, normalize_y=True).fit(x, [2., 4., z])
            native = gp.predict(pool)
            affine = r['slope'] * z + r['intercept']
            np.testing.assert_allclose(native, affine, rtol=1e-10, atol=1e-9)
            self.assertIn(int(np.argmin(native)), actions['indices'])

    def test_singular_inverse_is_not_silently_used(self):
        with self.assertRaises(np.linalg.LinAlgError):
            coefficient_enclosures(np.ones((2, 2)), np.ones((3, 2)), [1.])

    def test_joint_bound_accounts_for_pending_response(self):
        r = outer_actions([0., 0.], [0., 1.], response_lower=5.)
        self.assertEqual(joint_two_response_lower(10., [8., 1.], r), 5.)

    def test_category_boundaries_and_abstention(self):
        self.assertEqual(category_from_interval(100., 100., 100., 100., .001), 'tie')
        self.assertEqual(category_from_interval(100., 100., 0., 100., .001), 'abstain')
        self.assertEqual(category_from_interval(90., 100., 99., 100., .001), 'worse')


if __name__ == '__main__':
    unittest.main()
