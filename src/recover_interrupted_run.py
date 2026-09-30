"""Replay verified paid labels through unchanged code; query only the unpaid suffix."""
import os
for name in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:
    os.environ[name]='1'
import argparse
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import ioh
import numpy as np

ROOT=Path(__file__).resolve().parents[1]


def tail_events(path):
    with path.open('rb') as stream:
        stream.seek(0,2);end=stream.tell();stream.seek(max(0,end-65536))
        lines=stream.read().splitlines()
    return [json.loads(v) for v in lines[-2:]]


def recover(kind,fid,dim,instance,rep,method,budget,out,archive,capture='all'):
    archive=Path(archive);out=Path(out)
    original_file=archive/'events.jsonl'
    original_bytes=original_file.read_bytes();events=[json.loads(v) for v in original_bytes.decode('utf-8').splitlines()]
    assert events[0]['event']=='meta' and len(events)%2==1
    old_pre,old_labels=events[1::2],events[2::2];paid=len(old_labels)
    assert 0<paid<budget and len(old_pre)==paid
    meta=events[0]
    for key,value in dict(fid=fid,dim=dim,instance=instance,rep=rep,method=method,budget=budget).items():
        assert meta[key]==value
    for t,(pre,label) in enumerate(zip(old_pre,old_labels),1):
        assert pre['event']=='pre' and label['event']=='label' and pre['t']==label['t']==t
        assert pre['n_observed']==t-1 and 'y' not in pre and np.isfinite(label['y'])
    runid=f'{method}_f{fid:02}_d{dim}_i{instance}_r{rep}_b{budget}'
    directory=out/runid
    if (directory/'summary.json').exists():raise RuntimeError('Recovered summary already exists; do not replay twice')
    if (directory/'events.jsonl').exists():raise RuntimeError('Another incomplete recovery preserved; refuse overwrite')
    directory.mkdir(parents=True,exist_ok=True)
    original_factory=ioh.get_problem;instances=[]
    physical_path=directory/'recovery_physical_calls.jsonl'
    with physical_path.open('w',encoding='utf-8') as physical:
        class ReplayProblem:
            def __init__(self,problem):self.problem=problem;self.consumed=0;self.new_calls=0;self.replayed=0
            def __getattr__(self,name):return getattr(self.problem,name)
            @property
            def state(self):
                # This counts original paid calls plus new physical calls, never replay requests.
                return SimpleNamespace(evaluations=paid+self.problem.state.evaluations)
            def __call__(self,point):
                i=self.consumed
                assert i<budget
                previous,current=tail_events(directory/'events.jsonl')
                assert current['event']=='pre' and current['t']==i+1 and current['n_observed']==i
                if i==0:assert previous==meta, 'Frozen source/package/initialization metadata changed'
                if i and i<=paid:assert previous==old_labels[i-1]
                if i<paid:
                    copied=dict(current);copied.pop('preparation_seconds',None)
                    stored=dict(old_pre[i]);stored.pop('preparation_seconds',None)
                    assert copied==stored, f'Prefix state mismatch at {i+1}; no suffix call allowed'
                    np.testing.assert_array_equal(point,stored['x'])
                    value=old_labels[i]['y'];self.replayed+=1
                else:
                    assert self.replayed==paid and paid+self.new_calls<budget
                    physical.write(json.dumps(dict(event='pre',t=i+1,old_paid_calls=paid,new_paid_calls=self.new_calls,
                        x=np.asarray(point).tolist()))+'\n');physical.flush()
                    value=float(self.problem(point));self.new_calls+=1
                    physical.write(json.dumps(dict(event='label',t=i+1,y=value,new_paid_calls=self.new_calls))+'\n');physical.flush()
                self.consumed+=1;return value
        def factory(*args,**kwargs):
            assert not instances
            problem=ReplayProblem(original_factory(*args,**kwargs));instances.append(problem);return problem
        with patch.object(ioh,'get_problem',factory):
            if kind=='gp':
                from .gp_references import run_one
                summary=run_one(fid,dim,instance,rep,method,budget,out)
            else:
                from .experiment import run_one
                summary=run_one((fid,dim,instance,rep,method,budget,str(out),capture))
        oracle=instances[0]
        assert oracle.replayed==paid and oracle.new_calls==budget-paid and oracle.consumed==budget
        assert oracle.problem.state.evaluations==budget-paid
    regenerated=[json.loads(v) for v in (directory/'events.jsonl').read_text('utf-8').splitlines()]
    for a,b in zip(regenerated[1:1+2*paid],events[1:]):
        a.pop('preparation_seconds',None);b.pop('preparation_seconds',None);assert a==b
    recovery=dict(runid=runid,kind=kind,original_archive=str(archive),original_journal_sha256=hashlib.sha256(original_bytes).hexdigest(),
        old_paid_calls=paid,new_paid_calls=oracle.new_calls,physical_total=budget,replayed_calls_not_reevaluated=paid,
        complete_prefix_states_and_labels_equal=True,optimizer_source_unchanged=True,
        elapsed_is_reconstruction_segment_not_uninterrupted_runtime=True,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (directory/'recovery.json').write_text(json.dumps(recovery,indent=2),encoding='utf-8')
    return summary,recovery


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--kind',choices=['gp','internal'],default='gp')
    ap.add_argument('--archive',required=True);ap.add_argument('--fid',type=int,required=True)
    ap.add_argument('--dim',type=int,required=True);ap.add_argument('--instance',type=int,required=True)
    ap.add_argument('--rep',type=int,required=True);ap.add_argument('--method',required=True)
    ap.add_argument('--budget',type=int);ap.add_argument('--out',required=True);args=ap.parse_args()
    recover(args.kind,args.fid,args.dim,args.instance,args.rep,args.method,args.budget or 10*args.dim,args.out,args.archive)


if __name__=='__main__':main()
