from pathlib import Path
import shutil
import json

import pytest

from src import report_application
from src import analyze_application
from src import build_integrated_manuscripts


def test_application_report_refuses_missing_complete_batch_without_artifacts(tmp_path,monkeypatch):
    root=Path(__file__).resolve().parents[1]
    (tmp_path/'configs').mkdir()
    shutil.copyfile(root/'configs/application_formal.json',tmp_path/'configs/application_formal.json')
    monkeypatch.setattr(report_application,'ROOT',tmp_path)
    monkeypatch.setattr(report_application,'OUT',tmp_path/'results/application_report_v1')
    monkeypatch.setattr(analyze_application,'ROOT',tmp_path)
    with pytest.raises(FileNotFoundError):report_application.main()
    assert not (tmp_path/'results/application_report_v1').exists()
    assert not (tmp_path/'docs/LassoBench正式机制迁移结果.md').exists()


def test_manuscripts_refuse_live_reference_before_running_reports(tmp_path,monkeypatch):
    path=tmp_path/'results/reference_completion_v1';path.mkdir(parents=True)
    (path/'status.json').write_text(json.dumps(dict(stage='waiting_for_formal_batches',failure=None,pid=123)))
    monkeypatch.setattr(build_integrated_manuscripts,'ROOT',tmp_path)
    monkeypatch.setattr(build_integrated_manuscripts,'process_inventory',lambda:[])
    def refuse_reports(*args):raise AssertionError('Report tools must never run before completion')
    monkeypatch.setattr(build_integrated_manuscripts,'run',refuse_reports)
    with pytest.raises(AssertionError):build_integrated_manuscripts.main()
    assert not (tmp_path/'paper').exists()
    assert not (tmp_path/'results/application_report_v1').exists()
