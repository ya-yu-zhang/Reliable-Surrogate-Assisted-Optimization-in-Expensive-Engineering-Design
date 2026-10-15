"""Numerical program cases, not independent engineering optimization samples."""
from fractions import Fraction
import math
import random
import unittest
from src.certified_affine_envelope import coefficient_bands,check_exclusion
from src.filtered_exact_action_sets import integer_envelope_from_bands,filtered_pairwise_from_bands
from tests.test_certified_affine_envelope import all_pairs_oracle


class ExactActionSetTests(unittest.TestCase):
    def compare(self,bands,domain=0.):
        expected = all_pairs_oracle(bands,domain)
        for algorithm in [integer_envelope_from_bands,filtered_pairwise_from_bands]:
            result = algorithm(*bands,response_lower=domain)
            self.assertEqual(result['exact_intervals'],expected)
            self.assertEqual(result['indices'],sorted(expected))
            self.assertEqual(len(result['indices'])+len(result['excluded_proofs']),len(bands[0]))
            for proof in result['excluded_proofs']:
                self.assertLessEqual(len(proof)-1,2)
                self.assertTrue(check_exclusion(*bands,proof,domain))
        return expected

    def test_isolated_tie_and_closed_domain(self):
        bands=coefficient_bands([0.,1.,-1.],[1.,0.,2.])
        for domain in [0.,1.,1.5,10.]:self.compare(bands,domain)
        self.assertEqual(self.compare(bands)[0],(Fraction(1),Fraction(1)))

    def test_duplicate_parallel_candidates(self):
        self.assertEqual(list(self.compare(coefficient_bands([0.,0.,0.],[1.,1.,2.]))),[0,1])

    def test_float_proposal_overflow_does_not_remove_actions(self):
        self.compare(coefficient_bands([-1e308,1e308,0.],[1e308,-1e308,0.]))

    def test_subnormal_and_mixed_exponents(self):
        tiny=math.ulp(0.)
        self.compare(coefficient_bands([tiny,-tiny,0.],[tiny,0.,2*tiny]))
        self.compare(coefficient_bands([tiny,1.,-1e100],[1.,tiny,1e100]))

    def test_random_interval_bands_against_fraction_oracle(self):
        rng=random.Random(58)
        for _ in range(45):
            n=rng.randrange(1,18)
            self.compare(coefficient_bands([rng.uniform(-4,4) for _ in range(n)],
                [rng.uniform(-8,8) for _ in range(n)],
                [rng.choice([0.,.01,.5]) for _ in range(n)],
                [rng.choice([0.,.01,.5]) for _ in range(n)]),rng.uniform(0,3))

    def test_nominal_envelope_cannot_replace_band_contract(self):
        a=[0.,0.,1.,-1.];b=[1.,33/32,0.,2.]
        self.assertNotIn(1,self.compare(coefficient_bands(a,b)))
        bands=coefficient_bands(a,b);bands[1][1]=31/32;bands[3][1]=35/32
        self.assertEqual(self.compare(bands)[1],(Fraction(31,32),Fraction(33,32)))
