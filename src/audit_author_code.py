"""Executable budget-control counterexample, NOT a TuRBO performance run."""
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import numpy as np


def main():
    root = Path(__file__).resolve().parents[1]
    path = root/'literature/source-code/TuRBO/turbo/turbo_1.py'
    tree = ast.parse(path.read_text('utf-8'))
    cls = next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Turbo1')
    method = next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='optimize')
    # Execute the unmodified author's budget-control method with fake GP decisions.
    # No torch/GP dependencies, benchmark labels, or optimizer-performance claims.
    namespace = dict(np=np,deepcopy=deepcopy,
                     latin_hypercube=lambda n,d:np.full((n,d),.5),
                     from_unit_cube=lambda x,l,u:l+(u-l)*x,
                     to_unit_cube=lambda x,l,u:(x-l)/(u-l))
    exec(compile(ast.Module(body=[method],type_ignores=[]),str(path),'exec'),namespace)
    class Harness:
        optimize=namespace['optimize']
        def __init__(self):
            self.n_init=4; self.dim=2; self.max_evals=7; self.n_evals=0
            self.batch_size=1; self.verbose=False; self.lb=np.zeros(2); self.ub=np.ones(2)
            self.X=np.empty((0,2)); self.fX=np.empty((0,1)); self._fX=[]
            self.length_min=.01; self.n_training_steps=50; self.calls=0
        def f(self,x):
            self.calls+=1
            return float(self.calls)
        def _restart(self):
            self._X=[];self._fX=[];self.length=1
        def _create_candidates(self,*args,**kwargs):
            return np.zeros((1,2)),np.zeros((1,1)),{}
        def _select_candidates(self,*args):
            return np.zeros((1,2))
        def _adjust_length(self,*args):
            self.length=0
    harness=Harness();harness.optimize()
    assert harness.calls==harness.n_evals==9 > harness.max_evals
    out=root/'results/author_code_audit';out.mkdir(parents=True,exist_ok=True)
    report=dict(source='https://github.com/uber-research/TuRBO',commit='de0db39f481d9505bb3610b7b7aa0ebf7702e4a5',
                source_file='turbo/turbo_1.py',source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                original_method_unmodified=True,performance_experiment=False,gp_stub=True,
                requested_budget=7,initialization_per_restart=4,batch_size=1,
                actual_calls=harness.calls,recorded_optimizer_calls=harness.n_evals,
                trigger='Forced early trust-region restart with two evaluations remaining',
                mitigation='Strict objective-call guard and immutable external journal; retain charged prefix')
    (out/'turbo_restart_budget_counterexample.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
