"""Prospective, label-separated acquisition pilots and engineering workflows."""
from __future__ import annotations
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import Counter
import hashlib
import importlib.metadata
import json
from pathlib import Path
import time
import warnings
import numpy as np
from scipy.optimize import minimize
from scipy.special import ndtr
from scipy.stats import qmc
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/engineering_optimization_transfer.json"


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2) + "\n")
    tmp.replace(path)


def seed(cfg, condition, rep, namespace, step=0):
    return int(np.random.SeedSequence([cfg["master_seed"], condition, rep,
                                      namespace, step]).generate_state(1)[0])


def sobol(n_power, random_seed):
    return qmc.Sobol(19, scramble=True, seed=random_seed).random_base2(n_power)


def policy_choice(mu, sd, incumbent, scale, policy, cfg):
    safe = np.maximum(sd, 1e-15)
    improvement = incumbent - mu - cfg["xi"] * scale
    z = improvement / safe
    if policy == "mean":
        score = -mu
    elif policy == "ei":
        score = improvement * ndtr(z) + safe * np.exp(-0.5*z*z)/np.sqrt(2*np.pi)
    elif policy == "pi":
        score = ndtr(z)
    elif policy == "lcb":
        score = -mu + cfg["kappa"] * sd
    else:
        raise ValueError(policy)
    return int(np.argmax(score))


def select_policy(endpoints, priority):
    return min(priority, key=lambda p: (endpoints[p], priority.index(p)))


def fit_choice(X, y, pool, policy, cfg):
    def optimizer(objective, initial_theta, bounds):
        result = minimize(objective, initial_theta, method="L-BFGS-B", jac=True,
                          bounds=bounds, options={"maxiter": cfg["gp_optimizer_maxiter"]})
        return result.x, result.fun
    kernel = ConstantKernel(1., tuple(cfg["constant_bounds"])) * Matern(
        cfg["length_scale"], tuple(cfg["length_scale_bounds"]), nu=2.5)
    gp = GaussianProcessRegressor(kernel=kernel, alpha=cfg["alpha"],
                                  normalize_y=True, optimizer=optimizer,
                                  n_restarts_optimizer=cfg["gp_restarts"])
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        gp.fit(X, y)
        mu, sd = gp.predict(pool, return_std=True)
    index = policy_choice(mu, sd, float(np.min(y)), max(float(np.std(y)), 1e-12), policy, cfg)
    return pool[index], {"pool_index": index, "mu": float(mu[index]),
                         "sd": float(sd[index]), "kernel_theta": gp.kernel_.theta.tolist(),
                         "warnings": [str(w.message) for w in captured]}


class Ledger:
    def __init__(self, folder, cap, objective):
        folder.mkdir(parents=True, exist_ok=True)
        self.journal = (folder / "events.jsonl").open("x", encoding="utf-8")
        self.folder, self.cap, self.objective = folder, cap, objective
        self.calls = 0
        self.fe_seconds = Counter()
        self.gp_seconds = Counter()
        self.workflow_calls = Counter()

    def log(self, event):
        self.journal.write(json.dumps(event, separators=(",", ":")) + "\n")
        self.journal.flush()

    def evaluate(self, x, workflow, phase, policy, t, metadata=None):
        if self.calls >= self.cap:
            raise RuntimeError("Physical call cap reached")
        call_id = self.calls + 1
        self.log({"event": "pre", "call_id": call_id, "workflow": workflow,
                  "phase": phase, "policy": policy, "t": t, "x": x.tolist(),
                  **(metadata or {})})
        self.calls += 1
        self.workflow_calls[workflow] += 1
        started = time.perf_counter()
        try:
            value = float(self.objective(x))
            if not np.isfinite(value) or value <= 0:
                raise FloatingPointError("Invalid compliance")
        except Exception as exc:
            elapsed = time.perf_counter() - started
            self.fe_seconds[workflow] += elapsed
            self.log({"event": "failure", "call_id": call_id, "error": repr(exc),
                      "seconds": elapsed})
            self.checkpoint(False)
            raise
        elapsed = time.perf_counter() - started
        self.fe_seconds[workflow] += elapsed
        self.log({"event": "label", "call_id": call_id, "y": value, "seconds": elapsed})
        if self.calls % 20 == 0:
            self.checkpoint(False)
        return value

    def checkpoint(self, complete):
        write_json(self.folder / "progress.json", {"physical_calls": self.calls,
                   "workflow_calls": dict(self.workflow_calls), "complete": complete})


def run_policy(ledger, X0, y0, cfg, condition, rep, workflow, phase, policy, steps):
    X, y = X0.copy(), y0.copy()
    ledger.log({"event": "history_start", "workflow": workflow, "phase": phase,
                "policy": policy, "initial_observations": len(y),
                "initial_sha256": hashlib.sha256(X.tobytes()+y.tobytes()).hexdigest(),
                "pilot_labels_in_training": False})
    curve = [float(y.min())]
    for step in range(steps):
        started = time.perf_counter()
        pool_seed = seed(cfg, condition, rep, 55 if phase == "pilot" else 56, step)
        pool = sobol(cfg["pool_power"], pool_seed)
        observed = {row.tobytes() for row in X}
        pool = np.array([row for row in pool if row.tobytes() not in observed])
        if not len(pool):
            raise ValueError("No unobserved candidates")
        x, metadata = fit_choice(X, y, pool, policy, cfg)
        elapsed = time.perf_counter() - started
        ledger.gp_seconds[workflow] += elapsed
        metadata.update({"observations_before": len(y), "best_before": float(y.min()),
                         "pool_seed": pool_seed, "gp_seconds": elapsed})
        value = ledger.evaluate(x, workflow, phase, policy, len(y)+1, metadata)
        X = np.vstack((X, x)); y = np.append(y, value)
        curve.append(float(y.min()))
    return {"best": float(y.min()), "curve": curve, "observations": len(y)}


