"""Objective-free full audit and descriptive 5D/10D/15D performance summaries."""
from dataclasses import asdict
import hashlib,importlib.metadata,itertools,json
from pathlib import Path
import numpy as np
import pandas as pd
from .core import Settings,METHODS,bounds,management
from .experiment import code_hash
from .basic_references import fingerprint as basic_hash

ROOT=Path(__file__).resolve().parents[1];INTERNAL=['greedy','fixed01','fixed03','pool_random','PEM_T','PEM_ST']
BASIC=['sobol','cma_es'];GP=['gp_ei','turbo_1']


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def gp_hash():
    h=hashlib.sha256((ROOT/'src/gp_references.py').read_bytes())
    for name in ['turbo_1.py','gp.py','utils.py','__init__.py']:
        h.update(name.encode());h.update((ROOT/'literature/source-code/TuRBO/turbo'/name).read_bytes())
    return h.hexdigest()


def read(directory,budget):
    events=[json.loads(v) for v in (directory/'events.jsonl').read_text('utf-8').splitlines()]
    assert len(events)==1+2*budget and events[0]['event']=='meta'
    return events


def audit_internal(directory,summary):
    sig=summary['signature'];dim,budget,method=sig['dim'],sig['budget'],sig['method'];cfg=Settings();events=read(directory,budget)
    assert sig['code_hash']==code_hash() and sig['settings']==asdict(cfg) and method in INTERNAL
    assert all(events[0][k]==v for k,v in sig.items());ntrain,n0=dim+10,2*dim+20
    variant,manager,_,fixed=METHODS[method];labels=[];points=[];residuals=[];monitors=[];stagnation=0
    checkpoints=sorted(set(max(n0+1,int(np.ceil(budget*f))) for f in [.25,.5,.75,1]))
    assert events[0]['checkpoints']==checkpoints
    for t,(pre,label) in enumerate(zip(events[1::2],events[2::2]),1):
        assert pre['event']=='pre' and label['event']=='label' and pre['t']==label['t']==t and pre['n_observed']==t-1
        assert pre['best_before']==(min(labels) if labels else None)
        u,x=np.asarray(pre['x_unit']),np.asarray(pre['x']);assert u.shape==x.shape==(dim,) and np.all((u>=0)&(u<=1))
        assert np.allclose(x,-5+10*u,rtol=0,atol=1e-13) and np.isfinite(label['y'])
        if t<=ntrain:assert pre['mode']=='initial_train' and pre['mu'] is None
        else:
            assert len(pre['train_indices'])==len(set(pre['train_indices']))==min(t-1,256) and max(pre['train_indices'])<t-1
            result=bounds(np.array([pre['mu']]),pre['scale'],u[None,:],residuals,t,variant,cfg)
            for field,column in [('H','H'),('margin','q'),('neff','neff')]:assert np.isclose(pre[field],result[column][0],rtol=1e-12,atol=1e-12)
            state=management(monitors,stagnation,manager,fixed,cfg);assert all(pre[n]==v for n,v in state.items())
            before=min(labels);declared=bool(state['monitoring_ready'] and result['support'][0] and pre['H']<before-cfg.tau_factor*pre['scale'])
            r=(label['y']-pre['mu'])/pre['scale'];failure=label['y']>pre['H'];false=bool(declared and label['y']>=before-cfg.tau_factor*pre['scale'])
            significant=label['y']<before-cfg.tau_factor*pre['scale'];assert pre['declared']==declared
            assert label['residual']==r and label['upper_failure']==failure and label['false_claim']==false and label['significant_improvement']==significant
            residuals.append((t,u.copy(),r));monitors.append((float(failure),pre['margin']));stagnation=0 if significant else stagnation+1
        labels.append(label['y']);points.append(u);assert label['best_after']==min(labels)
    assert summary['algorithm_evaluations']==budget and summary['diagnostic_evaluations']==0 and summary['n0']==n0
    assert summary['best']==min(labels) and summary['error']==max(min(labels)-summary['optimum'],0)
    with np.load(directory/'candidate_pools.npz') as archive:
        assert set(archive.files)=={f't{t}_{n}' for t in checkpoints for n in ['points','mu','H']}
        for t in checkpoints:
            pre=events[2*t-1];k=pre['selection_index'];assert np.array_equal(archive[f't{t}_points'][k],pre['x_unit'])
            assert archive[f't{t}_mu'][k]==pre['mu'] and archive[f't{t}_H'][k]==pre['H']
    return events,labels,summary['error'],summary['optimum']


