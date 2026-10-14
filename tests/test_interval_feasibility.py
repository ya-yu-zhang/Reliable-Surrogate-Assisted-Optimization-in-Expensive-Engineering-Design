import itertools
import unittest
from src.audit_innovation_feasibility import candidate_interval_regret


class IntervalCertificateTests(unittest.TestCase):
    def test_formula_matches_adversarial_corner_values(self):
        # Enumerate terminal outcomes, independently of the analytic formula.
        lower={'a':3.,'b':1.,'c':2.};upper={'a':7.,'b':8.,'c':5.}
        for chosen in upper:
            actual=max(values[list(upper).index(chosen)]-min(values)
                       for values in itertools.product(*[(lower[k],upper[k]) for k in upper]))
            self.assertEqual(candidate_interval_regret(upper,lower,chosen),actual)

    def test_late_zero_competitor_blocks_small_loss_certificate(self):
        self.assertEqual(candidate_interval_regret({'a':100.,'b':100.},{'a':90.,'b':0.},'a'),100.)

    def test_exact_boundary_is_allowed_without_a_strict_gain_claim(self):
        self.assertEqual(candidate_interval_regret({'a':2.,'b':3.},{'a':0.,'b':1.},'a'),1.)

    def test_single_structural_class_has_no_selection_regret(self):
        self.assertEqual(candidate_interval_regret({'a':100.},{'a':0.},'a'),0.)


if __name__=='__main__':unittest.main()
