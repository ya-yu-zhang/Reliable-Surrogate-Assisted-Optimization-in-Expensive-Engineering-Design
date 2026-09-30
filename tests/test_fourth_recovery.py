import json

import pytest

from src.archive_fourth_interruption import inspect_events, module_from_command


def write(path, rows):
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_fourth_archive_accepts_only_complete_paid_pairs(tmp_path):
    events = [{"event": "meta"}]
    for t in range(1, 4):
        events += [
            {"event": "pre", "t": t, "n_observed": t - 1, "x": [t]},
            {"event": "label", "t": t, "y": float(t)},
        ]
    path = tmp_path / "events.jsonl"
    write(path, events)
    assert inspect_events(path) == (3, 0)
    write(path, events + [{"event": "pre", "t": 4, "n_observed": 3, "x": [4]}])
    with pytest.raises(AssertionError):
        inspect_events(path)


def test_module_parser_distinguishes_recovery_processes():
    assert module_from_command('"C:/Python/python.exe" -m src.gp_references --fid 1') == "src.gp_references"
    assert module_from_command("pwsh -Command Get-Process") is None
