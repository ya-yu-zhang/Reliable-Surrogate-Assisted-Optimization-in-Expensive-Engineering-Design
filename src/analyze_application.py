"""Complete application journals, unknown-optimum endpoint and separate test audit."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from .core import Settings,METHODS,bounds,management

ROOT=Path(__file__).resolve().parents[1]


def main():
    config=json.loads((ROOT/'configs/application_formal.json').read_text('utf-8'))
    source=ROOT/config['out'];status=json.loads((source/'status.json').read_text('utf-8'))
    expected={(d,r,m) for d in config['datasets'] for r in range(config['repeats']) for m in config['methods']}
    assert status['stage']=='complete' and status['completed']==status['expected']==len(expected) and not status['failed']
    assert not json.loads((source/'failures.json').read_text('utf-8'))
    frozen=json.loads((ROOT/'docs/frozen_application_formal_v1/sha256.json').read_text('utf-8'))
    assert json.loads((source/'manifest.json').read_text('utf-8'))['frozen_sources']==frozen
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest for name,digest in frozen.items())
    runtime=json.loads((ROOT/config['runtime_manifest']).read_text('utf-8'))
    seen=set();rows=[];curves=[];hashes={};data_by_task={};cfg=Settings()
    for file in sorted(source.glob('*/summary.json')):
        summary=json.loads(file.read_text('utf-8'));sig=summary['signature']
        dataset,rep,method=sig['dataset'],sig['rep'],sig['method'];key=(dataset,rep,method)
        assert key in expected and key not in seen;seen.add(key)
        dim,budget=config['dimensions'][dataset],config['budgets'][dataset]
        assert sig['dim']==dim and sig['budget']==budget and sig['data_seed']==config['data_seed']
        assert sig['seed']==100000*dim+1000*config['dataset_ids'][dataset]+10*config['data_seed']+rep
        assert sig['frozen_sources']==frozen and summary['algorithm_evaluations']==budget
        assert sig['packages']==runtime['packages']
        assert summary['optimum_known'] is False and 'error' not in summary and 'optimum' not in summary
        assert summary['cv_fold_solves']==5*budget and summary['test_method_calls']==summary['post_completion_test_fits']==1
        events=[json.loads(v) for v in (file.parent/'events.jsonl').read_text('utf-8').splitlines()]
        assert len(events)==1+2*budget and events[0]['event']=='meta'
        assert all(events[0][k]==v for k,v in sig.items()) and events[0]['optimum_known'] is False
        assert events[0]['data_hashes']==summary['data_hashes'] and events[0]['fold_hash']==summary['fold_hash']
        dataset_identity=(summary['data_hashes'],summary['fold_hash'])
        if dataset in data_by_task:assert data_by_task[dataset]==dataset_identity
        else:data_by_task[dataset]=dataset_identity
        points=[];labels=[];residuals=[];monitors=[];stagnation=0;selected=[]
        for t,(pre,label) in enumerate(zip(events[1::2],events[2::2]),1):
            assert pre['event']=='pre' and label['event']=='label' and pre['t']==label['t']==t
            assert pre['n_observed']==t-1 and 'y' not in pre and 'test_metrics' not in pre
            assert pre['best_before']==(min(labels) if labels else None)
            u,x=np.asarray(pre['x_unit']),np.asarray(pre['x'])
            assert u.shape==x.shape==(dim,) and np.isfinite(x).all() and np.all((u>=0)&(u<=1))
            assert np.allclose(x,-1+2*u,rtol=0,atol=1e-13)
            y=label['y'];assert np.isfinite(y) and y>=0
            if method in METHODS and pre['mu'] is not None:
                assert pre['scale']>0 and max(pre['train_indices'])<t-1 and len(pre['train_indices'])<=256
                variant,manager,_,fixed=METHODS[method]
                bound=bounds(np.array([pre['mu']]),pre['scale'],u[None,:],residuals,t,variant,cfg)
                for field,column in [('H','H'),('margin','q'),('neff','neff')]:
                    assert np.isclose(pre[field],bound[column][0],rtol=1e-12,atol=1e-12)
                assert pre['calibrator']==bound['used'][0] and pre['support']==bool(bound['support'][0])
                state=management(monitors,stagnation,manager,fixed,cfg)
                assert all(pre[name]==value for name,value in state.items()) and pre['stagnation']==stagnation
                before=min(labels);declared=bool(state['monitoring_ready'] and bound['support'][0] and pre['H']<before-cfg.tau_factor*pre['scale'])
                assert pre['declared']==declared
                r=(y-pre['mu'])/pre['scale'];failure=y>pre['H']
                false=bool(declared and y>=before-cfg.tau_factor*pre['scale'])
                significant=y<before-cfg.tau_factor*pre['scale']
                assert label['residual']==r and label['upper_failure']==failure and label['false_claim']==false
                assert not false or failure
                assert label['significant_improvement']==significant
                residuals.append((t,u.copy(),r));monitors.append((float(failure),pre['margin']))
                stagnation=0 if significant else stagnation+1
                if t>2*dim+20:
                    delta=(y-pre['H'])/pre['scale']
                    selected.append(dict(failure=float(failure),margin=pre['margin'],
                        qloss=delta*(.9-float(delta<0)),declared=float(declared),false=float(false),
                        exploration=float(pre['mode']=='explore'),neff=pre['neff'],fallback=float(pre['calibrator']!=variant)))
            if method in ['gp_ei','turbo_1']:
                assert len(pre['numpy_rng_hash'])==len(pre['torch_rng_hash'])==64
                assert np.isfinite(pre['preparation_seconds']) and pre['preparation_seconds']>=0
            points.append(x);labels.append(y);assert label['best_after']==min(labels)
        index=int(np.argmin(labels));assert summary['best_evaluation']==index+1
        assert summary['best_validation_loss']==labels[index] and summary['best_config']==points[index].tolist()
        assert summary['exact_duplicate_calls']==budget-len(np.unique(np.array(points),axis=0))
        post=json.loads((file.parent/'post_completion_test.json').read_text('utf-8'))
        assert post['algorithm_evaluations']==budget and post['selected_evaluation']==index+1
        assert post['selected_config']==summary['best_config'] and post['best_validation_loss']==labels[index]
        assert post['metrics']==summary['test_metrics'] and post['test_method_calls']==1
        assert post['optimization_labels_sha256']==hashlib.sha256((file.parent/'events.jsonl').read_bytes()).hexdigest()
        assert all(np.isfinite(v) for v in post['metrics'].values())
        with np.load(file.parent/'candidate_pools.npz') as pools:
            if method in METHODS:
                checkpoints=summary['checkpoints'];assert set(pools.files)=={f't{t}_{v}' for t in checkpoints for v in ['points','mu','H']}
                for t in checkpoints:
                    pre=events[2*t-1];pool=pools[f't{t}_points'];k=pre['selection_index']
                    assert pool.shape==(256,dim) and np.isfinite(pool).all() and np.all((pool>=0)&(pool<=1))
                    np.testing.assert_array_equal(pool[k],pre['x_unit'])
                    assert pools[f't{t}_mu'][k]==pre['mu'] and pools[f't{t}_H'][k]==pre['H']
            else:assert not pools.files
        row=dict(dataset=dataset,dim=dim,rep=rep,method=method,budget=budget,
            best_validation_loss=summary['best_validation_loss'],best_evaluation=index+1,
            test_mspe=post['metrics']['mspe'],test_fscore=post['metrics'].get('fscore',np.nan),
            objective_seconds=summary['objective_seconds'],optimization_seconds=summary['optimization_seconds'],
            peak_memory_gib=summary['process_peak_working_set_bytes']/2**30,
            exact_duplicate_calls=summary['exact_duplicate_calls'])
        if selected:
            table=pd.DataFrame(selected);claims=int(table.declared.sum());false=int(table.false.sum())
            row.update(selected_evaluations=len(selected),claims=claims,false_claims=false,
                fdp=false/claims if claims else np.nan,**{'selected_'+c:table[c].mean() for c in table.columns})
        rows.append(row)
        best=np.minimum.accumulate(labels)
        for fraction in np.linspace(0,1,101):
            n=max(1,int(np.ceil(fraction*budget)));curves.append(dict(dataset=dataset,rep=rep,method=method,
                budget_fraction=float(fraction),evaluation=n,best_validation_loss=best[n-1]))
        for name in ['summary.json','events.jsonl','post_completion_test.json','candidate_pools.npz']:
            path=file.parent/name;hashes[path.relative_to(ROOT).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
    assert seen==expected
    frame=pd.DataFrame(rows);out=ROOT/'results/application_analysis_v1';out.mkdir(parents=True,exist_ok=True)
    frame.to_csv(out/'runs.csv',index=False);pd.DataFrame(curves).to_csv(out/'convergence.csv',index=False)
    frame.groupby(['dataset','method'])[['best_validation_loss','test_mspe','test_fscore']].agg(
        ['median',lambda s:s.quantile(.25),lambda s:s.quantile(.75)]).to_csv(out/'endpoint_iqr.csv')
    effects=[]
    for ds in config['datasets']:
        a=frame[(frame.dataset==ds)&(frame.method=='PEM_T')].set_index('rep').best_validation_loss
        b=frame[(frame.dataset==ds)&(frame.method=='fixed01')].set_index('rep').best_validation_loss
        delta=(a-b).sort_index().to_numpy();rng=np.random.default_rng(config['bootstrap_seed']+config['dataset_ids'][ds])
        estimates=np.median(delta[rng.integers(0,len(delta),(config['bootstrap_replicates'],len(delta)))],axis=1)
        effects.append(dict(dataset=ds,median_raw_loss_difference=float(np.median(delta)),
            ci_low=float(np.quantile(estimates,.025)),ci_high=float(np.quantile(estimates,.975)),
            p=float(wilcoxon(delta,zero_method='wilcox',alternative='two-sided',method='auto').pvalue) if np.any(delta) else 1.,
            losses=int(sum(delta>0)),wins=int(sum(delta<0)),ties=int(sum(delta==0))))
    order=np.argsort([r['p'] for r in effects]);running=0.
    for i,j in enumerate(order):running=max(running,min(1.,(len(effects)-i)*effects[j]['p']));effects[j]['holm_p']=running
    pd.DataFrame(effects).to_csv(out/'predefined_comparisons.csv',index=False)
    audit=dict(runs=len(rows),algorithm_evaluations=int(frame.budget.sum()),cv_fold_solves=int(frame.budget.sum()*5),
        post_completion_test_calls=len(rows),complete_design=True,pre_information_verified=True,
        bounds_and_management_replayed=True,unknown_optimum_not_imputed=True,test_results_not_in_optimizer=True,
        statistical_family_size=len(effects),conditional_fixed_data_analysis=True)
    (out/'audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    (out/'source_hashes.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
    print(json.dumps(audit,indent=2))


if __name__=='__main__':main()
