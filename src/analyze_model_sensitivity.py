"""Full raw audit and descriptive summaries for the 450-run sensitivity design."""
from dataclasses import asdict
import hashlib,json,itertools
from pathlib import Path
import numpy as np
import pandas as pd
from .core import Settings,METHODS,bounds,management
from .experiment import code_hash

ROOT=Path(__file__).resolve().parents[1]


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_run(directory,summary,cfg):
    sig=summary['signature'];dim,budget=sig['dim'],sig['budget'];ntrain,n0=dim+10,2*dim+20
    assert sig['settings']==asdict(cfg) and sig['code_hash']==code_hash() and sig['method']=='PEM_T'
    events=[json.loads(v) for v in (directory/'events.jsonl').read_text('utf-8').splitlines()]
    assert len(events)==1+2*budget and events[0]['event']=='meta' and all(events[0][k]==v for k,v in sig.items())
    checkpoints=sorted(set(max(n0+1,int(np.ceil(budget*f))) for f in [.25,.5,.75,1]))
    assert events[0]['checkpoints']==checkpoints
    lb,ub=np.asarray(events[0]['lb']),np.asarray(events[0]['ub']);assert np.all(lb==-5) and np.all(ub==5)
    points=[];labels=[];residuals=[];monitors=[];stagnation=0;selected=[];capped=0
    variant,manager,_,fixed=METHODS['PEM_T']
    for t,(pre,label) in enumerate(zip(events[1::2],events[2::2]),1):
        assert pre['event']=='pre' and label['event']=='label' and pre['t']==label['t']==t
        assert pre['n_observed']==t-1 and pre['best_before']==(min(labels) if labels else None)
        u,x=np.asarray(pre['x_unit']),np.asarray(pre['x']);assert u.shape==x.shape==(dim,)
        assert np.isfinite(x).all() and np.all((u>=0)&(u<=1)) and np.allclose(x,lb+(ub-lb)*u,rtol=0,atol=1e-13)
        y=label['y'];assert np.isfinite(y)
        if t<=ntrain:
            assert pre['mode']=='initial_train' and pre['mu'] is None and not pre['declared']
        else:
            indices=pre['train_indices'];assert len(indices)==len(set(indices))==min(t-1,cfg.max_train)
            assert all(isinstance(j,int) and 0<=j<t-1 for j in indices);capped+=t-1>cfg.max_train
            assert pre['scale']>0 and pre['stagnation']==stagnation
            result=bounds(np.array([pre['mu']]),pre['scale'],u[None,:],residuals,t,variant,cfg)
            for field,column in [('H','H'),('margin','q'),('neff','neff')]:assert np.isclose(pre[field],result[column][0],rtol=1e-12,atol=1e-12)
            assert pre['calibrator']==result['used'][0] and pre['support']==bool(result['support'][0])
            state=management(monitors,stagnation,manager,fixed,cfg);assert all(pre[n]==v for n,v in state.items())
            before=min(labels);declared=bool(state['monitoring_ready'] and result['support'][0] and pre['H']<before-cfg.tau_factor*pre['scale'])
            assert pre['declared']==declared
            r=(y-pre['mu'])/pre['scale'];failure=y>pre['H'];false=bool(declared and y>=before-cfg.tau_factor*pre['scale'])
            significant=y<before-cfg.tau_factor*pre['scale']
            assert label['residual']==r and label['upper_failure']==failure and label['false_claim']==false
            assert label['significant_improvement']==significant and (not false or failure)
            residuals.append((t,u.copy(),r));monitors.append((float(failure),pre['margin']))
            stagnation=0 if significant else stagnation+1
            if t>n0:selected.append(dict(failure=float(failure),margin=pre['margin'],neff=pre['neff'],
                fallback=float(pre['calibrator']!='T'),exploration=float(pre['mode']=='explore'),declared=float(declared),false=float(false)))
        points.append(u);labels.append(y);assert label['best_after']==min(labels)
    assert summary['algorithm_evaluations']==budget and summary['diagnostic_evaluations']==0 and summary['n0']==n0
    assert summary['best']==min(labels) and summary['error']==max(min(labels)-summary['optimum'],0)
    initial=max(min(labels[:n0])-summary['optimum'],1e-12);assert summary['initial_error']==initial
    curve=np.maximum(np.minimum.accumulate(labels)[n0-1:]-summary['optimum'],1e-12)/initial
    assert summary['log_relative_error']==float(np.log10(max(summary['error']/initial,1e-12)))
    assert np.isclose(summary['auc_log_relative'],np.mean(np.log10(curve)))
    with np.load(directory/'candidate_pools.npz',allow_pickle=False) as archive:
        assert set(archive.files)=={f't{t}_{n}' for t in checkpoints for n in ['points','mu','H']}
        for t in checkpoints:
            pre=events[2*t-1];k=pre['selection_index'];pool=archive[f't{t}_points']
            assert pool.shape==(256,dim) and np.isfinite(pool).all() and len(np.unique(pool,axis=0))==256
            np.testing.assert_array_equal(pool[k],pre['x_unit']);assert archive[f't{t}_mu'][k]==pre['mu'] and archive[f't{t}_H'][k]==pre['H']
    metrics=dict(capped_fits=capped,selected_evaluations=len(selected))
    if selected:
        frame=pd.DataFrame(selected);claims=int(frame.declared.sum());false=int(frame.false.sum())
        metrics.update(upper_failure=frame.failure.mean(),margin=frame.margin.mean(),neff=frame.neff.mean(),
            fallback=frame.fallback.mean(),explore_frequency=frame.exploration.mean(),claims=claims,false_claims=false,
            fdp=false/claims if claims else np.nan)
    return events,metrics


