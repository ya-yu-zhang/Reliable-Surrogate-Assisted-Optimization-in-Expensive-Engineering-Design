import json
from src import build_sensitivity_revision as builder


def test_incomplete_sensitivity_audit_creates_no_paper(tmp_path):
    p=tmp_path/'results/model_sensitivity_analysis_v1';p.mkdir(parents=True)
    (p/'audit.json').write_text(json.dumps(dict(complete_design=False,runs=450,algorithm_evaluations=135000,
        diagnostic_evaluations=0,raw_file_hashes=1350,twenty_dim_base_cap512_invariant_runs=45,
        statistical_tests_added=0)))
    try:builder.require_complete(tmp_path)
    except AssertionError:pass
    else:raise AssertionError('incomplete sensitivity accepted')
    assert not (tmp_path/'paper').exists()
