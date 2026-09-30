import io
import json
from pathlib import Path
import numpy as np
import pytest
pytest.importorskip('torch', reason='GP reference checks require the isolated .venv-baselines environment.')
from src.gp_references import BudgetJournal, BudgetExhausted, expected_improvement, run_one


def test_guard_stops_before_extra_target_call():
    calls=[];stream=io.StringIO()
    oracle=BudgetJournal(lambda x:calls.append(x) or sum(x),2,[0,0],[1,1],stream)
    oracle([.1,.2]);oracle([.3,.4])
    with pytest.raises(BudgetExhausted):oracle([.5,.6])
    assert len(calls)==2
    events=[json.loads(v) for v in stream.getvalue().splitlines()]
    assert [v['event'] for v in events]==['pre','label','pre','label']
    assert all('y' not in v for v in events if v['event']=='pre')


def test_ei_zero_uncertainty_has_correct_deterministic_limit():
    result=expected_improvement(np.array([1.,3.,2.]),np.zeros(3),2.)
    np.testing.assert_array_equal(result,[1.,0.,0.])


def test_author_restart_keeps_paid_prefix_in_external_journal():
    import sys
    from src.gp_references import AUTHOR
    sys.path.insert(0,str(AUTHOR))
    from turbo import Turbo1
    stream=io.StringIO();calls=[]
    oracle=BudgetJournal(lambda x:calls.append(x) or float(len(calls)),7,[0,0],[1,1],stream)
    optimizer=Turbo1(oracle,np.zeros(2),np.ones(2),n_init=4,max_evals=7,verbose=False)
    # Stub only GP decisions; run the author's actual restart and archive control.
    optimizer._create_candidates=lambda *a,**kw:(np.zeros((1,2)),np.zeros((1,1)),{})
    optimizer._select_candidates=lambda *a:np.zeros((1,2))
    optimizer._adjust_length=lambda *a:setattr(optimizer,'length',0.)
    with pytest.raises(BudgetExhausted):optimizer.optimize()
    assert len(calls)==len(oracle.values)==7
    assert optimizer.n_evals==len(optimizer.fX)==5
    # The last two charged restart labels remain available despite the partial batch.
    labels=[json.loads(v) for v in stream.getvalue().splitlines() if json.loads(v)['event']=='label']
    assert len(labels)==7 and [v['y'] for v in labels][-2:]==[6.,7.]


@pytest.mark.parametrize('method',['gp_ei','turbo_1'])
def test_actual_reference_budget_and_seed_reproducibility(tmp_path,method):
    outcomes=[]
    for directory in ['first','second']:
        result=run_one(1,2,4,0,method,8,tmp_path/directory)
        assert result['algorithm_evaluations']==8
        events=[json.loads(v) for v in (tmp_path/directory/result['runid']/'events.jsonl').read_text().splitlines()]
        pre,post=events[1::2],events[2::2]
        assert len(pre)==len(post)==8
        assert all(a['n_observed']==a['t']-1 and 'y' not in a for a in pre)
        outcomes.append([(a['x'],b['y'],a['numpy_rng_hash'],a['torch_rng_hash']) for a,b in zip(pre,post)])
    assert outcomes[0]==outcomes[1]
