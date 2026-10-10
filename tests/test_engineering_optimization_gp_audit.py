"""Scientific integrity checks on synthetic fixtures, not engineering evidence."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from src import engineering_optimization_gp_audit as audit


class GPAuditTests(unittest.TestCase):
    def cfg(self, limit=4):
        return {"controls": ["mean", "ei", "pi", "lcb"], "xi_scale": .01, "kappa": 2.,
                "dimension": 2, "optimizer_budget": 3, "shared_initial_evaluations": 1,
                "repeats": 1, "checkpoints": [3], "sobol_power": 2,
                "max_new_diagnostic_calls": limit, "source_roots": {"gp_pi_shared_init": "archive"},
                "out": "audit"}

    def test_analytic_acquisitions_zero_variance_and_ties(self):
        cfg = self.cfg()
        values = audit.scores([0., 0., 2.], [0., 0., 0.], 1., 1., cfg)
        np.testing.assert_array_equal(values["ei"], [1., 1., 0.])
        np.testing.assert_array_equal(values["pi"], [1., 1., 0.])
        self.assertEqual(int(np.argmax(values["ei"])), 0)
        values = audit.scores([0., .5], [0., 2.], 1., 1., cfg)
        self.assertEqual(int(np.argmax(values["mean"])), 0)
        self.assertEqual(int(np.argmax(values["lcb"])), 1)
        with self.assertRaises(ValueError):
            audit.scores([0.], [-1.], 1., 1., cfg)

    def test_frozen_reader_never_parses_current_or_future_labels(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "events.jsonl"
            rows = [{"event": "meta", "seed": 1},
                    {"event": "pre", "t": 1, "n_observed": 0, "x_unit": [0., 0.]},
                    {"event": "label", "t": 1, "y": 4.},
                    {"event": "pre", "t": 2, "n_observed": 1, "x_unit": [1., 1.]}]
            path.write_text("\n".join(map(json.dumps, rows)) + "\nTHIS IS NOT JSON AND MUST NOT BE READ\n")
            _, xx, yy, pre = audit.frozen_state(path, 2)
            np.testing.assert_array_equal(xx, [[0., 0.]])
            np.testing.assert_array_equal(yy, [4.])
            self.assertEqual(pre["t"], 2)

    def test_model_replay_and_future_outcome_invariance(self):
        from sklearn.gaussian_process import GaussianProcessRegressor
        from sklearn.gaussian_process.kernels import ConstantKernel, Matern

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "events.jsonl"
            cfg = self.cfg()
            cfg.update(prediction_rtol=1e-8, prediction_atol=1e-8)
            xx, yy = np.array([[0., 0.], [1., 1.]]), np.array([4., 1.])
            selected = np.array([.3, .4])
            kernel = ConstantKernel(1., (.05, 20)) * Matern(np.full(2, .2), (.005, 2.), nu=2.5)
            model = GaussianProcessRegressor(kernel=kernel, alpha=1e-6, normalize_y=True, optimizer=None).fit(xx, yy)
            mu, sd = model.predict(selected[None], return_std=True)
            rows = [{"event": "meta", "seed": 1, "packages":
                     {p: audit.importlib.metadata.version(p) for p in ["numpy", "scipy", "scikit-learn"]}}]
            for t, point, label in zip([1, 2], xx, yy):
                rows += [{"event": "pre", "t": t, "n_observed": t - 1, "x_unit": point.tolist()},
                         {"event": "label", "t": t, "y": float(label)}]
            rows.append({"event": "pre", "t": 3, "n_observed": 2, "x_unit": selected.tolist(),
                         "optimizer_state": {"training_count": 2, "kernel_theta": kernel.theta.tolist(),
                                             "mu": float(mu[0]), "sd": float(sd[0])}})
            prefix = "\n".join(map(json.dumps, rows)) + "\n"
            path.write_text(prefix + json.dumps({"event": "label", "t": 3, "y": -1e10}) + "\n")
            first = audit.snapshot(path, 3, cfg)
            path.write_text(prefix + json.dumps({"event": "label", "t": 3, "y": 1e10}) + "\n")
            second = audit.snapshot(path, 3, cfg)
            self.assertEqual(first, second)
            self.assertTrue(first["source_prediction_replayed"])
            rows[-1]["optimizer_state"]["mu"] += 1.
            path.write_text("\n".join(map(json.dumps, rows)) + "\n")
            with self.assertRaises(RuntimeError):
                audit.snapshot(path, 3, cfg)

    def fixture(self, root, cfg):
        out = root / cfg["out"]
        out.mkdir()
        source = root / "source.jsonl"
        source.write_text(json.dumps({"event": "pre", "t": 3, "x_unit": [0., 0.]}) + "\n"
                          + json.dumps({"event": "label", "t": 3, "y": 2.}) + "\n")
        frozen = {"training_best": 5., "scale": 1., "pool": [[0., 0.], [.5, .5]], "source_selected": [0., 0.],
                  "decisions": {"mean": 0, "ei": 1, "pi": 1, "lcb": 1}}
        audit.write_json(out / "state.json", frozen)
        item = {"method": "gp_pi_shared_init", "rep": 0, "t": 3, "snapshot": "state.json",
                "snapshot_sha256": audit.digest(out / "state.json"), "source_events": "source.jsonl",
                "source_sha256": audit.digest(source)}
        manifest = {"status": "frozen", "config": cfg, "code_sha256": audit.digest(audit.__file__), "states": [item]}
        audit.write_json(out / "manifest.json", manifest)
        return out

    def test_labels_deduplicated_and_precedes_call(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            cfg = self.cfg()
            out = self.fixture(root, cfg)
            calls = []

            def objective(point):
                events = [json.loads(s) for s in (out / "diagnostic_events.jsonl").read_text().splitlines()]
                self.assertEqual(events[-1]["event"], "diagnostic_pre")
                calls.append(point.copy())
                return 1.

            result = audit.evaluate(cfg, root, objective)
            self.assertEqual(len(calls), 1)
            self.assertEqual(result["new_physical_calls"], 1)
            self.assertEqual(result["reused_source_labels"], 1)
            self.assertEqual(result["promotion"], "not assessed")
            utilities = json.loads((out / "common_state_results.json").read_text())["states"][0]["utility"]
            self.assertEqual(utilities, {"mean": 3., "ei": 4., "pi": 4., "lcb": 4.})
            with self.assertRaises(FileExistsError):
                audit.evaluate(cfg, root, objective)

    def test_corrupted_input_rejected_before_any_call(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            cfg = self.cfg()
            out = self.fixture(root, cfg)
            (out / "state.json").write_text("{}")
            with self.assertRaises(ValueError):
                audit.evaluate(cfg, root, lambda point: self.fail("Unexpected objective call"))
            self.assertFalse((out / "diagnostic_events.jsonl").exists())

    def test_failed_attempt_still_counted(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            cfg = self.cfg()
            out = self.fixture(root, cfg)

            def fail(point):
                raise RuntimeError("simulation failed")

            with self.assertRaises(RuntimeError):
                audit.evaluate(cfg, root, fail)
            counts = json.loads((out / "accounting.json").read_text())
            self.assertEqual(counts["new_physical_calls"], 1)
            self.assertFalse(counts["complete"])

    def test_call_budget_never_exceeded(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            cfg = self.cfg(limit=1)
            out = self.fixture(root, cfg)
            frozen = json.loads((out / "state.json").read_text())
            frozen["pool"].append([.75, .75])
            frozen["decisions"]["lcb"] = 2
            audit.write_json(out / "state.json", frozen)
            manifest = json.loads((out / "manifest.json").read_text())
            manifest["states"][0]["snapshot_sha256"] = audit.digest(out / "state.json")
            audit.write_json(out / "manifest.json", manifest)
            calls = []
            with self.assertRaises(RuntimeError):
                audit.evaluate(cfg, root, lambda p: calls.append(p) or 1.)
            self.assertEqual(len(calls), 1)
            self.assertEqual(json.loads((out / "accounting.json").read_text())["new_physical_calls"], 1)


if __name__ == "__main__":
    unittest.main()
