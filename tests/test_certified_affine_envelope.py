"""Exact all-pairs oracle and adversarial boundary tests; no engineering cases."""
from fractions import Fraction
import random
import unittest

from src.certified_affine_envelope import (exact_outer_actions,
    exact_outer_from_bands, coefficient_bands, check_exclusion)


def all_pairs_oracle(bands, domain):
    la, lb, ua, ub = [[Fraction.from_float(float(v)) for v in row] for row in bands]
    result = {}
    for i in range(len(la)):
        lo, hi = Fraction.from_float(float(domain)), None
        for j in range(len(la)):
            m, c = la[i]-ua[j], ub[j]-lb[i]
            if m == 0 and c < 0:
                hi = lo-1; break
            if m > 0:
                x = c/m; hi = x if hi is None else min(hi, x)
            if m < 0:
                lo = max(lo, c/m)
        if hi is None or lo <= hi:
            result[i] = (lo, hi)
    return result


class CertifiedEnvelopeTests(unittest.TestCase):
    def compare(self, a, b, ea=None, eb=None, domain=0.):
        bands = coefficient_bands(a, b, ea, eb)
        expected = all_pairs_oracle(bands, domain)
        actual = exact_outer_from_bands(*bands, response_lower=domain)
        self.assertEqual(actual['exact_intervals'], expected)
        self.assertEqual(actual['indices'], sorted(expected))
        self.assertEqual(len(actual['indices'])+len(actual['excluded_proofs']), len(a))
        for proof in actual['excluded_proofs']:
            self.assertLessEqual(len(proof)-1, 2)
            self.assertTrue(check_exclusion(*bands, proof, domain))
        return actual

    def test_interior_and_isolated_boundary_actions(self):
        self.compare([1., 0., -1.], [0., .5, 2.])
        r = self.compare([1., 0., -1.], [0., 1., 2.])
        self.assertEqual(r['exact_intervals'][1], (Fraction(1), Fraction(1)))

    def test_boundary_only_action_can_be_lowest_index_argmin(self):
        # Dropping zero-length acceptance intervals is unsafe for this contract.
        a, b = [0., 1., -1.], [1., 0., 2.]
        r = self.compare(a, b)
        self.assertEqual(r['exact_intervals'][0], (Fraction(1), Fraction(1)))
        values = [x+y for x, y in zip(a, b)]
        self.assertEqual(values.index(min(values)), 0)

    def test_parallel_identical_and_unbounded_ties(self):
        r = self.compare([0., 0., 0.], [1., 1., 2.])
        self.assertEqual(r['indices'], [0, 1])
        self.assertEqual(r['exact_intervals'][0], (Fraction(0), None))

    def test_domain_starts_inside_and_at_envelope_breakpoints(self):
        for domain in [0., .5, 1., 1.5, 2., 10.]:
            self.compare([1., 0., -1.], [0., 1., 2.], domain=domain)

    def test_uncertainty_and_nearly_parallel_bands(self):
        self.compare([0., 0.], [0., 1.], eb=[0., 2.])
        self.compare([1., 1.+2.**-50, 1.-2.**-50], [0., -1., 2.])

    def test_random_band_intervals_equal_independent_all_pairs(self):
        rng = random.Random(58)
        for _ in range(160):
            n = rng.randrange(1, 22)
            a = [rng.uniform(-5, 5) for _ in range(n)]
            b = [rng.uniform(-20, 20) for _ in range(n)]
            ea = [rng.choice([0., .001, .4]) for _ in range(n)]
            eb = [rng.choice([0., .01, 2.]) for _ in range(n)]
            self.compare(a, b, ea, eb, rng.uniform(0, 5))

    def test_forged_proof_and_invalid_bands_are_rejected(self):
        bands = coefficient_bands([0., 0.], [0., 1.])
        self.assertFalse(check_exclusion(*bands, [1, 1]))
        with self.assertRaises(ValueError):
            exact_outer_from_bands([1.], [0.], [0.], [0.])
        with self.assertRaises(ValueError):
            exact_outer_actions([float('inf')], [0.])
