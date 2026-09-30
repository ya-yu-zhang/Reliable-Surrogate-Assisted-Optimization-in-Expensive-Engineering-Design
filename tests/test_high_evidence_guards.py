import json
from src import build_high_extension_revision as builder
from src import finish_high_evidence_export as exporter


def test_incomplete_high_audit_refuses_builder(tmp_path):
    p=tmp_path/'results/application_high_analysis_v1';p.mkdir(parents=True)
    (p/'audit.json').write_text(json.dumps(dict(complete_design=False,runs=160,algorithm_evaluations=160000,
        cv_fold_solves=800000,post_completion_test_calls=160,statistical_tests_added=0,
        not_added_to_primary_three_test_family=True)))
    try:builder.require_complete(tmp_path)
    except AssertionError:pass
    else:raise AssertionError('incomplete audit accepted')
    assert not (tmp_path/'paper').exists()


def test_existing_export_record_refuses_duplicate(tmp_path,monkeypatch):
    monkeypatch.setattr(exporter,'ROOT',tmp_path);monkeypatch.setattr(exporter,'OUT',tmp_path/'results/high_evidence_export_v1')
    exporter.OUT.mkdir(parents=True)
    try:exporter.main()
    except AssertionError as error:assert 'duplicate' in str(error)
    else:raise AssertionError('duplicate exporter accepted')
