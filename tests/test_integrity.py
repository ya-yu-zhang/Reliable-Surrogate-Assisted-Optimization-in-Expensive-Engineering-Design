import json
from pathlib import Path
import numpy as np
from src.core import (init_design, weighted_quantile, bounds, Settings, reflect, distances, make_candidates, choose)
from src.experiment import run_one, problem


def test_quantile_inverse_cdf_no_interpolation():
    assert weighted_quantile([3,1,2],[1,8,1],.9) == 2
    assert weighted_quantile([-3,-1],[1,1],.9) == -1


def test_fallback_support_and_nonnegative_margin():
    points=np.ones((2,10))*.5
    residuals=[(i, np.ones(10)*i/100, -1.) for i in range(1,21)]
    result=bounds(np.zeros(2),1.,points,residuals,21,'ST')
    assert np.all(result['q']==0)
    assert np.all(result['used']=='G')  # T's ESS <20 and ST cannot have ESS20 here.
    assert np.all(result['support'])
    result=bounds(np.zeros(2),1.,points,residuals[:19],20,'ST')
    assert not np.any(result['support'])


def test_design_repeatable_and_candidates_unique():
    design=init_design(10,42)
    np.testing.assert_array_equal(design,init_design(10,42))
    p=make_candidates(design,np.arange(len(design)),42,41)
    assert p.shape==(256,10)
    assert np.all((p>=0)&(p<=1))
    assert distances(p,design).min()>Settings().duplicate_tol
    np.testing.assert_allclose(reflect(np.array([-2.2,-.1,1.1,2.2])),[.2,.1,.9,.2])


def test_bbob_known_optimum():
    for f in range(1,25):
        p=problem(f,10,1)
        assert abs(p(p.optimum.x)-p.optimum.y)<1e-6


def test_temporal_upper_mode_cannot_change_selected_point():
    # T/G give a candidate-independent additive correction. This is an
    # algebraic limitation of the supplied plan, not a tuning issue.
    rng=np.random.default_rng(91)
    x=rng.random((30,10)); points=rng.random((256,10)); mu=rng.normal(size=256)
    bound=dict(H=mu+0.1,support=np.ones(256,dtype=bool))
    state=dict(p=0.,a=0.,monitoring_ready=True)
    k,mode,_,_=choose(points,x,mu,bound,10.,1.,state,91,31,True)
    kk,mode2,_,_=choose(points,x,mu,bound,10.,1.,state,91,31,False)
    assert k==kk==np.argmin(mu) and mode=='upper' and mode2=='mean'


def test_event_order_budget_and_prefix(tmp_path):
    common=(1,10,1,0,'PEM_T')
    short=run_one((*common,50,str(tmp_path/'short'),'all'))
    long=run_one((*common,60,str(tmp_path/'long'),'all'))
    assert short['algorithm_evaluations']==50
    assert long['algorithm_evaluations']==60
    def read(summary,root):
        return [json.loads(v) for v in (root/summary['runid']/'events.jsonl').read_text('utf-8').splitlines()]
    ss=read(short,tmp_path/'short')[1:]
    ll=read(long,tmp_path/'long')[1:]
    assert ss==ll[:len(ss)]
    for pre,post in zip(ss[::2],ss[1::2]):
        assert pre['event']=='pre' and post['event']=='label'
        assert pre['t']==post['t']==pre['n_observed']+1
        assert 'y' not in pre
        if post.get('false_claim'):
            assert post['upper_failure']
    # Diagnostic evaluation in a separate object cannot affect search events.
    diag=problem(1,10,1); diag([0.]*10)
    assert read(short,tmp_path/'short')[1:]==ss
