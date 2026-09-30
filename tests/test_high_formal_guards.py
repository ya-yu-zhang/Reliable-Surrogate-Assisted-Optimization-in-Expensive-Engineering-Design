import json
from pathlib import Path
import pytest
from src import run_application_high_formal as runner


def test_missing_resource_audit_rejected_before_output(tmp_path,monkeypatch):
    monkeypatch.setattr(runner,'ROOT',tmp_path)
    with pytest.raises(FileNotFoundError):runner.main()
    assert not (tmp_path/'results/application_high_formal_v1').exists()


def test_incomplete_resource_audit_rejected_before_output(tmp_path,monkeypatch):
    monkeypatch.setattr(runner,'ROOT',tmp_path)
    p=tmp_path/'results/application_high_method_resource_analysis_v1';p.mkdir(parents=True)
    (p/'audit.json').write_text(json.dumps(dict(complete_design=False,source_hashes_verified=True,runs=8,
        algorithm_evaluations=8000,test_method_calls=0)))
    with pytest.raises(AssertionError):runner.main()
    assert not (tmp_path/'results/application_high_formal_v1').exists()