def main():
    config=json.loads((ROOT/'configs/model_sensitivity.json').read_text('utf-8'));source=ROOT/config['out']
    status=json.loads((source/'status.json').read_text('utf-8'));assert status['stage']=='complete' and status['completed']==status['expected']==450 and status['failed']==0
    assert json.loads((source/'failures.json').read_text('utf-8'))==[]
    frozen=json.loads((ROOT/config['freeze_manifest']).read_text('utf-8'))
    assert all(digest(ROOT/n)==v for n,v in frozen.items())
    manifest=json.loads((source/'manifest.json').read_text('utf-8'));assert manifest['config']==config and manifest['frozen_sources']==frozen
    expected=set(itertools.product(config['variants'],config['functions'],config['dimensions'],config['instances'],range(3)))
    rows=[];metrics=[];hashes={};seen=set();initialization={};all_events={}
    for variant in config['variants']:
        values=config['variants'][variant];cfg=Settings(kernel_scale=values['kernel_scale'],max_train=values['max_train'])
        for file in sorted((source/variant).glob('*/summary.json')):
            summary=json.loads(file.read_text('utf-8'));sig=summary['signature'];key=(variant,sig['fid'],sig['dim'],sig['instance'],sig['rep'])
            assert key in expected and key not in seen;seen.add(key)
            assert sig['budget']==10*sig['dim'] and sig['seed']==100000*sig['dim']+1000*sig['fid']+10*sig['instance']+sig['rep']
            events,m=audit_run(file.parent,summary,cfg);all_events[key]=events
            init=events[1:1+2*summary['n0']];problem=key[1:]
            normalized=[dict(v,**({'settings':None} if v.get('event')=='meta' else {})) for v in init]
            if problem in initialization:assert initialization[problem][1:]==normalized[1:]
            else:initialization[problem]=normalized
            rows.append(dict(variant=variant,fid=sig['fid'],dim=sig['dim'],instance=sig['instance'],rep=sig['rep'],
                log_relative_error=summary['log_relative_error'],normalized_error=summary['normalized_error'],auc_log_relative=summary['auc_log_relative']))
            metrics.append(dict(variant=variant,fid=sig['fid'],dim=sig['dim'],instance=sig['instance'],rep=sig['rep'],**m))
            for name in ['summary.json','events.jsonl','candidate_pools.npz']:
                path=file.parent/name;hashes[path.relative_to(ROOT).as_posix()]=digest(path)
    assert seen==expected and len(hashes)==1350
    invariant=0
    for f,d,i,r in itertools.product(config['functions'],[20],config['instances'],range(3)):
        a=all_events[('base',f,d,i,r)][1:];b=all_events[('cap512',f,d,i,r)][1:];assert a==b;invariant+=1
        da=source/'base'/f'PEM_T_f{f:02}_d{d}_i{i}_r{r}_b{10*d}'/'candidate_pools.npz'
        db=source/'cap512'/f'PEM_T_f{f:02}_d{d}_i{i}_r{r}_b{10*d}'/'candidate_pools.npz'
        with np.load(da) as aa,np.load(db) as bb:
            assert aa.files==bb.files and all(np.array_equal(aa[n],bb[n]) for n in aa.files)
    frame=pd.DataFrame(rows);metric=pd.DataFrame(metrics);out=ROOT/'results/model_sensitivity_analysis_v1';out.mkdir(parents=True,exist_ok=True)
    frame.to_csv(out/'runs.csv',index=False);metric.to_csv(out/'mechanism_metrics.csv',index=False)
    frame.groupby(['dim','variant'])[['log_relative_error','auc_log_relative']].agg(['median',lambda s:s.quantile(.25),lambda s:s.quantile(.75)]).to_csv(out/'endpoint_iqr.csv')
    base=frame[frame.variant=='base'].set_index(['fid','dim','instance','rep']).log_relative_error
    effects=[]
    for dim in config['dimensions']:
        for variant in [v for v in config['variants'] if v!='base']:
            value=frame[(frame.variant==variant)&(frame.dim==dim)].set_index(['fid','dim','instance','rep']).log_relative_error-base[base.index.get_level_values('dim')==dim]
            delta=value.to_numpy();effects.append(dict(dim=dim,variant=variant,median_difference=float(np.median(delta)),
                q1=float(np.quantile(delta,.25)),q3=float(np.quantile(delta,.75)),positive=int(sum(delta>0)),negative=int(sum(delta<0)),zero=int(sum(delta==0))))
    pd.DataFrame(effects).to_csv(out/'descriptive_paired_differences.csv',index=False)
    audit=dict(runs=450,algorithm_evaluations=135000,diagnostic_evaluations=0,complete_design=True,
        pre_information_verified=True,bounds_and_management_replayed=True,candidate_selection_archives_verified=True,
        raw_file_hashes=1350,twenty_dim_base_cap512_invariant_runs=invariant,statistical_tests_added=0,
        not_used_for_parameter_selection=True,source_hashes_verified=True)
    (out/'audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8');(out/'source_hashes.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
    print(json.dumps(audit,indent=2))


if __name__=='__main__':main()
