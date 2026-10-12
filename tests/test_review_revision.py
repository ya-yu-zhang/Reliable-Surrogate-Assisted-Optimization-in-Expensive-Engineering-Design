import unittest
from src.analyze_review_revision import completion_capacity, replay


class ReviewRevisionTests(unittest.TestCase):
    def state(self):
        curves = {
            'b0': [{'incumbent': 100., 'point_key': f'ctx:m{i}'} for i in range(6)],
            'b1': [{'incumbent': 100. if i < 5 else 80., 'point_key': f'ctx:e{i}'} for i in range(6)],
            'b2': [{'incumbent': 100., 'point_key': f'ctx:p{i}'} for i in range(6)],
        }
        return {'classes': {'b0': ['mean'], 'b1': ['ei'], 'b2': ['pi', 'lcb']},
                'mapping': {'mean': 'b0', 'ei': 'b1', 'pi': 'b2', 'lcb': 'b2'},
                'initial_best': 100., 'X': [[.5] * 19], 'root_sd': {b: 1. for b in curves},
                'trajectories': {'mean': curves}}

    def test_capacity_requires_shared_baseline_and_complete_alternative(self):
        self.assertEqual(completion_capacity(3, 11), 0)
        self.assertEqual(completion_capacity(3, 12), 1)
        self.assertEqual(completion_capacity(3, 18), 2)
        self.assertEqual(completion_capacity(1, 0), 0)
        with self.assertRaises(ValueError):
            completion_capacity(3, 12.5)

    def test_same_coverage_can_have_different_missed_opportunity(self):
        state = self.state()
        forward = replay(state, 'mean', ['b0', 'b1', 'b2'], 12, .001)
        reverse = replay(state, 'mean', ['b0', 'b2', 'b1'], 12, .001)
        self.assertEqual(forward['classified'], reverse['classified'])
        self.assertEqual(forward['result']['requests'], reverse['result']['requests'])
        self.assertEqual(sum(x['missed_positive'] for x in forward['comparisons']), 0)
        self.assertEqual(sum(x['missed_positive'] for x in reverse['comparisons']), 1)
        self.assertEqual(forward['selection_regret_percent'], 0.)
        self.assertEqual(reverse['selection_regret_percent'], 20.)

    def test_orders_agree_when_budget_completes_every_class(self):
        state = self.state()
        forward = replay(state, 'mean', ['b0', 'b1', 'b2'], 18, .001)
        reverse = replay(state, 'mean', ['b0', 'b2', 'b1'], 18, .001)
        self.assertEqual(forward['result']['labels'], reverse['result']['labels'])
        self.assertEqual(forward['classified'], 2)
        self.assertEqual(reverse['selection_regret_percent'], 0.)

    def test_partial_first_action_does_not_certify_target(self):
        result = replay(self.state(), 'mean', ['b0', 'b1', 'b2'], 11, .001)
        self.assertEqual(result['classified'], 0)
        self.assertEqual(result['result']['reasons']['ei'], 'budget_insufficient_for_target_horizon')


if __name__ == '__main__':
    unittest.main()
