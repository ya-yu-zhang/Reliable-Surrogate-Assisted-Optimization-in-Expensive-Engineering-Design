"""Audit GP-PI/GP-UCB matched-history beam runs and create manuscript assets."""
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from .engineering_beam_adapter import density_field
from .engineering_beam_shared_init import ROOT, audit_shared_sources, shared_archive

CONFIG = ROOT / "configs/engineering_beam_acquisition_refs.json"
OLD = ROOT / "results/engineering_beam_shared_init_v1"
SOURCE = ROOT / "results/engineering_beam_formal_v1"


def read_events(path):
    return [json.loads(line) for line in Path(path).read_text("utf-8").splitlines() if line.strip()]


def directory(base, method, rep, dim=19, budget=200):
    runid = f"{method}_f01_d{dim}_i1_r{rep}_b{budget}"
    return Path(base) / method / runid


def curve(base, method, rep):
    labels = [row["y"] for row in read_events(directory(base, method, rep) / "events.jsonl")
              if row.get("event") == "label"]
    return np.minimum.accumulate(np.asarray(labels))


def holm(values):
    order = np.argsort(values)
    adjusted = np.empty(len(values))
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (len(values) - rank) * values[index]))
        adjusted[index] = running
    return adjusted


def main():
    cfg = json.loads(CONFIG.read_text("utf-8"))
    out = ROOT / cfg["out"]
    issues, rows = [], []
    expected_hash = hashlib.sha256()
    for path in [ROOT / "src/engineering_beam_shared_init.py", ROOT / "src/core.py",
                 ROOT / "src/engineering_beam_adapter.py", ROOT / "src/gp_references.py"]:
        expected_hash.update(str(path.relative_to(ROOT)).replace("\\", "/").encode())
        expected_hash.update(path.read_bytes())
    for name in ["turbo_1.py", "gp.py", "utils.py", "__init__.py"]:
        path = ROOT / "literature/source-code/TuRBO/turbo" / name
        expected_hash.update(name.encode()); expected_hash.update(path.read_bytes())
    expected_hash = expected_hash.hexdigest()
    for method in cfg["methods"]:
        for rep in range(cfg["repeats"]):
            run = directory(out, method, rep)
            summary = json.loads((run / "summary.json").read_text("utf-8"))
            stream = read_events(run / "events.jsonl")
            meta = [row for row in stream if row.get("event") == "meta"]
            pre = [row for row in stream if row.get("event") == "pre"]
            labels = [row for row in stream if row.get("event") == "label"]
            points, initial, digest, _ = shared_archive(rep, cfg)
            observed_x = np.asarray([row["x"] for row in pre])
            observed_y = np.asarray([row["y"] for row in labels])
            checks = {
                "one_meta": len(meta) == 1,
                "event_counts": len(pre) == len(labels) == cfg["budget"],
                "ordered_pre": [row["t"] for row in pre] == list(range(1, cfg["budget"] + 1)),
                "ordered_labels": [row["t"] for row in labels] == list(range(1, cfg["budget"] + 1)),
                "shared_points": np.array_equal(observed_x[:len(points)], points),
                "shared_labels": np.array_equal(observed_y[:len(initial)], initial),
                "shared_digest": summary["signature"]["source_archive_sha256"] == digest,
                "code_hash": summary["signature"]["code_hash"] == expected_hash,
                "finite": np.isfinite(observed_x).all() and np.isfinite(observed_y).all(),
                "bounds": np.all((observed_x >= 0) & (observed_x <= 1)),
                "budget": summary["algorithm_evaluations"] == cfg["budget"],
                "reused": summary["reused_initial_evaluations"] == len(initial),
                "physical": summary["new_physical_evaluations"] == cfg["budget"] - len(initial),
                "duplicates": summary["exact_duplicate_calls"] == 0,
                "best": summary["best"] == float(observed_y.min()),
            }
            if not all(checks.values()):
                issues.append({"method": method, "rep": rep,
                               "failed": [key for key, value in checks.items() if not value]})
            pem = json.loads((directory(SOURCE, "PEM_T", rep) / "summary.json").read_text("utf-8"))
            rows.append({"method": method, "rep": rep, "best": summary["best"],
                         "initial_best": summary["initial_best"],
                         "improvement_fraction": 1 - summary["best"] / summary["initial_best"],
                         "pem_t_best": pem["best"], "difference_vs_pem_t": summary["best"] - pem["best"],
                         "elapsed_seconds": summary["elapsed"],
                         "warnings": sum(summary["warning_counts"].values())})
    frame = pd.DataFrame(rows)
    frame.to_csv(out / "paired_results.csv", index=False)
    summaries, tests = [], []
    for method, group in frame.groupby("method", sort=False):
        best = group["best"].to_numpy(); diff = group["difference_vs_pem_t"].to_numpy()
        summaries.append({"method": method, "median": np.median(best),
                          "q25": np.quantile(best, .25), "q75": np.quantile(best, .75),
                          "median_improvement_fraction": np.median(group["improvement_fraction"]),
                          "wins_vs_pem_t": int(np.sum(diff < 0)), "ties_vs_pem_t": int(np.sum(diff == 0)),
                          "losses_vs_pem_t": int(np.sum(diff > 0))})
        stat, p = wilcoxon(diff, zero_method="wilcox", alternative="two-sided")
        tests.append({"method": method, "comparison": "PEM_T", "median_difference": np.median(diff),
                      "wins": int(np.sum(diff < 0)), "ties": int(np.sum(diff == 0)),
                      "losses": int(np.sum(diff > 0)), "wilcoxon_statistic": stat, "p_value": p})
    summary_frame = pd.DataFrame(summaries); summary_frame.to_csv(out / "method_summary.csv", index=False)
    test_frame = pd.DataFrame(tests); test_frame["holm_p_value"] = holm(test_frame["p_value"].to_numpy())
    test_frame.to_csv(out / "paired_tests.csv", index=False)

    methods = ["PEM_T", "fixed01", "greedy", "gp_ei_shared_init", "gp_pi_shared_init",
               "gp_ucb_shared_init", "turbo_1_shared_init"]
    labels = {"PEM_T": "PEM-T", "fixed01": "Fixed-0.1", "greedy": "Greedy",
              "gp_ei_shared_init": "GP-EI", "gp_pi_shared_init": "GP-PI",
              "gp_ucb_shared_init": "GP-UCB", "turbo_1_shared_init": "TuRBO-1"}
    colors = {"PEM_T": "#c0392b", "fixed01": "#2980b9", "greedy": "#7f8c8d",
              "gp_ei_shared_init": "#8e44ad", "gp_pi_shared_init": "#d68910",
              "gp_ucb_shared_init": "#2471a3", "turbo_1_shared_init": "#16a085"}
    bases = {m: (out if m in cfg["methods"] else OLD if "shared_init" in m else SOURCE) for m in methods}
    fig, ax = plt.subplots(figsize=(7.4, 4.6)); x = np.arange(1, cfg["budget"] + 1)
    for method in methods:
        data = np.asarray([curve(bases[method], method, rep) for rep in range(cfg["repeats"])])
        median = np.median(data, axis=0); q25, q75 = np.quantile(data, [.25, .75], axis=0)
        ax.plot(x, median, label=labels[method], color=colors[method], linewidth=1.7)
        ax.fill_between(x, q25, q75, color=colors[method], alpha=.1, linewidth=0)
    ax.axvline(cfg["shared_initial_evaluations"], color="black", linestyle="--", linewidth=.9)
    ax.set_yscale("log"); ax.set_xlabel("Finite-element evaluations"); ax.set_ylabel("Best compliance so far")
    ax.grid(True, which="both", alpha=.2); ax.legend(frameon=False, fontsize=7.5, ncol=2)
    fig.tight_layout(); fig.savefig(out / "acquisition_comparison_convergence.png", dpi=600)
    fig.savefig(out / "acquisition_comparison_convergence.pdf"); plt.close(fig)

    audit = {"status": "pass" if not issues else "fail", "runs": len(frame),
             "algorithm_evaluations": int(len(frame) * cfg["budget"]),
             "reused_initial_evaluations": int(len(frame) * cfg["shared_initial_evaluations"]),
             "new_physical_evaluations": int(len(frame) * (cfg["budget"] - cfg["shared_initial_evaluations"])),
             "source_archives": audit_shared_sources(cfg), "expected_code_hash": expected_hash,
             "issues": issues}
    (out / "audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(summary_frame.to_string(index=False)); print(test_frame.to_string(index=False)); print(json.dumps(audit, indent=2))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
