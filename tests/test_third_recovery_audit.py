import hashlib
import json
from pathlib import Path

from src.audit_third_recovery import audit_run, budget_from_runid, event_equal


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_event_comparison_only_ignores_preparation_time():
    assert event_equal({"event": "pre", "t": 1, "preparation_seconds": 1.0},
                       {"event": "pre", "t": 1, "preparation_seconds": 9.0})
    assert not event_equal({"event": "pre", "t": 1, "x": [0]},
                           {"event": "pre", "t": 1, "x": [1]})
    assert budget_from_runid("gp_ei_f01_d2_i4_r0_b20") == 20


def test_single_run_audit_proves_prefix_suffix_and_accounting(tmp_path):
    runid = "gp_ei_f01_d2_i4_r0_b4"
    archived = tmp_path / "archive"
    current = tmp_path / "results" / "gp_ei_reference_v1" / runid
    archived.mkdir(parents=True)
    current.mkdir(parents=True)

    meta = {"event": "meta", "runid": runid}
    pairs = []
    for t in range(1, 5):
        pairs.extend(({"event": "pre", "t": t, "x": [t, -t]},
                      {"event": "label", "t": t, "y": float(t)}))
    old = [meta, *pairs[:4]]
    full = [meta, *pairs]
    physical = []
    for pre, label in zip(pairs[4::2], pairs[5::2]):
        physical.extend((
            {"event": "pre", "t": pre["t"], "x": pre["x"], "old_paid_calls": 2},
            {"event": "label", "t": label["t"], "y": label["y"], "new_paid_calls": label["t"] - 2},
        ))
    write_jsonl(archived / "events.jsonl", old)
    write_jsonl(current / "events.jsonl", full)
    write_jsonl(current / "recovery_physical_calls.jsonl", physical)
    (current / "recovery.json").write_text(json.dumps({
        "old_paid_calls": 2,
        "new_paid_calls": 2,
        "physical_total": 4,
        "complete_prefix_states_and_labels_equal": True,
        "optimizer_source_unchanged": True,
    }), encoding="utf-8")
    (current / "summary.json").write_text(json.dumps({
        "algorithm_evaluations": 4,
        "diagnostic_evaluations": 0,
    }), encoding="utf-8")

    row = {
        "source": "gp_ei_reference_v1",
        "runid": runid,
        "paid_labels": 2,
        "pending_pre": 0,
        "archive": "archive",
        "file_sha256": {"events.jsonl": sha256(archived / "events.jsonl")},
    }
    audited = audit_run(tmp_path, row, set())
    assert audited["new_physical_calls"] == 2
    assert audited["archived_prefix_exactly_equal"]
    assert audited["physical_suffix_exactly_equal"]
    assert audited["redundant_recovery_validation_calls"] == 0