def audit_basic(directory,summary):
    sig=summary['signature'];dim,budget,method=sig['dim'],sig['budget'],sig['method'];events=read(directory,budget)
    assert method in BASIC and sig['code_hash']==basic_hash() and all(events[0][k]==v for k,v in sig.items())
    assert sig['numpy']==importlib.metadata.version('numpy') and sig['scipy']==importlib.metadata.version('scipy')
    labels=[];points=[]
    for t,(pre,label) in enumerate(zip(events[1::2],events[2::2]),1):
        assert pre['t']==label['t']==t and pre['n_observed']==t-1 and pre['best_before']==(min(labels) if labels else None)
        u,x=np.asarray(pre['x_unit']),np.asarray(pre['x']);assert u.shape==x.shape==(dim,) and np.all((u>=0)&(u<=1))
        assert np.allclose(x,-5+10*u,rtol=0,atol=1e-13) and np.isfinite(label['y'])
        labels.append(label['y']);points.append(u);assert label['best_after']==min(labels)
    assert summary['algorithm_evaluations']==budget and summary['diagnostic_evaluations']==0 and summary['best']==min(labels)
    assert summary['exact_duplicate_calls']==budget-len(np.unique(np.asarray(points),axis=0))
    return events,labels,summary['error'],None


def audit_gp(directory,summary):
    sig=summary['signature'];dim,budget,method=sig['dim'],sig['budget'],sig['method'];events=read(directory,budget)
    assert method in GP and sig['code_hash']==gp_hash() and all(events[0][k]==v for k,v in sig.items())
    expected={'numpy':'2.2.6','scipy':'1.15.3','ioh':'0.3.22','torch':'2.5.1+cpu','gpytorch':'1.13','scikit-learn':'1.7.2'}
    assert sig['packages']==expected;labels=[];points=[]
    for t,(pre,label) in enumerate(zip(events[1::2],events[2::2]),1):
        assert pre['t']==label['t']==t and pre['n_observed']==t-1 and pre['best_before']==(min(labels) if labels else None)
        u,x=np.asarray(pre['x_unit']),np.asarray(pre['x']);assert u.shape==x.shape==(dim,) and np.all((u>=0)&(u<=1))
        assert np.allclose(x,-5+10*u,rtol=0,atol=1e-13) and len(pre['numpy_rng_hash'])==len(pre['torch_rng_hash'])==64
        state=pre['optimizer_state']
        if method=='gp_ei':
            if t<=2*dim:assert state['mode']=='initial_lhs' and state['index']==t-1
            else:assert state['mode'] in ['gp_ei','variance_fallback'] and state['training_count']==t-1 and state['continuous_starts']==8
        else:
            assert state['mode']=='turbo_author' and state['n_init']==2*dim and state['candidate_count']==min(100*dim,5000)
        labels.append(label['y']);points.append(u);assert label['best_after']==min(labels)
    assert summary['algorithm_evaluations']==budget and summary['diagnostic_evaluations']==0 and summary['best']==min(labels)
    assert summary['exact_duplicate_calls']==budget-len(np.unique(np.asarray(points),axis=0))
    return events,labels,summary['error'],None


