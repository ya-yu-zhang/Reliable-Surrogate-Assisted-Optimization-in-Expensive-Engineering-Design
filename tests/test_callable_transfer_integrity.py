import json
from pathlib import Path
import zipfile

import ioh
import numpy as np
import pytest

from src.application_methods import PaidObjective,BudgetLimit,execute
from src.experiment import run_one
from src.basic_references import run_one as reference_run


def read_events(file):
    return [json.loads(line) for line in file.read_text('utf-8').splitlines()]


@pytest.mark.parametrize('method',['greedy','fixed01','PEM_T','PEM_ST'])
def test_callable_internal_matches_frozen_bbob_trajectory(tmp_path,method):
    fid,dim,instance,rep,budget=6,2,4,0,60
    original=run_one((fid,dim,instance,rep,method,budget,str(tmp_path/'original'),'checkpoints'))
    objective=ioh.get_problem(fid,dimension=dim,instance=instance,problem_class=ioh.ProblemClass.BBOB)
    oracle=PaidObjective(objective,np.full(dim,-5.),np.full(dim,5.),budget)
    journal=tmp_path/'events.jsonl';pool=tmp_path/'pools.npz'
    with journal.open('w',encoding='utf-8') as stream,zipfile.ZipFile(pool,'w') as archive:
        extra=execute(oracle,dim,original['seed'],method,stream,archive)
    historical=tmp_path/'original'/original['runid']/'events.jsonl'
    assert read_events(journal)==read_events(historical)[1:]
    assert oracle.calls==objective.state.evaluations==budget and min(oracle.values)==original['best']
    assert extra['n0']==original['n0'] and any(e.get('monitoring_ready') for e in read_events(journal))
    with zipfile.ZipFile(pool) as left,zipfile.ZipFile(historical.parent/'candidate_pools.npz') as right:
        assert left.namelist()==right.namelist()
        assert all(left.read(name)==right.read(name) for name in left.namelist())


@pytest.mark.parametrize('method',['sobol','cma_es'])
def test_callable_references_match_original_search(tmp_path,method):
    fid,dim,instance,rep=1,2,4,0
    original=reference_run((fid,dim,instance,rep,method,str(tmp_path/'original')))
    seed=100000*dim+1000*fid+10*instance+rep;budget=10*dim
    objective=ioh.get_problem(fid,dimension=dim,instance=instance,problem_class=ioh.ProblemClass.BBOB)
    oracle=PaidObjective(objective,np.full(dim,-5.),np.full(dim,5.),budget)
    journal=tmp_path/'events.jsonl'
    with journal.open('w',encoding='utf-8') as stream:execute(oracle,dim,seed,method,stream)
    historical=tmp_path/'original'/original['runid']/'events.jsonl'
    assert read_events(journal)==read_events(historical)[1:]
    assert oracle.calls==objective.state.evaluations==budget


def test_paid_guard_refuses_extra_or_invalid_before_objective():
    actual=[]
    oracle=PaidObjective(lambda x:actual.append(x) or 1.,[-1,-1],[1,1],2)
    with pytest.raises(ValueError):oracle([2.,0.])
    assert oracle.calls==len(actual)==0
    oracle([0.,0.]);oracle([0.,0.])
    with pytest.raises(BudgetLimit):oracle([0.,0.])
    assert oracle.calls==len(actual)==2


def test_pre_is_persisted_before_every_unknown_objective_label(tmp_path):
    journal=tmp_path/'events.jsonl'; actual=[]
    def opaque(point):
        events=read_events(journal);pre=events[-1]
        assert pre['event']=='pre' and pre['t']==len(actual)+1 and pre['n_observed']==len(actual)
        assert 'y' not in pre and 'error' not in pre and 'optimum' not in pre
        assert sum(e['event']=='label' for e in events)==len(actual)
        actual.append(point.copy());return float(.1+np.square(point).sum())
    oracle=PaidObjective(opaque,np.full(3,-1.),np.full(3,1.),52)
    with journal.open('w',encoding='utf-8') as stream,zipfile.ZipFile(tmp_path/'pools.npz','w') as archive:
        execute(oracle,3,923517,'PEM_ST',stream,archive)
    events=read_events(journal)
    for pre,label in zip(events[::2],events[1::2]):
        if pre['mu'] is not None:
            assert label['residual']==(label['y']-pre['mu'])/pre['scale']
            assert not label['false_claim'] or label['upper_failure']
            assert max(pre['train_indices'])<pre['t']-1
    assert oracle.calls==len(actual)==52
