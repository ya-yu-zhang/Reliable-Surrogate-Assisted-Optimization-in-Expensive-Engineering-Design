"""Audit and summarize the frozen EngiBench Beams2D experiment."""
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

from .engineering_beam_adapter import EngineeringBeamObjective, density_field

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/engineering_beam_formal_v1"
CFG = json.loads((ROOT / "configs/engineering_beam_formal.json").read_text("utf-8"))


def quantile(values, q):
    return float(np.quantile(np.asarray(values, dtype=float), q))


def main():
    frozen = json.loads((OUT / "source_hashes_at_launch.json").read_text("utf-8-sig"))
    source_ok = all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
                    for name, digest in frozen.items())
    if not source_ok:
        raise RuntimeError("source changed after formal launch")

    rows, curves, best_fields, file_hashes, reevaluations = [], {}, {}, {}, []
    expected = {(m, r) for m in CFG["methods"] for r in range(CFG["repeats"])}
    found = set()
    max_volume_error = 0.0
    for summary_path in sorted(OUT.glob("*/*/summary.json")):
        summary = json.loads(summary_path.read_text("utf-8"))
        sig = summary["signature"]
        method, rep = sig["method"], int(sig["rep"])
        found.add((method, rep))
        if sig["dim"] != CFG["dimension"] or sig["budget"] != CFG["budget"]:
            raise AssertionError("signature differs from frozen design")
        event_path = summary_path.with_name("events.jsonl")
        items = [json.loads(line) for line in event_path.read_text("utf-8").splitlines()]
        if items[0]["event"] != "meta":
            raise AssertionError("missing meta")
        pre = [x for x in items if x["event"] == "pre"]
        labels = [x for x in items if x["event"] == "label"]
        if len(pre) != CFG["budget"] or len(labels) != CFG["budget"]:
            raise AssertionError("PRE/LABEL count mismatch")
        values, points = [], []
        for t, (a, b) in enumerate(zip(pre, labels), 1):
            if a["t"] != t or b["t"] != t:
                raise AssertionError("event order mismatch")
            point = np.asarray(a["x"], dtype=float)
            if point.shape != (CFG["dimension"],) or np.any(point < 0) or np.any(point > 1):
                raise AssertionError("invalid design parameter")
            volume_error = abs(float(density_field(point).mean()) - 0.35)
            max_volume_error = max(max_volume_error, volume_error)
            value = float(b["y"])
            if not np.isfinite(value) or value <= 0:
                raise AssertionError("invalid compliance")
            points.append(point); values.append(value)
            if abs(float(b["best_after"]) - min(values)) > 1e-9 * max(1.0, min(values)):
                raise AssertionError("best-so-far mismatch")
        values = np.asarray(values); points = np.asarray(points)
        best_index = int(np.argmin(values)); best = float(values[best_index])
        if abs(best - float(summary["best"])) > 1e-9 * max(1.0, best):
            raise AssertionError("summary endpoint mismatch")
        initial_count = 2 * CFG["dimension"] + (20 if method in {"greedy", "fixed01", "PEM_T"} else 0)
        initial_best = float(np.min(values[:initial_count]))
        improvement = (initial_best - best) / initial_best
        rows.append({"method": method, "rep": rep, "best_compliance": best,
                     "initial_best": initial_best, "relative_improvement": improvement,
                     "elapsed_seconds": float(summary["elapsed"]),
                     "algorithm_evaluations": int(summary["algorithm_evaluations"])})
        curves[(method, rep)] = np.minimum.accumulate(values)
        best_fields[(method, rep)] = density_field(points[best_index])
        oracle = EngineeringBeamObjective()
        repeated = float(oracle(points[best_index]))
        difference = repeated - best
        if abs(difference) > 1e-8 * max(1.0, abs(best)):
            raise AssertionError("independent endpoint reevaluation mismatch")
        reevaluations.append({"method": method, "rep": rep, "original": best,
                              "reevaluated": repeated, "difference": difference})
        for path in (summary_path, event_path):
            file_hashes[str(path.relative_to(ROOT)).replace("\\", "/")] = hashlib.sha256(path.read_bytes()).hexdigest()
    if found != expected:
        raise AssertionError(f"design incomplete: missing={sorted(expected-found)} extra={sorted(found-expected)}")

    with (OUT / "runs.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    with (OUT / "endpoint_reevaluations.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(reevaluations[0])); writer.writeheader(); writer.writerows(reevaluations)

    summary_rows = []
    for method in CFG["methods"]:
        group = [r for r in rows if r["method"] == method]
        endpoint = [r["best_compliance"] for r in group]
        gain = [r["relative_improvement"] for r in group]
        elapsed = [r["elapsed_seconds"] for r in group]
        summary_rows.append({"method": method, "runs": len(group),
                             "median_compliance": quantile(endpoint, .5),
                             "q1_compliance": quantile(endpoint, .25),
                             "q3_compliance": quantile(endpoint, .75),
                             "median_relative_improvement": quantile(gain, .5),
                             "median_elapsed_seconds": quantile(elapsed, .5)})
    with (OUT / "method_summary.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0])); writer.writeheader(); writer.writerows(summary_rows)

    by = {(r["method"], r["rep"]): r for r in rows}
    paired = []
    for control in ("greedy", "fixed01"):
        differences = [by[("PEM_T", rep)]["best_compliance"] - by[(control, rep)]["best_compliance"]
                       for rep in range(CFG["repeats"])]
        paired.append({"contrast": f"PEM_T-minus-{control}",
                       "median_difference": quantile(differences, .5),
                       "q1_difference": quantile(differences, .25),
                       "q3_difference": quantile(differences, .75),
                       "pem_t_better": sum(v < 0 for v in differences),
                       "pem_t_worse": sum(v > 0 for v in differences),
                       "ties": sum(v == 0 for v in differences)})
    with (OUT / "paired_internal.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(paired[0])); writer.writeheader(); writer.writerows(paired)

    fig, ax = plt.subplots(figsize=(7.4, 4.3))
    for method in CFG["methods"]:
        matrix = np.asarray([curves[(method, rep)] for rep in range(CFG["repeats"])])
        ax.plot(np.arange(1, CFG["budget"] + 1), np.median(matrix, axis=0), label=method)
    ax.set(xlabel="Finite-element evaluations", ylabel="Best compliance (median)")
    ax.grid(alpha=.25); ax.legend(ncol=3, fontsize=8); fig.tight_layout()
    fig.savefig(OUT / "convergence.png", dpi=220); fig.savefig(OUT / "convergence.pdf"); plt.close(fig)

    fig, axes = plt.subplots(1, len(CFG["methods"]), figsize=(12, 2.5), constrained_layout=True)
    for ax, method in zip(axes, CFG["methods"]):
        ordered = sorted(range(CFG["repeats"]), key=lambda r: by[(method, r)]["best_compliance"])
        rep = ordered[len(ordered) // 2]
        image = ax.imshow(best_fields[(method, rep)], cmap="gray_r", vmin=0, vmax=1, aspect="auto")
        ax.set_title(f"{method}\nrep {rep}", fontsize=8); ax.axis("off")
    fig.colorbar(image, ax=axes, fraction=.02, pad=.02, label="Density")
    fig.savefig(OUT / "representative_designs.png", dpi=220); fig.savefig(OUT / "representative_designs.pdf"); plt.close(fig)

    audit = {"runs": len(rows), "canonical_finite_element_evaluations": len(rows) * CFG["budget"],
             "independent_endpoint_reevaluations": len(reevaluations),
             "pre_label_pairs": len(rows) * CFG["budget"], "failures": 0,
             "complete_design": found == expected, "source_hashes_verified": source_ok,
             "raw_file_hashes": len(file_hashes), "max_volume_fraction_error": max_volume_error,
             "endpoint_reevaluations_match": True, "statistical_tests_added": 0,
             "smoke_results_used_for_selection": False, "file_hashes": file_hashes}
    (OUT / "audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps({"audit": {k: v for k, v in audit.items() if k != "file_hashes"},
                      "method_summary": summary_rows, "paired": paired}, indent=2))


if __name__ == "__main__":
    main()
