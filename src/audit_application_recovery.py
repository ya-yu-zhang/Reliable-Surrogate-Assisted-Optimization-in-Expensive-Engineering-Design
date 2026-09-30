"""Read-only pointwise audit of the interrupted application recovery."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "results/application_interruption_20260921_v1/partial_runs"
OUT = ROOT / "results/application_formal_v1"
RUNS = [
    "gp_ei_DNA_r11_b500", "PEM_T_DNA_r01_b500",
    "turbo_1_synt_simple_r14_b500", "turbo_1_DNA_r05_b500",
]


def comparable(event: dict) -> dict:
    result = dict(event); result.pop("preparation_seconds", None); return result


def main() -> None:
    rows = []
    for runid in RUNS:
        old = [json.loads(line) for line in (ARCHIVE / runid / "events.jsonl").read_text("utf-8").splitlines()]
        new = [json.loads(line) for line in (OUT / runid / "events.jsonl").read_text("utf-8").splitlines()]
        recovery = json.loads((OUT / runid / "recovery.json").read_text("utf-8"))
        summary = json.loads((OUT / runid / "summary.json").read_text("utf-8"))
        paid = recovery["old_paid_calls"]
        assert len(new) == 1001 and summary["algorithm_evaluations"] == 500
        assert new[0] == old[0]
        for left, right in zip(new[1:1 + 2 * paid], old[1:1 + 2 * paid]):
            assert comparable(left) == comparable(right)
        if len(old) == 2 + 2 * paid:
            assert comparable(new[1 + 2 * paid]) == comparable(old[-1])
        physical = [json.loads(line) for line in (OUT / runid / "recovery_physical_calls.jsonl").read_text("utf-8").splitlines()]
        assert len(physical) == 2 * recovery["new_paid_calls"]
        assert summary["test_method_calls"] == 1
        rows.append({
            "runid": runid, "old_paid_calls": paid,
            "new_paid_calls": recovery["new_paid_calls"],
            "prefix_equal": True,
            "journal_sha256": hashlib.sha256((OUT / runid / "events.jsonl").read_bytes()).hexdigest(),
        })
    result = {
        "schema": "application_recovery_audit_v1",
        "complete": True,
        "objective_calls_by_auditor": 0,
        "recovered_runs": len(rows),
        "saved_paid_labels": sum(row["old_paid_calls"] for row in rows),
        "new_physical_calls": sum(row["new_paid_calls"] for row in rows),
        "canonical_evaluations": 2000,
        "post_completion_test_calls": 4,
        "rows": rows,
    }
    assert result["saved_paid_labels"] == 1368 and result["new_physical_calls"] == 632
    target = ROOT / "results/application_recovery_audit_v1"
    target.mkdir(exist_ok=False)
    (target / "audit.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "rows"}, indent=2))


if __name__ == "__main__":
    main()
