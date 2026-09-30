"""Audit and analyze the matched-initialization beam experiment."""
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from .engineering_beam_adapter import density_field
from .engineering_beam_shared_init import CONFIG, ROOT, audit_shared_sources, shared_archive

OLD_HASH = "655f4fc812284dd932ce3b79eaab4ee6e2132bc171d5607172462bf5c3f6aa44"
NEW_HASH = "78fd08dc394d0bb486b674fe9574ef39f7d1c365ddd0f88a32f91e33ad7aa2b2"


def events(path):
    return [json.loads(line) for line in Path(path).read_text("utf-8").splitlines() if line.strip()]


def result_path(base, method, rep, dim=19, budget=200):
    runid = f"{method}_f01_d{dim}_i1_r{rep}_b{budget}"
    return Path(base) / method / runid


def final_curve(path):
    labels = [row["y"] for row in events(path) if row.get("event") == "label"]
    return np.minimum.accumulate(np.asarray(labels, dtype=float))


def main():
    cfg = json.loads(CONFIG.read_text("utf-8"))
    out = ROOT / cfg["out"]
    source = ROOT / cfg["source"]
    source_audit = audit_shared_sources(cfg)
    rows, curves, issues = [], {}, []
    total_algorithm = total_reused = total_physical = 0
    hash_counts = {}
    for method in cfg["methods"]:
        curves[method] = []
        native = "gp_ei" if method.startswith("gp_ei") else "turbo_1"
        for rep in range(cfg["repeats"]):
            directory = result_path(out, method, rep, cfg["dimension"], cfg["budget"])
            summary = json.loads((directory / "summary.json").read_text("utf-8"))
            stream = events(directory / "events.jsonl")
            pre = [row for row in stream if row.get("event") == "pre"]
            labels = [row for row in stream if row.get("event") == "label"]
            points, values, digest, _ = shared_archive(rep, cfg)
            observed_x = np.asarray([row["x"] for row in pre], dtype=float)
            observed_y = np.asarray([row["y"] for row in labels], dtype=float)
            checks = {
                "meta_count": sum(row.get("event") == "meta" for row in stream) == 1,
                "pre_count": len(pre) == cfg["budget"],
                "label_count": len(labels) == cfg["budget"],
                "sequential_pre": [row["t"] for row in pre] == list(range(1, cfg["budget"] + 1)),
                "sequential_labels": [row["t"] for row in labels] == list(range(1, cfg["budget"] + 1)),
                "shared_points": np.array_equal(observed_x[:len(points)], points),
                "shared_labels": np.array_equal(observed_y[:len(values)], values),
                "shared_flags": all(row.get("reused_label") is True for row in labels[:len(values)]),
                "finite": bool(np.isfinite(observed_x).all() and np.isfinite(observed_y).all()),
                "bounds": bool(np.all((observed_x >= 0) & (observed_x <= 1))),
                "algorithm_budget": summary["algorithm_evaluations"] == cfg["budget"],
                "reused_count": summary["reused_initial_evaluations"] == len(values),
                "physical_count": summary["new_physical_evaluations"] == cfg["budget"] - len(values),
                "archive_digest": summary["signature"]["source_archive_sha256"] == digest,
                "duplicates": summary["exact_duplicate_calls"] == 0,
                "best": np.isclose(summary["best"], observed_y.min(), rtol=0, atol=0),
            }
            if not all(checks.values()):
                issues.append({"method": method, "rep": rep,
                               "failed_checks": [key for key, ok in checks.items() if not ok]})
            code = summary["signature"]["code_hash"]
            hash_counts[code] = hash_counts.get(code, 0) + 1
            if code not in {OLD_HASH, NEW_HASH}:
                issues.append({"method": method, "rep": rep, "failed_checks": ["unknown_code_hash"]})
            native_summary = json.loads((result_path(source, native, rep) / "summary.json").read_text("utf-8"))
            pem_summary = json.loads((result_path(source, "PEM_T", rep) / "summary.json").read_text("utf-8"))
            rows.append({"method": method, "rep": rep, "best": summary["best"],
                         "initial_best": summary["initial_best"],
                         "native_best": native_summary["best"],
                         "shared_minus_native": summary["best"] - native_summary["best"],
                         "pem_t_best": pem_summary["best"],
                         "shared_minus_pem_t": summary["best"] - pem_summary["best"],
                         "elapsed": summary["elapsed"], "warnings": sum(summary["warning_counts"].values()),
                         "code_hash": code})
            curves[method].append(np.minimum.accumulate(observed_y))
            total_algorithm += summary["algorithm_evaluations"]
            total_reused += summary["reused_initial_evaluations"]
            total_physical += summary["new_physical_evaluations"]

    frame = pd.DataFrame(rows)
    frame.to_csv(out / "paired_results.csv", index=False)
    summaries = []
    tests = []
    for method, group in frame.groupby("method", sort=False):
        values = group["best"].to_numpy()
        summaries.append({"method": method, "median": np.median(values),
                          "q25": np.quantile(values, .25), "q75": np.quantile(values, .75),
                          "mean": np.mean(values), "std": np.std(values, ddof=1),
                          "wins_vs_pem_t": int(np.sum(group["shared_minus_pem_t"] < 0)),
                          "ties_vs_pem_t": int(np.sum(group["shared_minus_pem_t"] == 0)),
                          "losses_vs_pem_t": int(np.sum(group["shared_minus_pem_t"] > 0))})
        for comparison, column in [("native_initialization", "shared_minus_native"),
                                   ("PEM_T", "shared_minus_pem_t")]:
            diff = group[column].to_numpy()
            statistic, pvalue = wilcoxon(diff, zero_method="wilcox", alternative="two-sided")
            tests.append({"method": method, "comparison": comparison,
                          "median_difference": np.median(diff),
                          "wins": int(np.sum(diff < 0)), "ties": int(np.sum(diff == 0)),
                          "losses": int(np.sum(diff > 0)),
                          "wilcoxon_statistic": statistic, "p_value": pvalue})
    pd.DataFrame(summaries).to_csv(out / "method_summary.csv", index=False)
    test_frame = pd.DataFrame(tests)
    test_frame["holm_p_value"] = np.nan
    for comparison, indices in test_frame.groupby("comparison").groups.items():
        ordered = sorted(indices, key=lambda idx: test_frame.loc[idx, "p_value"])
        running = 0.0
        m = len(ordered)
        for rank, idx in enumerate(ordered):
            adjusted = min(1.0, (m - rank) * test_frame.loc[idx, "p_value"])
            running = max(running, adjusted)
            test_frame.loc[idx, "holm_p_value"] = running
    test_frame.to_csv(out / "paired_tests.csv", index=False)

    plot_methods = ["PEM_T", "fixed01", "greedy"] + cfg["methods"]
    plot_curves = {}
    for method in plot_methods:
        if method in curves:
            plot_curves[method] = np.asarray(curves[method])
        else:
            plot_curves[method] = np.asarray([
                final_curve(result_path(source, method, rep) / "events.jsonl")
                for rep in range(cfg["repeats"])])
    labels = {"PEM_T": "PEM-T", "fixed01": "Fixed-0.1", "greedy": "Greedy",
              "gp_ei_shared_init": "GP-EI (shared init.)",
              "turbo_1_shared_init": "TuRBO-1 (shared init.)"}
    colors = {"PEM_T": "#c0392b", "fixed01": "#2980b9", "greedy": "#7f8c8d",
              "gp_ei_shared_init": "#8e44ad", "turbo_1_shared_init": "#16a085"}
    fig, ax = plt.subplots(figsize=(7.2, 4.5))
    x = np.arange(1, cfg["budget"] + 1)
    for method in plot_methods:
        data = plot_curves[method]
        median = np.median(data, axis=0)
        q25, q75 = np.quantile(data, [.25, .75], axis=0)
        ax.plot(x, median, label=labels[method], color=colors[method], linewidth=1.8)
        ax.fill_between(x, q25, q75, color=colors[method], alpha=.12, linewidth=0)
    ax.axvline(cfg["shared_initial_evaluations"], color="black", linestyle="--", linewidth=.9)
    ax.set_yscale("log")
    ax.set_xlabel("Finite-element evaluations")
    ax.set_ylabel("Best compliance so far")
    ax.grid(True, which="both", alpha=.2)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "matched_initialization_convergence.png", dpi=350)
    fig.savefig(out / "matched_initialization_convergence.pdf")
    plt.close(fig)

    fig, axes = plt.subplots(1, len(plot_methods), figsize=(12, 2.5), constrained_layout=True)
    for ax, method in zip(axes, plot_methods):
        base = out if method in cfg["methods"] else source
        endpoints = []
        for rep in range(cfg["repeats"]):
            stream = events(result_path(base, method, rep) / "events.jsonl")
            pre = {row["t"]: row for row in stream if row.get("event") == "pre"}
            observed = {row["t"]: row["y"] for row in stream if row.get("event") == "label"}
            best_t = min(observed, key=observed.get)
            endpoints.append((observed[best_t], rep, pre[best_t]["x"]))
        endpoints.sort(key=lambda item: item[0])
        _, rep, point = endpoints[len(endpoints) // 2]
        image = ax.imshow(density_field(point), cmap="gray_r", vmin=0, vmax=1, aspect="auto")
        ax.set_title(f"{labels[method]}\nrep {rep}", fontsize=8)
        ax.axis("off")
    fig.colorbar(image, ax=axes, fraction=.02, pad=.02, label="Density")
    fig.savefig(out / "matched_initialization_representative_designs.png", dpi=350)
    fig.savefig(out / "matched_initialization_representative_designs.pdf")
    plt.close(fig)

    audit = {"status": "pass" if not issues else "fail", "runs": len(frame),
             "algorithm_evaluations": total_algorithm,
             "reused_initial_evaluations": total_reused,
             "new_physical_evaluations": total_physical,
             "exact_duplicate_calls": 0 if not issues else None,
             "source_archives": source_audit, "code_hash_counts": hash_counts,
             "issues": issues}
    (out / "audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps(audit, indent=2))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
