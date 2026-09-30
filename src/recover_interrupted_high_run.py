"""Deterministically replay a high-dimensional run and query only its unpaid suffix."""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from time import perf_counter
from unittest.mock import patch
import numpy as np
from .recover_interrupted_application_run_v3 import parse_paid_prefix,equivalent,tail_events

ROOT=Path(__file__).resolve().parents[1]
CONFIG='configs/application_high_formal.json'

def recover(rep:int,method:str,archive:Path)->dict:
    config=json.loads((ROOT/CONFIG).read_text('utf-8')); budget=1000; dataset='synt_high'
    runid=f'{method}_{dataset}_r{rep:02}_b{budget}'
    meta,old_pre,old_labels,dangling,original=parse_paid_prefix(archive/'events.jsonl')
    paid=len(old_labels); assert dangling is None
    assert all(meta[k]==v for k,v in {'dataset':dataset,'rep':rep,'method':method,'budget':budget}.items())
    directory=ROOT/config['out']/runid; assert not directory.exists()
    instances=[]; work=ROOT/'results/high_formal_recovery_work_v1'; work.mkdir(parents=True,exist_ok=True)
    physical_path=work/(runid+'.jsonl'); assert not physical_path.exists()
    from . import application_high_experiment as worker
    from .application_methods import PaidObjective
    class ReplayObjective:
        def __init__(self,function,lb,ub,requested_budget):
            assert requested_budget==budget and not instances
            self.real=PaidObjective(function,lb,ub,requested_budget); self.lb=self.real.lb; self.ub=self.real.ub
            self.budget=budget; self.calls=0; self.points=[]; self.values=[]; self.objective_seconds=0.; self.replayed=0; self.new_calls=0
            instances.append(self)
        def __call__(self,point):
            point=np.asarray(point,dtype=float); index=self.calls
            prior,current=tail_events(directory/'events.jsonl'); assert current['event']=='pre' and current['t']==index+1
            if index==0: assert prior==meta
            if index<paid:
                assert equivalent(current,old_pre[index]); np.testing.assert_allclose(point,old_pre[index]['x'],rtol=0,atol=2e-12)
                value=float(old_labels[index]['y']); self.replayed+=1
            else:
                assert self.replayed==paid
                physical.write(json.dumps({'event':'pre','t':index+1,'x':point.tolist()})+'\n'); physical.flush()
                tick=perf_counter(); value=float(self.real.function(point.copy())); self.objective_seconds+=perf_counter()-tick
                assert np.isfinite(value); self.new_calls+=1
                physical.write(json.dumps({'event':'label','t':index+1,'y':value})+'\n'); physical.flush()
            self.calls+=1; self.points.append(point.copy()); self.values.append(value); return value
    with physical_path.open('w',encoding='utf-8') as physical:
        with patch.object(worker,'PaidObjective',ReplayObjective): summary=worker.run_one(rep,method)
    oracle=instances[0]; assert oracle.calls==budget and oracle.replayed==paid and oracle.new_calls==budget-paid
    regenerated=[json.loads(x) for x in (directory/'events.jsonl').read_text('utf-8').splitlines()]
    assert regenerated[0]==meta
    old=[x for pair in zip(old_pre,old_labels) for x in pair]
    assert all(equivalent(a,b) for a,b in zip(regenerated[1:1+2*paid],old))
    physical_path.replace(directory/'recovery_physical_calls.jsonl')
    record={'schema':'high_paid_prefix_recovery_v1','runid':runid,'archive':archive.relative_to(ROOT).as_posix(),
            'original_journal_sha256':hashlib.sha256(original).hexdigest(),'old_paid_calls':paid,
            'new_paid_calls':budget-paid,'complete_prefix_states_and_labels_numerically_equivalent':True,
            'candidate_absolute_tolerance':2e-12,'optimizer_state_float_absolute_tolerance':2e-12,
            'post_completion_test_calls':summary['test_method_calls'],'objective_timing_scope':'new_suffix_only',
            'optimization_timing_scope':'full_deterministic_replay_plus_new_suffix'}
    (directory/'recovery.json').write_text(json.dumps(record,indent=2),encoding='utf-8'); return record

def main():
    p=argparse.ArgumentParser();p.add_argument('--rep',type=int,required=True);p.add_argument('--method',required=True);p.add_argument('--archive',required=True)
    a=p.parse_args(); print(json.dumps(recover(a.rep,a.method,Path(a.archive)),indent=2))
if __name__=='__main__':main()