def main():
    config=json.loads((ROOT/'configs/budget_performance_sensitivity.json').read_text('utf-8'));source=ROOT/config['out']
    status=json.loads((source/'status.json').read_text('utf-8'));assert status['stage']=='complete' and status['completed']==status['expected']==2700 and status['failed']==0
    assert json.loads((source/'failures.json').read_text('utf-8'))==[]
    frozen=json.loads((ROOT/config['freeze_manifest']).read_text('utf-8'));assert all(digest(ROOT/n)==v for n,v in frozen.items())
    assert json.loads((source/'manifest.json').read_text('utf-8'))['frozen_sources']==frozen
    expected=set(itertools.product(config['methods'],config['functions'],config['dimensions'],config['instances'],range(3),config['budget_multipliers']))
    records={};hashes={};seen=set()
    for method,fid,dim,instance,rep,multiplier in sorted(expected):
        budget=multiplier*dim;runid=f'{method}_f{fid:02}_d{dim}_i{instance}_r{rep}_b{budget}'
        directory=source/f'budget_{multiplier}D'/method/runid;summary=json.loads((directory/'summary.json').read_text('utf-8'))
        sig=summary['signature'];key=(method,fid,dim,instance,rep,multiplier);assert key not in seen;seen.add(key)
        assert all(sig[n]==v for n,v in dict(method=method,fid=fid,dim=dim,instance=instance,rep=rep,budget=budget).items())
        assert sig['seed']==100000*dim+1000*fid+10*instance+rep
        events,labels,error,optimum=(audit_internal(directory,summary) if method in INTERNAL else audit_basic(directory,summary) if method in BASIC else audit_gp(directory,summary))
        records[key]=dict(events=events,labels=labels,error=error,optimum=optimum,summary=summary)
        for name in ['summary.json','events.jsonl']+(['candidate_pools.npz'] if method in INTERNAL else []):
            path=directory/name;hashes[path.relative_to(ROOT).as_posix()]=digest(path)
    assert seen==expected and len(hashes)==7020
    prefix=[]
    for method,fid,dim,instance,rep in itertools.product(config['methods'],config['functions'],config['dimensions'],config['instances'],range(3)):
        groups=[records[(method,fid,dim,instance,rep,m)]['events'][1:] for m in [5,10,15]]
        equal=groups[0]==groups[1][:len(groups[0])] and groups[1]==groups[2][:len(groups[1])]
        if method in INTERNAL:assert equal
        prefix.append(dict(method=method,fid=fid,dim=dim,instance=instance,rep=rep,all_budget_prefixes_equal=equal))
    rows=[];curves=[]
    for key,record in records.items():
        method,fid,dim,instance,rep,multiplier=key;fixed=records[('fixed01',fid,dim,instance,rep,multiplier)]
        n0=2*dim+20;optimum=fixed['optimum'];denominator=max(min(fixed['labels'][:n0])-optimum,1e-12)
        endpoint=np.log10(max(record['error']/denominator,1e-12));rows.append(dict(method=method,fid=fid,dim=dim,instance=instance,
            rep=rep,budget_multiplier=multiplier,budget=multiplier*dim,log_relative_error=endpoint))
        best=np.minimum.accumulate(record['labels'])
        for fraction in np.linspace(0,1,101):
            n=max(1,int(np.ceil(fraction*len(best))));value=np.log10(max((best[n-1]-optimum)/denominator,1e-12))
            curves.append(dict(method=method,fid=fid,dim=dim,instance=instance,rep=rep,budget_multiplier=multiplier,
                budget_fraction=float(fraction),evaluation=n,log_relative_error=value))
    frame=pd.DataFrame(rows);out=ROOT/'results/budget_performance_sensitivity_analysis_v1';out.mkdir(parents=True,exist_ok=True)
    frame.to_csv(out/'runs.csv',index=False);pd.DataFrame(curves).to_csv(out/'convergence.csv',index=False);pd.DataFrame(prefix).to_csv(out/'prefix_checks.csv',index=False)
    instance=frame.groupby(['method','dim','budget_multiplier','fid','instance']).log_relative_error.median()
    functions=instance.groupby(['method','dim','budget_multiplier','fid']).mean();functions.to_csv(out/'function_scores.csv')
    functions.groupby(['method','dim','budget_multiplier']).mean().to_csv(out/'endpoint_scores.csv')
    audit=dict(runs=2700,algorithm_evaluations=int(frame.budget.sum()),diagnostic_evaluations=0,complete_design=True,
        raw_file_hashes=len(hashes),pre_information_verified=True,internal_bounds_and_management_replayed=True,
        internal_budget_prefix_invariant_runs=int(pd.DataFrame(prefix)[pd.DataFrame(prefix).method.isin(INTERNAL)].all_budget_prefixes_equal.sum()),
        external_prefix_equal_runs=int(pd.DataFrame(prefix)[~pd.DataFrame(prefix).method.isin(INTERNAL)].all_budget_prefixes_equal.sum()),
        statistical_tests_added=0,not_used_for_parameter_selection=True,source_hashes_verified=True)
    assert audit['algorithm_evaluations']==270000 and audit['internal_budget_prefix_invariant_runs']==540
    (out/'audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8');(out/'source_hashes.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
    print(json.dumps(audit,indent=2))


if __name__=='__main__':main()
