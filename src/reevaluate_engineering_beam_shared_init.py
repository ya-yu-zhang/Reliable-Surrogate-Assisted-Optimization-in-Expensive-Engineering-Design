"""Independent post-completion endpoint checks for shared-init beam runs."""
import json
from pathlib import Path
import pandas as pd
import numpy as np

from .engineering_beam_adapter import make_problem
from .engineering_beam_shared_init import CONFIG, ROOT


def main():
    cfg = json.loads(CONFIG.read_text("utf-8"))
    out = ROOT / cfg["out"]
    target = out / "endpoint_reevaluations.csv"
    if target.exists():
        raise RuntimeError(f"endpoint audit already exists: {target}")
    rows = []
    for method in cfg["methods"]:
        for rep in range(cfg["repeats"]):
            runid = f"{method}_f01_d{cfg['dimension']}_i1_r{rep}_b{cfg['budget']}"
            directory = out / method / runid
            stream = [json.loads(line) for line in (directory / "events.jsonl").read_text("utf-8").splitlines()]
            pre = {row["t"]: row for row in stream if row.get("event") == "pre"}
            labels = {row["t"]: row for row in stream if row.get("event") == "label"}
            best_t = min(labels, key=lambda t: labels[t]["y"])
            stored = float(labels[best_t]["y"])
            objective = make_problem()
            repeated = float(objective(pre[best_t]["x"]))
            rows.append({"diagnostic_round": 2, "method": method, "rep": rep, "best_t": best_t,
                         "stored": stored, "reevaluated": repeated,
                         "absolute_difference": abs(repeated - stored),
                         "relative_difference": abs(repeated - stored) / stored})
    frame = pd.DataFrame(rows)
    # Sparse finite-element solves may differ in their last few floating-point
    # digits across fresh solver instances; this threshold is far below any
    # reported precision and is applied only to the independent diagnostic.
    if not np.allclose(frame["stored"], frame["reevaluated"], rtol=1e-10, atol=1e-8):
        raise AssertionError("endpoint reevaluation mismatch")
    frame.to_csv(target, index=False)
    print(frame[["absolute_difference", "relative_difference"]].max().to_json())


if __name__ == "__main__":
    main()
