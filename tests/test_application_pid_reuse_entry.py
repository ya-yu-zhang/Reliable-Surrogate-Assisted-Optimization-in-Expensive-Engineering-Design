import json

import pytest

from src import application_batch_pid_reuse_entry as entry


def prepare(tmp_path):
    status = tmp_path / "results/reference_completion_v1/status.json"
    status.parent.mkdir(parents=True)
    status.write_text(json.dumps({"stage": "complete", "failure": None, "pid": 25036}), encoding="utf-8")
    audit = tmp_path / "results/solo_cost_analysis_v1/integrity_audit.json"
    audit.parent.mkdir(parents=True)
    audit.write_text(json.dumps({"runs": 54, "complete_design": True, "source_hashes_verified": True}), encoding="utf-8")


def test_reused_pid_with_unrelated_identity_is_accepted(tmp_path, monkeypatch):
    prepare(tmp_path)
    monkeypatch.setattr(entry.batch, "ROOT", tmp_path)
    monkeypatch.setattr(entry, "process_inventory", lambda: [{
        "ProcessId": 25036, "CommandLine": "python -m src.finish_high_extension"
    }])
    assert entry.prerequisite()["stage"] == "complete"


def test_identity_matched_live_prerequisite_is_rejected(tmp_path, monkeypatch):
    prepare(tmp_path)
    monkeypatch.setattr(entry.batch, "ROOT", tmp_path)
    monkeypatch.setattr(entry, "process_inventory", lambda: [{
        "ProcessId": 25036, "CommandLine": "python -m src.finish_reference_batch"
    }])
    with pytest.raises(AssertionError, match="Identity-matched"):
        entry.prerequisite()
