import unittest
from fractions import Fraction

import numpy as np

from src.reduced_compliance_bounds import TrialSpace, material_upper


class ReducedComplianceTests(unittest.TestCase):
    def fixture(self):
        ke = np.array([[2., -1.], [-1., 2.]])
        vectors = np.array([[[1., .3], [.4, 1.]], [[-.7, .8], [.2, -.5]]])
        return ke, vectors, TrialSpace(vectors, ke, [-.4, -1.], emin=.1, emax=1.)

    def exact_rayleigh(self, ke, vectors, rho, coefficients):
        f = Fraction
        energy = f(0)
        for e, r in enumerate(rho):
            v = [sum(f(vectors[e, i, k]) * f(coefficients[k]) for k in range(2)) for i in range(2)]
            quadratic = sum(v[i] * f(ke[i, j]) * v[j] for i in range(2) for j in range(2))
            material = f(.1) + f(r) ** 3 * (f(1.) - f(.1))
            energy += material * quadratic
        work = f(-.4) * f(coefficients[0]) + f(-1.) * f(coefficients[1])
        return work ** 2 / energy

    def test_material_upper_encloses_exact_binary_float_simp(self):
        rho = np.array([0., .001, .35, .999999, 1.])
        upper = material_upper(rho, .1, 1.)
        for r, u in zip(rho, upper):
            exact = Fraction(.1) + Fraction(r) ** 3 * (Fraction(1.) - Fraction(.1))
            self.assertGreaterEqual(Fraction(u), exact)

    def test_rayleigh_enclosure_including_negative_cross_terms(self):
        ke, vectors, space = self.fixture()
        for rho in [[.1, .9], [.35, .35], [.99, .02]]:
            for coefficients in [[1., 0.], [0., 1.], [-2., .3], [1e4, -2e4]]:
                lower = space.rayleigh_lower(rho, coefficients)
                exact = self.exact_rayleigh(ke, vectors, rho, coefficients)
                self.assertLessEqual(Fraction(lower), exact)
                self.assertGreater(lower, 0.)

    def test_span_bound_cannot_be_weaker_than_either_trial(self):
        _, _, space = self.fixture()
        result = space.evaluate(np.array([.35, .8]))
        self.assertGreaterEqual(result['span_two_lower'], result['two_trial_max_lower'])
        self.assertTrue(result['reduced_system_success'])

    def test_singular_reduced_space_falls_back_to_scalar_trial(self):
        ke, vectors, _ = self.fixture()
        vectors[:, :, 1] = vectors[:, :, 0]
        space = TrialSpace(vectors, ke, [-.4, -.4], emin=.1, emax=1.)
        result = space.evaluate(np.array([.35, .8]))
        self.assertFalse(result['reduced_system_success'])
        self.assertEqual(result['span_two_lower'], result['two_trial_max_lower'])

    def test_density_outside_physical_interval_is_rejected(self):
        _, _, space = self.fixture()
        for rho in [[-.1, .5], [1.1, .5], [float('nan'), .5]]:
            with self.assertRaises(ValueError):
                space.evaluate(np.array(rho))


if __name__ == '__main__':
    unittest.main()
