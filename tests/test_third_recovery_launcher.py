from pathlib import Path

import pytest

from src import resume_interrupted_gp_batch_v4_parallel as launcher


def row(pid, command):
    return {"ProcessId": pid, "CommandLine": command}


def test_strict_python_module_matching_is_configuration_isolated():
    rows = [
        row(1, 'powershell -Command "python -m src.resume_interrupted_gp_batch_v4_parallel --config configs/turbo_reference.json"'),
        row(2, 'python.exe -m src.resume_interrupted_gp_batch_v4_parallel --config configs/turbo_reference.json'),
        row(3, 'python.exe -m src.resume_interrupted_gp_batch_v4_parallel --config configs/gp_ei_reference.json'),
        row(4, 'python.exe -m src.gp_references --method turbo_1'),
    ]
    assert [item["ProcessId"] for item in launcher.matching_inventory(rows, "configs/turbo_reference.json")] == [2]


def test_partial_route_and_unarchived_partial_refusal(tmp_path, monkeypatch):
    monkeypatch.setattr(launcher, "ROOT", tmp_path)
    monkeypatch.setattr(launcher, "expected_signature", lambda *args: {"budget": args[-1]})
    out = tmp_path / "results"
    out.mkdir()
    runid = "gp_ei_f01_d2_i4_r0_b20"
    archive = tmp_path / "archive"
    archive.mkdir()
    eligible = {runid: {"archive": "archive"}}
    actual, command = launcher.command_for((1, 2, 4, 0, "gp_ei"), out, eligible)
    assert actual == runid and "src.recover_interrupted_run" in command and str(archive) in command
    (out / runid).mkdir()
    with pytest.raises(RuntimeError, match="unarchived incomplete"):
        launcher.command_for((1, 2, 4, 0, "gp_ei"), out, eligible)
