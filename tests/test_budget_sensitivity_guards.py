import json
import pytest
from src import run_budget_performance_sensitivity as runner
from src.experiment import run_one
from src.analyze_budget_performance_sensitivity import audit_internal,audit_basic
from src.budget_sensitivity_worker import basic


def test_incomplete_prior_evidence_rejects_before_output(tmp_path,monkeypatch):
    monkeypatch.setattr(runner,'ROOT',tmp_path);monkeypatch.setattr(runner,'process_inventory',lambda:[])
    p=tmp_path/'results/sensitivity_evidence_export_v1';p.mkdir(parents=True)
    (p/'status.json').write_text(json.dumps(dict(stage='waiting_for_sensitivity_audit',failure=None,pid=1)))
    with pytest.raises(AssertionError):runner.main()
    assert not (tmp_path/'results/budget_performance_sensitivity_v1').exists()


def test_actual_internal_and_basic_arbitrary_budget_journals(tmp_path):
    internal=run_one((1,3,4,0,'PEM_T',52,str(tmp_path/'internal'),'checkpoints'))
    directory=tmp_path/'internal'/internal['runid'];events,labels,error,optimum=audit_internal(directory,internal)
    assert len(labels)==52 and error>=0 and optimum is not None
    external=basic(1,2,4,0,'sobol',8,tmp_path/'basic')
    directory=tmp_path/'basic'/external['runid'];events,labels,error,optimum=audit_basic(directory,external)
    assert len(labels)==8 and error>=0 and optimum is None
