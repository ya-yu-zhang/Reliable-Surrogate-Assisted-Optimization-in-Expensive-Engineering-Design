"""Frozen PEM rules with an opaque callable; no optimum-dependent statistics."""
from dataclasses import asdict
from time import perf_counter

import numpy as np

from .core import Settings, GaussianRBF, init_design, make_candidates, bounds, management, choose, METHODS
from .experiment import json_line, write_array


def optimize(oracle, dim, seed, method, budget, journal, archive, lb, ub, capture='checkpoints'):
    cfg = Settings()
    if method not in METHODS or method == 'T_fixed':
        raise ValueError('Use explicit method probabilities; environment substitution is not supported')
    lb, ub = np.asarray(lb), np.asarray(ub)
    assert lb.shape == ub.shape == (dim,) and np.all(ub > lb)
    design = init_design(dim,seed)
    ntrain,n0 = dim+10,2*dim+20
    if budget<n0: raise ValueError('Budget must include complete initialization')
    x,y,residuals,monitors = [],[],[],[]
    stagnation = 0
    timers = dict(train=0.,candidates=0.,calibrate=0.,choose=0.,objective=0.,journal=0.)
    checkpoints = sorted(set(max(n0+1,int(np.ceil(budget*f))) for f in [.25,.5,.75,1]))
    variant,manager,use_upper,fixed = METHODS[method]
    for t in range(1,budget+1):
        best = min(y) if y else None
        pred,bound,state,pool = None,None,None,None
        pre = dict(event='pre',t=t,n_observed=len(y),best_before=best)
        if t<=ntrain:
            point = design[t-1]
            pre.update(mode='initial_train',mu=None,H=None,scale=None,declared=False,monitoring_ready=False)
        else:
            xx,yy = np.array(x),np.array(y)
            tick = perf_counter();model = GaussianRBF(cfg).fit(xx,yy)
            timers['train'] += perf_counter()-tick
            if t<=n0:
                point = design[t-1];pool = np.array([point]);mode,u,random_state = 'startup',None,None;k=0
            else:
                tick = perf_counter();pool = make_candidates(xx,yy,seed,t,cfg)
                timers['candidates'] += perf_counter()-tick
            tick = perf_counter();pred = model.predict(pool)
            bound = bounds(pred,model.scale,pool,residuals,t,variant,cfg)
            timers['calibrate'] += perf_counter()-tick
            state = management(monitors,stagnation,manager,fixed,cfg)
            if method=='pool_random': state['random_candidate']=True
            if t>n0:
                tick = perf_counter()
                k,mode,u,random_state = choose(pool,xx,pred,bound,best,model.scale,state,seed,t,use_upper,cfg)
                timers['choose'] += perf_counter()-tick;point=pool[k]
            declared = bool(state['monitoring_ready'] and bound['support'][k] and bound['H'][k]<best-cfg.tau_factor*model.scale)
            pre.update(mu=float(pred[k]),H=float(bound['H'][k]),scale=model.scale,
                margin=float(bound['q'][k]),neff=float(bound['neff'][k]),support=bool(bound['support'][k]),
                calibrator=str(bound['used'][k]),variant=variant,
                weighted_distance=None if np.isnan(bound['weighted_distance'][k]) else float(bound['weighted_distance'][k]),
                mode=mode,declared=declared,stagnation=stagnation,train_indices=model.indices.tolist(),**state,
                selection_index=k,mode_uniform=u,mode_rng_after=random_state,
                candidate_stream=[seed,21,t],sobol_stream=[seed,22,t])
        pre['x_unit']=point.tolist();pre['x']=(lb+(ub-lb)*point).tolist()
        tick=perf_counter()
        if pool is not None and t>n0 and (capture=='all' or t in checkpoints):
            write_array(archive,f't{t}_points',pool);write_array(archive,f't{t}_mu',pred);write_array(archive,f't{t}_H',bound['H'])
            archive.fp.flush()
        json_line(journal,pre);timers['journal'] += perf_counter()-tick
        tick=perf_counter();value=float(oracle(pre['x']));timers['objective'] += perf_counter()-tick
        if not np.isfinite(value): raise FloatingPointError('Nonfinite opaque objective')
        post=dict(event='label',t=t,y=value,best_after=value if best is None else min(best,value))
        if pre['mu'] is not None:
            residual=(value-pre['mu'])/pre['scale'];failed=value>pre['H']
            false_claim=bool(pre['declared'] and value>=best-cfg.tau_factor*pre['scale'])
            if false_claim and not failed: raise AssertionError('False claim not a subset of upper failure')
            significant=value<best-cfg.tau_factor*pre['scale']
            post.update(residual=residual,upper_failure=failed,false_claim=false_claim,
                        improvement=max(0.,best-value),significant_improvement=significant)
            residuals.append((t,point.copy(),residual));monitors.append((float(failed),pre['margin']))
            stagnation=0 if significant else stagnation+1
        x.append(point.copy());y.append(value);json_line(journal,post)
    return dict(points=x,values=y,n0=n0,timers=timers,settings=asdict(cfg),checkpoints=checkpoints)
