"""Audit second-interruption recoveries, allowing only bounded CMA floating roundoff."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "results/application_interruption_20260922_v2/partial_runs"
OUT = ROOT / "results/application_formal_v1"
RUNS = ["cma_es_DNA_r08_b500", "turbo_1_DNA_r04_b500", "turbo_1_synt_simple_r07_b500"]


def equivalent(left, right, tolerant):
    a = dict(left); b = dict(right); a.pop("preparation_seconds", None); b.pop("preparation_seconds", None)
    assert set(a) == set(b)
    for key in a:
        if tolerant and key in {"x", "x_unit"}:
            if not np.allclose(np.asarray(a[key]), np.asarray(b[key]), rtol=0, atol=2e-12): return False
        elif a[key] != b[key]: return False
    return True


def main():
    first = json.loads((ROOT / "results/application_recovery_audit_v1/audit.json").read_text("utf-8"))
    assert first["complete"] and first["objective_calls_by_auditor"] == 0
    rows = []
    for runid in RUNS:
        tolerant = runid.startswith("cma_es_")
        old = [json.loads(line) for line in (ARCHIVE / runid / "events.jsonl").read_text("utf-8").splitlines()]
        new = [json.loads(line) for line in (OUT / runid / "events.jsonl").read_text("utf-8").splitlines()]
        recovery = json.loads((OUT / runid / "recovery.json").read_text("utf-8"))
        summary = json.loads((OUT / runid / "summary.json").read_text("utf-8")); paid = recovery["old_paid_calls"]
        assert len(new) == 1001 and summary["algorithm_evaluations"] == 500 and new[0] == old[0]
        assert all(equivalent(left, right, tolerant) for left, right in zip(new[1:1 + 2 * paid], old[1:1 + 2 * paid]))
        dangling = len(old) == 2 + 2 * paid
        if dangling: assert equivalent(new[1 + 2 * paid], old[-1], tolerant)
        physical = (OUT / runid / "recovery_physical_calls.jsonl").read_text("utf-8").splitlines()
        assert len(physical) == 2 * recovery["new_paid_calls"] and summary["test_method_calls"] == 1
        rows.append({"runid": runid, "old_paid_calls": paid, "new_paid_calls": recovery["new_paid_calls"],
                     "prefix_equivalent": True, "candidate_absolute_tolerance": 2e-12 if tolerant else 0,
                     "dangling_unpaid_pre_reproduced": dangling,
                     "journal_sha256": hashlib.sha256((OUT / runid / "events.jsonl").read_bytes()).hexdigest()})
    result = {"schema": "application_recovery_audit_v3", "complete": True, "objective_calls_by_auditor": 0,
              "recovered_runs": 3, "saved_paid_labels": sum(r["old_paid_calls"] for r in rows),
              "new_physical_calls": sum(r["new_paid_calls"] for r in rows), "canonical_evaluations": 1500,
              "post_completion_test_calls": 3, "prior_recovery_audit_preserved": True, "rows": rows}
    assert result["saved_paid_labels"] == 924 and result["new_physical_calls"] == 576
    target = ROOT / "results/application_recovery_audit_v3"; target.mkdir(exist_ok=False)
    (target / "audit.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, indent=2))


if __name__ == "__main__": main()
