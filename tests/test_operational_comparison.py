import unittest

from src.analyze_operational_comparison import calibration, read_grouped, read_named


class OperationalComparisonTests(unittest.TestCase):
    def state(self, alias=False):
        branches = {"b0": ["mean", "ei", "pi", "lcb"]} if alias else {"b0": ["mean", "pi"], "b1": ["ei", "lcb"]}
        curves = {b: [{"incumbent": 100. if b == "b0" or i < 5 else 80., "point_key": f"ctx:{b}:{i}"}
                      for i in range(6)] for b in branches}
        return {"classes": branches, "mapping": {n: b for b, nn in branches.items() for n in nn},
                "root_sd": {b: 1. for b in branches}, "initial_best": 100.,
                "trajectories": {"mean": curves}, "root_ei": {b: .02 for b in branches},
                "calibration": {"nrmse": .1, "coverage90": 1.}}

    def test_alias_only_needs_no_target_requests_but_naive_reader_charges_24(self):
        s = self.state(True)
        plain = read_named(s, "mean", 24, .001)
        grouped = read_grouped(s, "mean", 18, .001, "fixed_depth")
        self.assertEqual(plain["labels"], grouped["labels"])
        self.assertEqual((plain["requests"], grouped["requests"]), (24, 0))

    def test_later_positive_survives_full_target_but_partial_abstains(self):
        s = self.state()
        full = read_grouped(s, "mean", 12, .001, "fixed_depth")
        partial = read_grouped(s, "mean", 11, .001, "fixed_depth")
        self.assertEqual(full["labels"]["ei"], "better")
        self.assertEqual(partial["labels"]["ei"], "abstain")
        self.assertEqual(read_named(s, "mean", 24, .001)["labels"], full["labels"])

    def test_calibration_alias_skip_changes_cost_only(self):
        cfg = {"calibration_max_nrmse": .25, "calibration_min_coverage": .8,
               "relative_margin": .001, "calibration_points": 8}
        for alias in [False, True]:
            s = self.state(alias)
            old, new = calibration(s, cfg), calibration(s, cfg, True)
            self.assertEqual(old["labels"], new["labels"])
            self.assertEqual(new["requests"], 0 if alias else 8)


if __name__ == "__main__":
    unittest.main()
