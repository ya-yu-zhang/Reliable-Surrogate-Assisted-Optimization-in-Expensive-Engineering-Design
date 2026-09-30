import json

from src.recover_interrupted_application_run import parse_paid_prefix


def write(path, rows):
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def test_parse_complete_pairs(tmp_path):
    path = tmp_path / "events.jsonl"
    write(path, [
        {"event": "meta", "budget": 5},
        {"event": "pre", "t": 1, "n_observed": 0},
        {"event": "label", "t": 1, "y": 1.0},
    ])
    _, pre, labels, dangling, _ = parse_paid_prefix(path)
    assert len(pre) == len(labels) == 1 and dangling is None


def test_parse_dangling_unpaid_pre(tmp_path):
    path = tmp_path / "events.jsonl"
    write(path, [
        {"event": "meta", "budget": 5},
        {"event": "pre", "t": 1, "n_observed": 0},
        {"event": "label", "t": 1, "y": 1.0},
        {"event": "pre", "t": 2, "n_observed": 1},
    ])
    _, pre, labels, dangling, _ = parse_paid_prefix(path)
    assert len(pre) == len(labels) == 1 and dangling["t"] == 2
