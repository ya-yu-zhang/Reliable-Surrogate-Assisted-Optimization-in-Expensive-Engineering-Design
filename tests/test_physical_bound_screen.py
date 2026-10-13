import unittest
from copy import deepcopy

import numpy as np

from src.physical_bound_screen import future_pool, metadata_cases


class PhysicalScreenTests(unittest.TestCase):
    def case(self, continuation='mean'):
        return {'dataset': 'previous_holdout', 'block': 10, 'state': 's', 'source': 'ei',
                'classes': {'b0': ['mean'], 'b1': ['ei']}, 'baseline': 'b0', 'initial': 100.,
                'X': [[.5] * 19], 'continuation': continuation,
                'curves': {'b0': [{'incumbent': 100.}] * 6}}

    def test_future_labels_do_not_enter_metadata_plan(self):
        one = self.case()
        two = deepcopy(one)
        two['curves']['b0'][-1] = {'incumbent': 1.}
        self.assertEqual(metadata_cases([one]), metadata_cases([two]))

    def test_two_continuations_share_physical_pool_without_becoming_new_states(self):
        self.assertEqual(len(metadata_cases([self.case(), self.case('ei')])), 1)
        cfg = {'previous_holdout': {'master_seed': 2026101207, 'source_controls': ['ei', 'pi', 'lcb'], 'pool_power': 10}}
        a, seed = future_pool(self.case(), 1, cfg)
        b, seed2 = future_pool(self.case('ei'), 1, cfg)
        np.testing.assert_array_equal(a, b)
        self.assertEqual(seed, seed2)

    def test_pool_namespace_matches_frozen_previous_holdout_rule(self):
        from scipy.stats import qmc
        cfg = {'previous_holdout': {'master_seed': 2026101207, 'source_controls': ['ei', 'pi', 'lcb'], 'pool_power': 10}}
        result, seed = future_pool(self.case(), 3, cfg)
        expected = int(np.random.SeedSequence([2026101207, 10, 0, 5, 3]).generate_state(1)[0])
        self.assertEqual(seed, expected)
        np.testing.assert_array_equal(result, qmc.Sobol(19, scramble=True, seed=expected).random_base2(10))

    def test_archived_pool_namespace_matches_its_separate_frozen_rule(self):
        from scipy.stats import qmc
        case = self.case()
        case.update(dataset='archived_common_mean', block=7, source='gp_ucb_shared_init')
        cfg = {'archived_common_mean': {'master_seed': 20261012, 'source_methods':
               ['gp_ei_shared_init', 'gp_pi_shared_init', 'gp_ucb_shared_init'], 'pool_power': 10}}
        pool, seed = future_pool(case, 4, cfg)
        expected = int(np.random.SeedSequence([20261012, 2, 7, 4]).generate_state(1)[0])
        self.assertEqual(seed, expected)
        np.testing.assert_array_equal(pool, qmc.Sobol(19, scramble=True, seed=expected).random_base2(10))


if __name__ == '__main__':
    unittest.main()
