"""Actual opaque-callable trajectory fixture and intentional information corruption."""
import json
import zipfile
import numpy as np
import pytest
from src.application_methods import PaidObjective, execute
from src.application_journal_audit import audit_journal
from src.application_high_method_resource import TimedJournal, run
from src.experiment import json_line
from time import perf_counter


def fixture(tmp_path):
    dim,budget = 3,52
    oracle = PaidObjective(lambda x:float(np.dot(x,x)),np.full(dim,-1.),np.full(dim,1.),budget)
    sig = dict(dim=dim,budget=budget,method='PEM_ST')
    data = {'fixture':'no author data'}
    start = perf_counter()
    with (tmp_path/'events.jsonl').open('w') as stream,(tmp_path/'timing.jsonl').open('w') as timing,zipfile.ZipFile(
            tmp_path/'candidate_pools.npz','w') as archive:
        journal = TimedJournal(stream,timing,start)
        json_line(journal,dict(event='meta',**sig,data_hashes=data,fold_hash='fixture',optimum_known=False))
        extra = execute(oracle,dim,123,'PEM_ST',journal,archive,'checkpoints')
    index = int(np.argmin(oracle.values))
    summary = dict(signature=sig,data_hashes=data,fold_hash='fixture',optimum_known=False,
                   algorithm_evaluations=budget,cv_fold_solves=5*budget,best_evaluation=index+1,
                   best_validation_loss=oracle.values[index],best_config=oracle.points[index].tolist(),
                   exact_duplicate_calls=budget-len(np.unique(np.asarray(oracle.points),axis=0)),**extra)
    return summary


def test_actual_paid_fixture_has_complete_states_and_separate_timing(tmp_path):
    summary = fixture(tmp_path)
    audit_journal(tmp_path,summary)
    timing = [json.loads(v) for v in (tmp_path/'timing.jsonl').read_text().splitlines()]
    assert [v['t'] for v in timing] == list(range(1,53))
    events = [json.loads(v) for v in (tmp_path/'events.jsonl').read_text().splitlines()]
    assert all('cumulative_seconds' not in v for v in events)


def test_future_training_information_is_rejected(tmp_path):
    summary = fixture(tmp_path)
    path = tmp_path/'events.jsonl'; events = [json.loads(v) for v in path.read_text().splitlines()]
    for pre in events[1::2]:
        if pre['mu'] is not None:
            pre['train_indices'][0] = pre['t']; break
    path.write_text('\n'.join(json.dumps(v) for v in events)+'\n')
    with pytest.raises(AssertionError):
        audit_journal(tmp_path,summary)


def test_resource_worker_cannot_run_before_six_call_audit(tmp_path,monkeypatch):
    from src import application_high_method_resource as worker
    monkeypatch.setattr(worker,'ROOT',tmp_path)
    with pytest.raises(FileNotFoundError):
        run('PEM_T')
    assert not (tmp_path/'results').exists()
