import math
import random
import unittest
from fractions import Fraction

from src.budgeted_decision_audit import Observation
from src.monotone_horizon_audit import audit, effect_interval


class MonotoneHorizonTests(unittest.TestCase):
    def run_reader(self, base, alternative, **kw):
        curves = {"b": base, "a": alternative}
        exposed = {b: -1 for b in curves}

        def observe(branch, step):
            self.assertEqual(step, exposed[branch] + 1)
            exposed[branch] = step
            return Observation(curves[branch][step], f"ctx:{branch}:{step}")

        return audit({"b": ["mean", "pi"], "a": ["ei", "lcb"]}, "b",
                     observe, 100., **kw)

    def test_early_better_has_no_measured_effect(self):
        r = self.run_reader([100.] * 6, [80.] * 6, mode="baseline_depth")
        self.assertEqual(r["labels"]["ei"], "better")
        self.assertEqual(r["requests"], 7)
        self.assertIsNone(r["measured_effects"]["ei"])
        self.assertEqual(r["depth"]["a"], 0)
        self.assertTrue(r["selection"]["certified"])
        self.assertEqual(r["selection"]["additional_requests_to_complete_selected"], 5)

    def test_early_worse_and_realization_cost(self):
        r = self.run_reader([70.] * 6, [100.] * 6, mode="h0_largest_upper")
        self.assertEqual(r["labels"]["ei"], "worse")
        self.assertEqual(r["requests"], 7)
        self.assertEqual(r["selection"]["branch"], "b")
        self.assertEqual(r["requests"] + r["selection"]["additional_requests_to_complete_selected"], 12)
        self.assertTrue(r["selection"]["certified"])

    def test_h0_tie_cannot_certify_delayed_benefit(self):
        r = self.run_reader([100.] * 6, [100.] * 5 + [80.], budget=2, mode="h0_largest_upper")
        self.assertEqual(r["labels"]["ei"], "abstain")
        self.assertFalse(r["selection"]["certified"])
        completed = self.run_reader([100.] * 6, [100.] * 5 + [80.])
        self.assertEqual(completed["labels"]["ei"], "better")
        self.assertEqual(completed["requests"], 12)

    def test_unread_future_cannot_change_reader_output(self):
        one = self.run_reader([100.] * 6, [80.] * 6)
        two = self.run_reader([100.] * 6, [80., 75., 70., 65., 60., 55.])
        self.assertEqual(one, two)

    def test_complete_pair_keeps_v1_threshold_boundary(self):
        a = 99.9
        margin = (100. - a) / 100.
        r = self.run_reader([100.] * 6, [a] * 6, margin=margin)
        self.assertEqual(r["labels"]["ei"], "tie")
        self.assertEqual(r["requests"], 12)
        self.assertEqual(r["measured_effects"]["ei"], margin)

    def test_outward_interval_contains_exact_float_arithmetic(self):
        for base, alternative in [((0., 100.), (99.9, 99.9)), ((100., 100.), (0., 99.9)),
                                  ((0., 1e-200), (0., 1e-200)), ((0., 1e200), (0., 1e200))]:
            low, high = effect_interval(base, alternative, 100.)
            exact_low = (Fraction(base[0]) - Fraction(alternative[1])) / 100
            exact_high = (Fraction(base[1]) - Fraction(alternative[0])) / 100
            self.assertLessEqual(Fraction(low), exact_low)
            self.assertGreaterEqual(Fraction(high), exact_high)

    def test_same_action_needs_no_category_requests(self):
        def forbidden(*_):
            self.fail("Aliases must not request labels")
        r = audit({"b": ["mean", "ei"]}, "b", forbidden, 100.)
        self.assertEqual(r["requests"], 0)
        self.assertEqual(r["labels"], {"mean": "tie", "ei": "tie"})
        self.assertTrue(r["selection"]["certified"])
        self.assertEqual(r["selection"]["additional_requests_to_complete_selected"], 6)

    def test_identical_outcomes_do_not_merge_distinct_actions(self):
        r = self.run_reader([100.] * 6, [100.] * 6)
        self.assertEqual(r["requests"], 12)
        self.assertEqual(r["reasons"]["ei"], "measured_target_horizon")

    def test_invalid_incumbent_or_bound_is_rejected(self):
        with self.assertRaises(ValueError):
            self.run_reader([100., 101.] + [100.] * 4, [100.] * 6)
        with self.assertRaises(ValueError):
            self.run_reader([100.] * 6, [-1.] * 6)
        with self.assertRaises(ValueError):
            self.run_reader([math.nan] * 6, [100.] * 6)

    def test_categories_do_not_certify_which_of_two_better_branches_to_select(self):
        curves = {"b": [100.] * 6, "a": [80.] * 6, "c": [90.] * 5 + [60.]}

        def run(target):
            exposed = {b: -1 for b in curves}
            def observe(b, step):
                self.assertEqual(step, exposed[b] + 1)
                exposed[b] = step
                return Observation(curves[b][step], f"ctx:{b}:{step}")
            return audit({"b": ["mean"], "a": ["ei"], "c": ["pi"]}, "b", observe, 100.,
                         budget=18, target=target)
        categories = run("categories")
        self.assertEqual(categories["requests"], 8)
        self.assertTrue(categories["all_categories_certified"])
        self.assertFalse(categories["selection"]["certified"])
        joint = run("categories_and_selection")
        self.assertEqual(joint["requests"], 18)
        self.assertTrue(joint["target_satisfied"])
        self.assertEqual(joint["selection"]["branch"], "c")
        self.assertGreater(joint["requests"], categories["requests"])

    def test_all_permutations_have_correct_full_budget_labels(self):
        for base, alt in [([100.] * 6, [80.] * 6), ([70.] * 6, [100.] * 6),
                          ([100.] * 6, [100.] * 5 + [80.]), ([100.] * 6, [100.] * 6)]:
            for mode in ["baseline_depth", "alternative_depth", "fixed_breadth", "h0_largest_upper"]:
                r = self.run_reader(base, alt, mode=mode)
                expected = "better" if base[-1] > alt[-1] else "worse" if base[-1] < alt[-1] else "tie"
                self.assertEqual(r["labels"]["ei"], expected)
                self.assertEqual(r["labels"]["mean"], "tie")

    def test_random_prefixes_never_certify_an_incorrect_category_or_selection(self):
        rng = random.Random(2026101301)
        for _ in range(25):
            curves = {b: sorted([rng.uniform(0., 100.) for _ in range(6)], reverse=True)
                      for b in ["b", "a", "c"]}
            for mode in ["baseline_depth", "alternative_depth", "fixed_breadth", "h0_largest_upper"]:
                for target in ["categories", "categories_and_selection"]:
                    for budget in [0, 1, 3, 7, 12, 18]:
                        exposed = {b: -1 for b in curves}
                        def observe(b, step):
                            self.assertEqual(step, exposed[b] + 1)
                            exposed[b] = step
                            return Observation(curves[b][step], f"ctx:{b}:{step}")
                        r = audit({"b": ["mean"], "a": ["ei"], "c": ["pi"]}, "b", observe,
                                  100., budget=budget, mode=mode, target=target)
                        for b in ["a", "c"]:
                            effect = (curves["b"][-1] - curves[b][-1]) / 100.
                            label = "better" if effect > .001 else "worse" if effect < -.001 else "tie"
                            self.assertIn(r["branch_labels"][b], {"abstain", label})
                            low, high = r["effect_intervals"]["ei" if b == "a" else "pi"]
                            self.assertLessEqual(low, effect)
                            self.assertGreaterEqual(high, effect)
                        if r["selection"]["certified"]:
                            chosen = r["selection"]["branch"]
                            regret = curves[chosen][-1] - min(c[-1] for c in curves.values())
                            self.assertLessEqual(regret, .1)
                            if r["terminal_bounds"][chosen][1] > .1:
                                self.assertTrue(all(r["depth"][b] == 5 for b in curves if b != chosen))
                                self.assertEqual(r["requests"] + r["selection"]["additional_requests_to_complete_selected"], 18)


if __name__ == "__main__":
    unittest.main()
