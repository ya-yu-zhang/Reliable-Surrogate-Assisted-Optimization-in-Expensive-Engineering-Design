"""Dependency guards must reject before creating scientific records."""
import json
import pytest
from src import application_high_precheck as worker


def statuses(root, stages):
    for i, (name, stage) in enumerate(stages.items(), 1):
        folder = root / 'results' / name
        folder.mkdir(parents=True)
        (folder / 'status.json').write_text(json.dumps(dict(stage=stage, failure=None, pid=100+i)))


def test_pending_dependencies_create_no_high_record(tmp_path, monkeypatch):
    monkeypatch.setattr(worker, 'ROOT', tmp_path)
    monkeypatch.setattr(worker, 'process_inventory', lambda: [])
    statuses(tmp_path, {'reference_completion_v1': 'waiting_for_formal_batches'})
    with pytest.raises(AssertionError, match='prerequisite incomplete'):
        worker.main()
    assert not (tmp_path / 'results/application_high_precheck_v1').exists()
    assert not (tmp_path / 'configs').exists()


def test_compiled_export_still_live_rejects_before_design(tmp_path, monkeypatch):
    monkeypatch.setattr(worker, 'ROOT', tmp_path)
    monkeypatch.setattr(worker, 'process_inventory', lambda: [dict(ProcessId=103, CommandLine='-m src.finish_evidence_export')])
    statuses(tmp_path, {'reference_completion_v1': 'complete', 'application_completion_v1': 'complete',
                        'evidence_export_v1': 'compiled_pending_visual_review'})
    with pytest.raises(AssertionError, match='prerequisite still live'):
        worker.main()
    assert not (tmp_path / 'results/application_high_precheck_v1').exists()
    assert not (tmp_path / 'configs').exists()
