"""Validate the diagnostic ledger and report prespecified repeat aggregates."""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path
import numpy as np
from .engineering_optimization_gp_audit import digest, recorded_label, source_units, write_json

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "paper/engineering_optimization/gp_audit"


def analyze(released=False):
    cfg = json.loads((ROOT / "configs/engineering_optimization_gp_audit.json").read_text())
    out = REPORT if released else ROOT / cfg["out"]
    manifest_path = REPORT / "frozen_manifest.json" if released else out / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    assert digest(manifest_path) == digest(REPORT / "frozen_manifest.json")
    assert digest(ROOT / "configs/engineering_optimization_gp_audit.json") == manifest["config_sha256"]
    assert digest(ROOT / "src/engineering_optimization_gp_audit.py") == manifest["code_sha256"]
    accounting = json.loads((out / "accounting.json").read_text())
    assert accounting["complete"] and accounting["new_physical_calls"] <= cfg["max_new_diagnostic_calls"]
    states = json.loads((out / "common_state_results.json").read_text())["states"]
    assert len(states) == 120
    by_name = {i["snapshot"]: i for i in manifest["states"]}
    snapshots = {}
    compact = {s["snapshot"]: s for s in json.loads((REPORT / "frozen_decisions.json").read_text())["states"]}
    assert set(compact) == set(by_name)
    for name, item in by_name.items():
        assert digest(ROOT / item["source_events"]) == item["source_sha256"]
        assert digest((ROOT / item["source_events"]).parent / "summary.json") == item["summary_sha256"]
        if released:
            decision = compact[name]
            assert all(decision[k] == v for k, v in item.items())
            decisions = {c: d["index"] for c, d in decision["decisions"].items()}
            pool = {d["index"]: d["point"] for d in decision["decisions"].values()}
            from .engineering_optimization_gp_audit import frozen_state
            _, _, train_y, _ = frozen_state(ROOT / item["source_events"], item["t"])
            assert decision["training_best"] == float(train_y.min())
            assert decision["scale"] == (float(train_y.std()) or 1.)
            snapshots[name] = {"decisions": decisions, "pool": pool,
                               "training_best": decision["training_best"], "scale": decision["scale"]}
        else:
            assert digest(out / name) == item["snapshot_sha256"]
            snapshots[name] = json.loads((out / name).read_text())
    journal = [json.loads(line) for line in (out / "diagnostic_events.jsonl").read_text().splitlines()]
    assert journal[0]["manifest_sha256"] == digest(manifest_path)
    assert (len(journal) - 1) % 2 == 0
    labels, origins, response_cache = {}, Counter(), {}
    physical = 0
    for pre, label in zip(journal[1::2], journal[2::2]):
        assert pre["event"] == "diagnostic_pre" and label["event"] == "diagnostic_label"
        assert (pre["snapshot"], pre["index"]) == (label["snapshot"], label["index"])
        key = pre["snapshot"], pre["index"]
        assert key not in labels and pre["new_calls_before"] == physical
        snap = snapshots[pre["snapshot"]]
        assert pre["index"] in snap["decisions"].values()
        assert pre["point"] == snap["pool"][pre["index"]]
        assert np.isfinite(label["y"]) and label["y"] > 0
        point_key = np.asarray(pre["point"], dtype="<f8").tobytes()
        if label["origin"] == "diagnostic_cache":
            assert point_key in response_cache and response_cache[point_key] == label["y"]
        else:
            assert point_key not in response_cache
        if label["origin"] == "new_finite_element_call":
            physical += 1
        elif label["origin"] == "already_paid_source_action":
            item = by_name[pre["snapshot"]]
            assert recorded_label(ROOT / item["source_events"], item["t"], pre["point"]) == label["y"]
        else:
            assert label["origin"] == "diagnostic_cache"
        origins[label["origin"]] += 1
        response_cache[point_key] = label["y"]
        labels[key] = label["y"]
    assert physical == accounting["new_physical_calls"]
    assert origins["already_paid_source_action"] == accounting["reused_source_labels"]
    assert origins["diagnostic_cache"] == accounting["reused_diagnostic_labels"]
    for row in states:
        name = f"{row['method']}_r{row['rep']}_t{row['t']}.json"
        snap = snapshots[name]
        for control, index in snap["decisions"].items():
            u = max(0., snap["training_best"] - labels[name, index]) / snap["scale"]
            assert u == row["utility"][control]
            assert row["changed_from_mean"][control] == (index != snap["decisions"]["mean"])
    initialization = {}
    for method, rep, events, summary in source_units(cfg):
        data = [json.loads(line) for line in events.read_text().splitlines()]
        pres = [r for r in data if r.get("event") == "pre"]
        labs = [r for r in data if r.get("event") == "label"]
        s = json.loads(summary.read_text())
        assert [r["t"] for r in pres] == list(range(1, 201)) == [r["t"] for r in labs]
        assert min(r["y"] for r in labs) == s["best"] and s["algorithm_evaluations"] == 200
        pairs = [(p["x_unit"], l["y"]) for p, l in zip(pres[:58], labs[:58])]
        if rep in initialization:
            assert pairs == initialization[rep]
        initialization[rep] = pairs
    repeats, groups = [], []
    for method in cfg["source_roots"]:
        for rep in range(10):
            selected = [r for r in states if r["method"] == method and r["rep"] == rep]
            assert sorted(r["t"] for r in selected) == cfg["checkpoints"]
            for c in cfg["controls"]:
                repeats.append({"source_history": method, "rep": rep, "control": c,
                                "action_change_fraction": float(np.mean([r["changed_from_mean"][c] for r in selected])),
                                "mean_utility": float(np.mean([r["utility"][c] for r in selected])),
                                "mean_delta_vs_mean": float(np.mean([r["utility"][c] - r["utility"]["mean"] for r in selected]))})
        for c in cfg["controls"]:
            selected = [r for r in repeats if r["source_history"] == method and r["control"] == c]
            groups.append({"source_history": method, "control": c, "repeats": 10, "states": 40,
                           **{key: float(np.mean([r[key] for r in selected])) for key in
                              ["action_change_fraction", "mean_utility", "mean_delta_vs_mean"]}})
    solver = json.loads((REPORT / "solver_replay.json").read_text())
    assert solver["complete"] and solver["retained_replay_calls"] == 60
    summary = {"design": {"source_histories": 3, "repeats_per_history": 10, "checkpoints_per_repeat": 4,
                           "states": 120, "controls": cfg["controls"]},
               "source_validation": {"files": 60, "algorithm_observations": 6000,
                                     "common_initial_labels": 580, "historical_postinitial_calls": 4260},
               "ledger": {"unique_state_choices": len(labels), "origins": dict(origins), **accounting},
               "costs": {"diagnostic_new_calls": physical, "solver_validation_attempts": solver["total_validation_attempts"],
                         "total_new_finite_element_attempts_this_revision": physical + solver["total_validation_attempts"],
                         "gp_state_preparation_seconds": manifest["preparation_seconds"],
                         "diagnostic_objective_seconds": accounting["objective_seconds"],
                         "solver_validation_seconds_first_pass": "not retained",
                         "solver_validation_seconds_retained_pass": solver["objective_seconds_retained_replay"],
                         "timing_interpretation": "Observed implementation times; no exclusive process guard or workflow saving comparison"},
               "solver_max_relative_difference": max(r["relative_difference"] for r in solver["rows"]),
               "groups": groups, "interpretation": "Descriptive immediate utility; repeat-first aggregation; no new inferential tests, delayed-value claim, promotion, or net-savings claim"}
    REPORT.mkdir(parents=True, exist_ok=True)
    write_json(REPORT / "summary.json", summary)
    for name, rows in [("repeat_aggregates.csv", repeats), ("group_aggregates.csv", groups)]:
        with (REPORT / name).open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    return {**summary, "validation_scope": (
        "Released chosen-point vectors, raw-source hashes, PRE/LABEL order and exact utilities; "
        "does not independently replay the full GP posterior or full candidate pool"
        if released else "Full frozen snapshot and source hashes, PRE/LABEL order and exact utilities")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--released", action="store_true", help="Validate compact public evidence without full 263-MB snapshots")
    print(json.dumps(analyze(parser.parse_args().released), indent=2))
