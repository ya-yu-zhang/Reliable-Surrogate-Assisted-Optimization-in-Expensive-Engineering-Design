"""Boundary and information-barrier examples for the H1 certificate."""
from fractions import Fraction as F
import unittest
from src.diagnose_h1_bound_bottlenecks import threshold_certificate


class ThresholdCertificateTests(unittest.TestCase):
    def test_closed_margin_boundary_passes(self):
        self.assertEqual(threshold_certificate(F(20), F(10), [F(10)], [F(10)]),
                         (F(10), 0, 0, True))

    def test_correcting_only_one_information_source_does_not_pass(self):
        self.assertFalse(threshold_certificate(F(20), F(10), [F(100)], [F(9)])[3])
        self.assertFalse(threshold_certificate(F(20), F(10), [F(9)], [F(100)])[3])

    def test_distinct_actions_can_block_distinct_terms(self):
        self.assertEqual(threshold_certificate(F(20), F(10), [F(9), F(12)], [F(12), F(9)]),
                         (F(9), 1, 1, False))

    def test_incumbent_is_an_independent_constraint(self):
        self.assertEqual(threshold_certificate(F(9), F(10), [F(12)], [F(12)]),
                         (F(9), 0, 0, False))


if __name__ == '__main__':
    unittest.main()