def run_case(cfg, condition, rep):
    from engibench.problems.beams2d.v1 import Beams2D
    from .engineering_beam_adapter import density_field
    name = f"load{condition}_r{rep:02d}"
    folder = ROOT / cfg["out"] / name
    # Beams2D caches the force-dependent FE state. Configure once, per case.
    problem = Beams2D(seed=0, config={"forcedist": cfg["forcedist"][condition]})
    objective = lambda x: problem.simulate(density_field(x))[0]
    ledger = Ledger(folder, cfg["case_call_cap"], objective)
    started = time.perf_counter()
    versions = {p: importlib.metadata.version(p) for p in
                ["numpy", "scipy", "scikit-learn", "engibench", "cvxopt"]}
    assert versions == {"numpy":"2.2.6", "scipy":"1.15.3", "scikit-learn":"1.7.2",
                        "engibench":"0.2.0", "cvxopt":"1.3.2"}, versions
    ledger.log({"event":"meta", "condition":condition, "forcedist":cfg["forcedist"][condition],
                "repeat":rep, "config_sha256":hashlib.sha256(CONFIG.read_bytes()).hexdigest(),
                "code_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "versions":versions})
    X0 = sobol(6, seed(cfg, condition, rep, 11))[:cfg["initial"]]
    y0 = np.array([ledger.evaluate(x, "audited", "initial", None, i+1)
                   for i, x in enumerate(X0)])
    pilots = {p:run_policy(ledger, X0, y0, cfg, condition, rep, "audited", "pilot", p,
                           cfg["pilot_steps"]) for p in cfg["policies"]}
    selected = select_policy({p:d["best"] for p,d in pilots.items()}, cfg["tie_priority"])
    ledger.log({"event":"selection", "selected":selected,
                "pilot_endpoints":{p:d["best"] for p,d in pilots.items()},
                "calls_before_validation":ledger.calls, "pilot_labels_discarded":True})
    audited = run_policy(ledger, X0, y0, cfg, condition, rep, "audited", "canonical", selected,
                         cfg["budget"]-cfg["initial"])
    y_portfolio = np.array([ledger.evaluate(x, "portfolio", "initial", None, i+1)
                            for i,x in enumerate(X0)])
    if not np.allclose(y0, y_portfolio, rtol=cfg["canonical_replay_rtol"], atol=0):
        raise AssertionError("Independently paid initialization replay differs")
    portfolio = {p:run_policy(ledger, X0, y_portfolio, cfg, condition, rep,
                              "portfolio", "canonical", p, cfg["budget"]-cfg["initial"])
                 for p in cfg["policies"]}
    if not np.allclose(audited["curve"], portfolio[selected]["curve"],
                       rtol=cfg["canonical_replay_rtol"], atol=0):
        raise AssertionError("Selected canonical replay differs")
    assert ledger.calls == cfg["case_call_cap"] == 906
    assert ledger.workflow_calls == {"audited":280, "portfolio":626}
    summary = {"case":name, "condition":condition, "forcedist":cfg["forcedist"][condition],
               "repeat":rep, "initial_best":float(y0.min()), "pilots":pilots,
               "selected":selected, "audited":audited, "portfolio":portfolio,
               "physical_calls":ledger.calls, "workflow_calls":dict(ledger.workflow_calls),
               "fe_seconds":dict(ledger.fe_seconds), "gp_seconds":dict(ledger.gp_seconds),
               "observed_wall_seconds":time.perf_counter()-started, "complete":True}
    ledger.log({"event":"complete", "physical_calls":ledger.calls})
    ledger.journal.close(); ledger.checkpoint(True)
    summary["journal_sha256"] = hashlib.sha256((folder/"events.jsonl").read_bytes()).hexdigest()
    write_json(folder / "summary.json", summary)
    return {k:summary[k] for k in ["case", "selected", "physical_calls", "observed_wall_seconds"]}


def main():
    cfg = json.loads(CONFIG.read_text())
    out = ROOT / cfg["out"]
    if out.exists():
        raise FileExistsError("Existing scientific outputs: inspect; do not automatically rerun")
    assert cfg["case_call_cap"]*len(cfg["forcedist"])*cfg["repeats"] == cfg["global_call_cap"]
    out.mkdir(parents=True)
    write_json(out / "run_status.json", {"complete":False, "cases_completed":0, "config":cfg})
    cases = [(c,r) for c in range(len(cfg["forcedist"])) for r in range(cfg["repeats"])]
    completed = []
    with ProcessPoolExecutor(max_workers=cfg["workers"]) as executor:
        futures = {executor.submit(run_case,cfg,c,r):(c,r) for c,r in cases}
        for future in as_completed(futures):
            try:
                item = future.result()
            except Exception as exc:
                for f in futures: f.cancel()
                write_json(out/"run_status.json", {"complete":False, "error":repr(exc),
                           "cases_completed":len(completed), "completed":completed, "config":cfg})
                raise
            completed.append(item)
            write_json(out/"run_status.json", {"complete":len(completed)==len(cases),
                       "cases_completed":len(completed), "completed":completed, "config":cfg})
            print(json.dumps(item), flush=True)


if __name__ == "__main__":
    main()
