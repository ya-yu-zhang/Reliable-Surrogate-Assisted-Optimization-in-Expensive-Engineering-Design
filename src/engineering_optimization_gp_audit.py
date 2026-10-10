"""Bounded common-state GP acquisition audit on archived beam histories.

No candidate label is consulted during planning. The source optimizer is never
updated. This diagnostic module alone does not establish closed-loop promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
from time import perf_counter

import numpy as np
from scipy.spatial.distance import cdist
from scipy.stats import norm, qmc

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/engineering_optimization_gp_audit.json"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def validate_config(cfg):
    if cfg["controls"] != ["mean", "ei", "pi", "lcb"]:
        raise ValueError("The protocol requires exactly the four prespecified controls")
    for name in ["dimension", "optimizer_budget", "shared_initial_evaluations", "repeats", "max_new_diagnostic_calls"]:
        if not isinstance(cfg[name], int) or cfg[name] <= 0:
            raise ValueError(f"Invalid integer setting: {name}")
    times = cfg["checkpoints"]
    if not times or times != sorted(set(times)) or any(not isinstance(t, int) or not cfg["shared_initial_evaluations"] < t <= cfg["optimizer_budget"] for t in times):
        raise ValueError("Invalid checkpoint schedule")
    if not isinstance(cfg["sobol_power"], int) or not 1 <= cfg["sobol_power"] <= 16:
        raise ValueError("Invalid candidate count")
    if cfg["xi_scale"] < 0 or cfg["kappa"] < 0 or not cfg["source_roots"]:
        raise ValueError("Invalid acquisition/history settings")


def scores(mu, sd, best, scale, cfg):
    mu, sd = np.asarray(mu, dtype=float), np.asarray(sd, dtype=float)
    if mu.ndim != 1 or sd.shape != mu.shape or not len(mu):
        raise ValueError("Prediction arrays must be nonempty one-dimensional peers")
    if not np.isfinite(mu).all() or not np.isfinite(sd).all() or np.any(sd < 0):
        raise ValueError("Invalid GP prediction")
    gain = best - mu
    z = np.divide(gain, sd, out=np.zeros_like(gain), where=sd > 1e-15)
    xi = cfg["xi_scale"] * scale
    pi_gain = gain - xi
    pi_z = np.divide(pi_gain, sd, out=np.zeros_like(gain), where=sd > 1e-15)
    # All scores are maximized; np.argmax uses the first index on ties.
    return {"mean": -mu,
            "ei": np.where(sd > 1e-15, gain * norm.cdf(z) + sd * norm.pdf(z), np.maximum(gain, 0)),
            "pi": np.where(sd > 1e-15, norm.cdf(pi_z), (pi_gain > 0).astype(float)),
            "lcb": -mu + cfg["kappa"] * sd}


def source_units(cfg, root=ROOT):
    for method, directory in cfg["source_roots"].items():
        for rep in range(cfg["repeats"]):
            runid = f"{method}_f01_d{cfg['dimension']}_i1_r{rep}_b{cfg['optimizer_budget']}"
            folder = root / directory / method / runid
            yield method, rep, folder / "events.jsonl", folder / "summary.json"


def preflight(cfg, root=ROOT):
    validate_config(cfg)
    required = [path for _, _, events, summary in source_units(cfg, root) for path in [events, summary]]
    missing = [str(p.relative_to(root)) for p in required if not p.is_file()]
    return {"ready": not missing, "required_files": len(required), "missing_files": missing,
            "expected_states": len(cfg["source_roots"]) * cfg["repeats"] * len(cfg["checkpoints"]),
            "worst_case_new_diagnostic_calls": len(cfg["controls"]) * len(cfg["source_roots"]) * cfg["repeats"] * len(cfg["checkpoints"]),
            "budget_limit": cfg["max_new_diagnostic_calls"], "new_objective_calls": 0}


def frozen_state(path, t):
    """Stop reading at PRE(t); do not parse LABEL(t) or any later event."""
    meta, points, labels, pending = None, [], [], None
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("event") == "meta":
                if meta is not None:
                    raise ValueError("Repeated metadata")
                meta = row
            elif row.get("event") == "pre":
                if pending is not None or row["t"] != len(labels) + 1 or row["n_observed"] != len(labels):
                    raise ValueError("Invalid PRE/LABEL ordering")
                if row["t"] == t:
                    if meta is None:
                        raise ValueError("Missing metadata")
                    return meta, np.asarray(points), np.asarray(labels), row
                pending = row
            elif row.get("event") == "label":
                if pending is None or row["t"] != pending["t"]:
                    raise ValueError("Label without matching prediction")
                points.append(pending["x_unit"])
                labels.append(float(row["y"]))
                pending = None
    raise ValueError(f"No frozen PRE record at {t}")


def snapshot(path, t, cfg):
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import ConstantKernel, Matern

    meta, xx, yy, pre = frozen_state(path, t)
    dim = cfg["dimension"]
    if xx.shape != (t - 1, dim) or not np.isfinite(xx).all() or not np.isfinite(yy).all():
        raise ValueError("Invalid training history")
    if np.any(xx < 0) or np.any(xx > 1) or t <= cfg["shared_initial_evaluations"]:
        raise ValueError("Invalid state domain/checkpoint")
    # Reconstruct the source fitted kernel, without optimizing it a second time.
    state = pre["optimizer_state"]
    selected = np.asarray(pre["x_unit"], dtype=float)
    if selected.shape != (dim,) or not np.isfinite(selected).all() or np.any(selected < 0) or np.any(selected > 1):
        raise ValueError("Invalid recorded source action")
    if state["training_count"] != len(yy):
        raise ValueError("Recorded training count differs")
    installed = {p: importlib.metadata.version(p) for p in ["numpy", "scipy", "scikit-learn"]}
    if any(meta["packages"][p] != installed[p] for p in installed):
        raise RuntimeError("Use the source journal's frozen numpy/scipy/scikit-learn versions")
    kernel = ConstantKernel(1., (.05, 20)) * Matern(np.full(dim, .2), (.005, 2.), nu=2.5)
    kernel = kernel.clone_with_theta(np.asarray(state["kernel_theta"]))
    model = GaussianProcessRegressor(kernel=kernel, alpha=1e-6, normalize_y=True,
                                     optimizer=None, random_state=meta["seed"])
    model.fit(xx, yy)
    sm, ss = model.predict(selected[None], return_std=True)
    if not np.allclose([sm[0], ss[0]], [state["mu"], state["sd"]],
                       rtol=cfg["prediction_rtol"], atol=cfg["prediction_atol"]):
        raise RuntimeError("Source prediction replay failed")
    sequence = qmc.Sobol(dim, scramble=True,
                          seed=np.random.default_rng(np.random.SeedSequence([meta["seed"], 721, t]))).random_base2(cfg["sobol_power"])
    sequence = sequence[cdist(sequence, xx).min(axis=1) >= 1e-10]
    # Include the recorded source action as a shared alternative. No refitting
    # or acquisition-specific continuous search is performed at this audit stage.
    pool = np.unique(np.vstack([sequence, selected]), axis=0)
    mu, sd = model.predict(pool, return_std=True)
    scale = float(yy.std()) or 1.0
    values = scores(mu, sd, float(yy.min()), scale, cfg)
    decisions = {name: int(np.argmax(values[name])) for name in cfg["controls"]}
    return {"t": t, "training_count": len(yy), "training_best": float(yy.min()), "scale": scale,
            "pool": pool.tolist(), "mu": mu.tolist(), "sd": sd.tolist(),
            "decisions": decisions, "source_selected": selected.tolist(),
            "kernel_theta": state["kernel_theta"], "source_prediction_replayed": True}


def freeze(cfg, config_path=CONFIG, root=ROOT):
    status = preflight(cfg, root)
    if not status["ready"]:
        raise FileNotFoundError(f"Missing {len(status['missing_files'])} source files; run --preflight")
    if status["worst_case_new_diagnostic_calls"] > cfg["max_new_diagnostic_calls"]:
        raise ValueError("Prespecified diagnostic budget is insufficient")
    out = root / cfg["out"]
    out.mkdir(parents=True, exist_ok=False)
    manifest = {"schema": 1, "status": "freezing", "config": cfg,
                "config_sha256": digest(config_path), "code_sha256": digest(__file__),
                "scientific_labels_acquired": False, "states": []}
    write_json(out / "manifest.json", manifest)
    start = perf_counter()
    for method, rep, events, summary in source_units(cfg, root):
        before = digest(events)
        for t in cfg["checkpoints"]:
            frozen = snapshot(events, t, cfg)
            name = f"{method}_r{rep}_t{t}.json"
            write_json(out / name, frozen)
            manifest["states"].append({"method": method, "rep": rep, "t": t,
                                        "snapshot": name, "snapshot_sha256": digest(out / name),
                                        "source_events": events.relative_to(root).as_posix(),
                                        "source_sha256": before, "summary_sha256": digest(summary)})
        if digest(events) != before:
            raise RuntimeError("Source journal changed during freezing")
    manifest.update(status="frozen", preparation_seconds=perf_counter() - start)
    write_json(out / "manifest.json", manifest)
    return manifest


def recorded_label(path, t, point):
    """Access an already-paid outcome only after audit selections are frozen."""
    selected = None
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("event") == "pre" and row["t"] == t:
                selected = row["x_unit"]
            if row.get("event") == "label" and row["t"] == t:
                return float(row["y"]) if np.array_equal(selected, point) else None
    raise ValueError("Missing recorded outcome")


def evaluate(cfg, root=ROOT, objective=None):
    validate_config(cfg)
    out = root / cfg["out"]
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    if manifest["status"] != "frozen" or manifest["config"] != cfg or manifest["code_sha256"] != digest(__file__):
        raise ValueError("Manifest is not an unchanged frozen plan")
    expected = {(method, rep, t) for method in cfg["source_roots"] for rep in range(cfg["repeats"]) for t in cfg["checkpoints"]}
    actual = [(item["method"], item["rep"], item["t"]) for item in manifest["states"]]
    if len(actual) != len(expected) or set(actual) != expected:
        raise ValueError("Incomplete or duplicate frozen-state design")
    # Preflight the complete frozen input BEFORE any expensive calls.
    for item in manifest["states"]:
        if digest(out / item["snapshot"]) != item["snapshot_sha256"] or digest(root / item["source_events"]) != item["source_sha256"]:
            raise ValueError("Frozen inputs changed")
        frozen = json.loads((out / item["snapshot"]).read_text(encoding="utf-8"))
        pool = np.asarray(frozen["pool"], dtype=float)
        if pool.ndim != 2 or pool.shape[1] != cfg["dimension"] or not np.isfinite(pool).all() or np.any(pool < 0) or np.any(pool > 1):
            raise ValueError("Invalid frozen candidate pool")
        if set(frozen["decisions"]) != set(cfg["controls"]) or any(not isinstance(i, int) or not 0 <= i < len(pool) for i in frozen["decisions"].values()):
            raise ValueError("Invalid frozen decision indices")
        if not np.isfinite(frozen["training_best"]) or not np.isfinite(frozen["scale"]) or frozen["scale"] <= 0:
            raise ValueError("Invalid frozen normalization")
        # Current outcomes may be checked only after all choices are frozen.
        source_value = recorded_label(root / item["source_events"], item["t"], frozen["source_selected"])
        if source_value is None or not np.isfinite(source_value):
            raise ValueError("Invalid archived source action/outcome")
    journal_path = out / "diagnostic_events.jsonl"
    if journal_path.exists():
        raise FileExistsError("Existing diagnostic ledger: inspect it; no automatic rerun/recovery")
    if objective is None:
        from .engineering_beam_adapter import make_problem
        objective = make_problem()
    cache, rows = {}, []
    counts = {"new_physical_calls": 0, "reused_source_labels": 0, "reused_diagnostic_labels": 0,
              "objective_seconds": 0., "complete": False, "promotion": "not assessed"}
    with journal_path.open("x", encoding="utf-8") as journal:
        def record(event):
            journal.write(json.dumps(event, allow_nan=False) + "\n")
            journal.flush()
        record({"event": "meta", "manifest_sha256": digest(out / "manifest.json"), "budget": cfg["max_new_diagnostic_calls"]})
        try:
            for item in manifest["states"]:
                frozen = json.loads((out / item["snapshot"]).read_text(encoding="utf-8"))
                pool = np.asarray(frozen["pool"])
                utilities = {}
                for index in sorted(set(frozen["decisions"].values())):
                    point = pool[index]
                    key = point.astype("<f8").tobytes().hex()
                    record({"event": "diagnostic_pre", "snapshot": item["snapshot"], "index": index,
                            "point": point.tolist(), "new_calls_before": counts["new_physical_calls"]})
                    if key in cache:
                        label = cache[key]
                        origin = "diagnostic_cache"
                        counts["reused_diagnostic_labels"] += 1
                    else:
                        label = recorded_label(root / item["source_events"], item["t"], point)
                        if label is not None:
                            origin = "already_paid_source_action"
                            counts["reused_source_labels"] += 1
                        else:
                            if counts["new_physical_calls"] >= cfg["max_new_diagnostic_calls"]:
                                raise RuntimeError("Diagnostic budget exhausted")
                            # Increment before calling: a failed/incomplete physical
                            # attempt cannot silently disappear from the ledger.
                            counts["new_physical_calls"] += 1
                            origin = "new_finite_element_call"
                            started = perf_counter()
                            try:
                                label = float(objective(point))
                            finally:
                                counts["objective_seconds"] += perf_counter() - started
                        if not np.isfinite(label):
                            raise FloatingPointError("Nonfinite diagnostic objective")
                        cache[key] = label
                    record({"event": "diagnostic_label", "snapshot": item["snapshot"], "index": index,
                            "y": label, "origin": origin})
                    utilities[index] = max(0., frozen["training_best"] - label) / frozen["scale"]
                greedy = frozen["decisions"]["mean"]
                rows.append({"method": item["method"], "rep": item["rep"], "t": item["t"],
                             "utility": {name: utilities[index] for name, index in frozen["decisions"].items()},
                             "changed_from_mean": {name: index != greedy for name, index in frozen["decisions"].items()}})
            counts["complete"] = True
        except Exception as error:
            counts["error"] = f"{type(error).__name__}: {error}"
            raise
        finally:
            write_json(out / "accounting.json", counts)
    write_json(out / "common_state_results.json", {"states": rows, "interpretation": "Immediate utility only; no net-savings or closed-loop promotion claim"})
    return counts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=CONFIG)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--preflight", action="store_true")
    action.add_argument("--freeze", action="store_true")
    action.add_argument("--evaluate", action="store_true")
    args = parser.parse_args()
    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    result = preflight(cfg) if args.preflight else freeze(cfg, args.config) if args.freeze else evaluate(cfg)
    print(json.dumps(result, indent=2))
    if args.preflight and not result["ready"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
