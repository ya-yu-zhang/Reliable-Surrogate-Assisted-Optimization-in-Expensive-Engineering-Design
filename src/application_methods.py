"""Callable interfaces preserving internal and external search mechanisms."""
import os
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:
    os.environ[key]='1'
from time import perf_counter

import numpy as np
from scipy.stats import qmc

from .experiment import json_line
from .generic_internal import optimize


class BudgetLimit(Exception):
    pass


class PaidObjective:
    def __init__(self,function,lb,ub,budget):
        self.function=function;self.lb=np.asarray(lb,dtype=float);self.ub=np.asarray(ub,dtype=float)
        self.budget=budget;self.calls=0;self.points=[];self.values=[];self.objective_seconds=0.
    def __call__(self,point):
        if self.calls>=self.budget: raise BudgetLimit('Refuse extra objective call before evaluation')
        point=np.asarray(point,dtype=float)
        if point.shape!=self.lb.shape or not np.isfinite(point).all() or np.any(point<self.lb) or np.any(point>self.ub):
            raise ValueError('Invalid physical-domain proposal')
        self.calls+=1;tick=perf_counter()
        try: value=float(self.function(point.copy()))
        finally: self.objective_seconds+=perf_counter()-tick
        if not np.isfinite(value): raise FloatingPointError('Nonfinite paid application objective')
        self.points.append(point.copy());self.values.append(value);return value


def execute(oracle,dim,seed,method,journal,archive=None,capture='checkpoints'):
    budget=oracle.budget
    if method not in ['sobol','cma_es','gp_ei','turbo_1']:
        if archive is None: raise ValueError('Internal candidate archive required')
        extra=optimize(oracle,dim,seed,method,budget,journal,archive,oracle.lb,oracle.ub,capture)
        assert oracle.calls==len(extra['values'])==budget
        return {k:v for k,v in extra.items() if k not in ['points','values']}
    if method in ['gp_ei','turbo_1']:
        from .gp_references import BudgetJournal,gp_ei,turbo
        import torch
        np.random.seed(seed);torch.manual_seed(seed)
        guarded=BudgetJournal(oracle,budget,oracle.lb,oracle.ub,journal)
        extra=turbo(guarded,dim,seed) if method=='turbo_1' else gp_ei(guarded,dim,seed) or {}
        assert oracle.calls==len(guarded.values)==budget
        return dict(**extra,n0=2*dim,preparation_seconds=guarded.prepare_seconds,
                    external_search_unchanged=True)
    def evaluate(point,state):
        point=np.asarray(point);t=oracle.calls+1
        if t>budget: raise BudgetLimit('Basic reference guard before extra call')
        if point.shape!=(dim,) or np.any(point<0) or np.any(point>1) or not np.isfinite(point).all():
            raise ValueError('Invalid normalized reference proposal')
        physical=oracle.lb+(oracle.ub-oracle.lb)*point
        json_line(journal,dict(event='pre',t=t,n_observed=t-1,x_unit=point.tolist(),x=physical.tolist(),
                  best_before=min(oracle.values) if oracle.values else None,optimizer_state=state))
        value=oracle(physical)
        json_line(journal,dict(event='label',t=t,y=value,best_after=min(oracle.values)))
        return value
    if method=='sobol':
        sequence=qmc.Sobol(dim,scramble=True,seed=seed).random_base2(int(np.ceil(np.log2(budget))))
        for k,point in enumerate(sequence[:budget]):evaluate(point,dict(sequence_index=k,scrambled=True))
        extra=dict(scrambled=True,sequence_length=len(sequence),n0=None)
    else:
        import cma
        optimizer=cma.CMAEvolutionStrategy(np.full(dim,.5),.3,
            dict(bounds=[0,1],seed=seed,verbose=-9,verb_disp=0,verb_log=0))
        generation=0;partial=0
        while oracle.calls<budget:
            population=optimizer.ask();available=budget-oracle.calls;evaluations=[]
            state=dict(generation=generation,mean=optimizer.mean.tolist(),sigma=float(optimizer.sigma),population_size=len(population))
            for j,point in enumerate(population[:available]):
                evaluations.append(evaluate(point,dict(**state,individual=j)))
            if len(evaluations)==len(population):optimizer.tell(population,evaluations)
            else:partial=len(evaluations)
            generation+=1
        extra=dict(initial_mean=.5,initial_sigma=.3,bounds=[0,1],default_population=optimizer.popsize,
            ignore_convergence_stop=True,partial_final_generation_evaluations=partial,n0=None)
    assert oracle.calls==len(oracle.values)==budget
    return extra
