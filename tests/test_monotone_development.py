import unittest

from src.analyze_monotone_development import assess, read_prefix


class MonotoneDevelopmentTests(unittest.TestCase):
    def case(self):
        curves = {b: [{"incumbent": y, "point_key": f"ctx:{b}:{s}"}
                      for s, y in enumerate(yy)]
                  for b, yy in {"b": [70.] * 6, "a": [100.] * 6}.items()}
        return {"classes": {"b": ["mean", "ei", "pi"], "a": ["lcb"]},
                "baseline": "b", "initial": 100., "curves": curves, "X": []}

    def test_request_reduction_is_erased_after_selected_completion(self):
        case = self.case()
        old = read_prefix(case, "v1_fixed_depth", 18, .001)
        candidate = read_prefix(case, "h0_largest_upper", 18, .001)
        strong = read_prefix(case, "alternative_depth", 18, .001)
        old_cost, _, _ = assess(case, old, .001)
        new_cost, _, _ = assess(case, candidate, .001)
        simple_cost, _, _ = assess(case, strong, .001)
        self.assertEqual((old_cost["requests"], new_cost["requests"]), (12, 7))
        self.assertEqual(new_cost["audit_plus_selected_completion_requests"], old_cost["requests"])
        self.assertEqual(new_cost, simple_cost)

    def test_response_ties_are_not_action_aliases(self):
        case = self.case()
        for r in case["curves"]["a"]:
            r["incumbent"] = 70.
        r = read_prefix(case, "h0_largest_upper", 18, .001)
        metrics, _, _ = assess(case, r, .001)
        self.assertEqual(metrics["requests"], 12)
        self.assertEqual(metrics["contrasts"], 1)
        self.assertEqual(metrics["early_certificates"], 0)

    def test_unseen_future_is_only_used_for_grading_after_reader_finishes(self):
        case = self.case()
        r1 = read_prefix(case, "h0_largest_upper", 2, .001)
        case["curves"]["a"][-1]["incumbent"] = 20.
        r2 = read_prefix(case, "h0_largest_upper", 2, .001)
        self.assertEqual(r1, r2)
        before, truth, _ = assess(case, r2, .001)
        self.assertEqual(truth["a"], "better")
        self.assertEqual(before["abstained_positives"], 1)
        self.assertEqual(before["false_eliminations"], 0)


if __name__ == "__main__":
    unittest.main()
