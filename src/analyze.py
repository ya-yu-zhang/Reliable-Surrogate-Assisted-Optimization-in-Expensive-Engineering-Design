"""Function-level exploratory development statistics and source-data audit."""
import argparse
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .diagnostics import load_events


def holm(ps):
    order=np.argsort(ps); adjusted=np.zeros(len(ps)); previous=0.
    for j,k in enumerate(order):
        previous=max(previous,(len(ps)-j)*ps[k]);adjusted[k]=min(previous,1.)
    return adjusted


def function_scores(frame, value='log_relative_error'):
    instance=frame.groupby(['dim','fid','instance','method'],as_index=False)[value].median()
    return instance.groupby(['dim','fid','method'],as_index=False)[value].mean()


def hierarchical_ci(frame, comparator, dim, repeats=4000):
    df=frame[frame.dim==dim]
    wide=df.pivot(index=['fid','instance','rep'],columns='method',values='log_relative_error')
    rng=np.random.default_rng(81031+dim)
    functions=sorted(df.fid.unique()); estimates=[]
    arrays={f:{i:wide.loc[f].loc[i][['PEM_T',comparator]].to_numpy()
               for i in sorted(df[df.fid==f].instance.unique())} for f in functions}
    # Same resampled run/instance indices in both methods, then equal function weights.
    for _ in range(repeats):
        fs=rng.choice(functions,len(functions),replace=True);ff=[]
        for f in fs:
            inst=arrays[f];ii=rng.choice(list(inst),len(inst),replace=True);vv=[]
            for i in ii:
                rr=inst[i];mm=np.median(rr[rng.integers(len(rr),size=len(rr))],axis=0)
                vv.append(float(mm[0]-mm[1]))
            ff.append(np.mean(vv))
        estimates.append(np.mean(ff))
    return [float(v) for v in np.quantile(estimates,[.025,.975])]


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--out',required=True)
    ap.add_argument('--diagnostics');args=ap.parse_args()
    root=Path(args.source);out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((root/'manifest.json').read_text('utf-8'));cfg=manifest['config']
    summaries=[json.loads(f.read_text('utf-8')) for f in sorted(root.glob('*/summary.json'))]
    expected=len(cfg['functions'])*len(cfg['dimensions'])*len(cfg['instances'])*cfg['repeats']*len(cfg['methods'])
    if len(summaries)!=expected:raise RuntimeError(f'Incomplete experiment {len(summaries)}/{expected}.')
    records=[];trajectories={};rows=[];curves=[];ref_init={};audited=0
    for s in summaries:
        a=s['signature'];assert a['code_hash']==manifest['hash']
        records.append(dict(**{k:a[k] for k in ['fid','dim','instance','rep','method','budget']},
                            **{k:s[k] for k in ['error','initial_error','normalized_error','log_relative_error','auc_log_relative','elapsed']},
                            **{f'time_{k}':v for k,v in s['timers'].items()}))
        meta,pre,post=load_events(root/s['runid'])
        assert len(pre)==a['budget']==s['algorithm_evaluations']
        key=(a['fid'],a['dim'],a['instance'],a['rep'])
        startup=[(p['x_unit'],l['y'],p['mu']) for p,l in zip(pre,post)][:s['n0']]
        if key in ref_init:assert startup==ref_init[key]
        else:ref_init[key]=startup
        trajectories[(*key,a['method'])]=[p['x_unit'] for p in pre]
        declared=[];false=[];failure=[];margins=[];prob=[];modes=[];gains=[];fallback=[]
        for p,l in zip(pre,post):
            if l.get('false_claim'):assert l['upper_failure']
            if p['t']>s['n0']:
                declared.append(p['declared']);false.append(l['false_claim']);failure.append(l['upper_failure'])
                margins.append(p['margin']);prob.append(p['p']);modes.append(p['mode']);gains.append(l['improvement']/p['scale'])
                fallback.append(p['calibrator']!=p['variant'])
            curves.append(dict(fid=a['fid'],dim=a['dim'],instance=a['instance'],rep=a['rep'],method=a['method'],
                               t=p['t'],log_relative=float(np.log10(max((l['best_after']-s['optimum'])/s['initial_error'],1e-12)))))
        rows.append(dict(fid=a['fid'],dim=a['dim'],instance=a['instance'],rep=a['rep'],method=a['method'],
                         claims=sum(declared),false_claims=sum(false),fdp=sum(false)/sum(declared) if sum(declared) else np.nan,
                         claim_frequency=np.mean(declared),upper_failure=np.mean(failure),margin=np.mean(margins),
                         mean_probability=np.mean(prob),explore_frequency=np.mean(np.array(modes)=='explore'),
                         upper_mode_frequency=np.mean(np.array(modes)=='upper'),mean_improvement=np.mean(gains),fallback=np.mean(fallback)))
        audited+=1
    df=pd.DataFrame(records);metrics=pd.DataFrame(rows);curve=pd.DataFrame(curves)
    df.to_csv(out/'runs.csv',index=False);metrics.to_csv(out/'closed_loop_metrics.csv',index=False)
    scores=function_scores(df);scores.to_csv(out/'function_scores.csv',index=False)
    endpoints=scores.groupby(['dim','method'],as_index=False).log_relative_error.mean()
    endpoints.to_csv(out/'endpoint_scores.csv',index=False)
    fixed=scores[scores.method.str.startswith('fixed')].groupby('method').log_relative_error.mean().sort_values()
    fixedbest=str(fixed.index[0]);selection=dict(metric='equal-weight mean over dimension/function of instance mean of run medians of log10(E_B/E_init)',
                                               selected=fixedbest,probability=int(fixedbest[-2:])/10,scores={k:float(v) for k,v in fixed.items()},development_only=True)
    (out/'fixed_selection.json').write_text(json.dumps(selection,indent=2),encoding='utf-8')
    comparisons=[]
    controls=[m for m in cfg['methods'] if m!='PEM_T' and m not in {'T_fixed','no_upper'}]
    for dim in cfg['dimensions']:
        wide=scores[scores.dim==dim].pivot(index='fid',columns='method',values='log_relative_error')
        for control in controls:
            delta=wide.PEM_T-wide[control]
            ps=1. if np.allclose(delta,0,atol=1e-14) else float(wilcoxon(delta,alternative='two-sided',method='exact').pvalue)
            ci=hierarchical_ci(df,control,dim)
            comparisons.append(dict(dim=dim,comparator=control,mean_log_delta=float(delta.mean()),
                error_ratio_geometric=float(10**delta.mean()),wins=int((delta<-1e-12).sum()),ties=int((np.abs(delta)<=1e-12).sum()),
                losses=int((delta>1e-12).sum()),p_raw=ps,ci_low=ci[0],ci_high=ci[1]))
    comp=pd.DataFrame(comparisons)
    # One family contains BOTH dimensions and all listed primary/control comparisons.
    comp['p_holm']=holm(comp.p_raw.to_numpy());comp.to_csv(out/'paired_comparisons.csv',index=False)
    equivalence={}
    for left,right in [('PEM_T','no_upper'),('fixed03','T_fixed')]:
        keys=list(ref_init);equal=sum(trajectories[(*k,left)]==trajectories[(*k,right)] for k in keys)
        equivalence[f'{left} == {right}']=dict(identical_runs=equal,total=len(keys))
    (out/'audit.json').write_text(json.dumps(dict(audited_runs=audited,expected_runs=expected,init_groups=len(ref_init),
        budget_sum=int(df.budget.sum()),future_label_in_pre=False,equivalence=equivalence),indent=2),encoding='utf-8')
    style=['greedy',fixedbest,'PEM_T','PEM_ST','stagnation_only']
    fig,ax=plt.subplots(1,len(cfg['dimensions']),figsize=(11,4),squeeze=False)
    for j,dim in enumerate(cfg['dimensions']):
        for method in style:
            local=curve[(curve.dim==dim)&(curve.method==method)&(curve.t>=2*dim+20)]
            group=local.groupby('t').log_relative.median()
            ax[0,j].plot(group.index,group.values,label=method)
        ax[0,j].set(xlabel='Charged evaluations',ylabel='Median log10(error / initial error)',title=f'D={dim}: development only')
        ax[0,j].grid(alpha=.2)
    ax[0,-1].legend(fontsize=8);fig.tight_layout();fig.savefig(out/'convergence.png',dpi=180);fig.savefig(out/'convergence.pdf');plt.close(fig)
    fig,ax=plt.subplots(1,2,figsize=(11,4))
    gm=metrics.groupby(['dim','method'],as_index=False).mean(numeric_only=True)
    for dim in cfg['dimensions']:
        local=gm[gm.dim==dim]
        ax[0].scatter(local.explore_frequency,local.upper_failure,label=f'D={dim}')
        ax[1].scatter(local.claim_frequency,local.fdp,label=f'D={dim}')
        for _,r in local.iterrows():
            if r.method in style:
                ax[0].annotate(r.method,(r.explore_frequency,r.upper_failure),fontsize=7)
                if np.isfinite(r.fdp):ax[1].annotate(r.method,(r.claim_frequency,r.fdp),fontsize=7)
    ax[0].set(xlabel='Realized exploration fraction',ylabel='Mean run upper failure rate');ax[1].set(xlabel='Claim frequency',ylabel='Mean FDP among nonzero-claim runs')
    ax[0].legend();ax[1].legend();fig.tight_layout();fig.savefig(out/'decisions.png',dpi=180);plt.close(fig)
    selected=comp[comp.comparator==fixedbest]
    # Development continuation criterion: advantage in each dimension and pooled
    # over functions; this is a practical decision, not a confirmatory test.
    gate=bool((selected.mean_log_delta<0).all())
    gate_result=dict(pass_directional_gate=gate,fixedbest=fixedbest,
        criterion='PEM_T mean function-level log-relative endpoint better than selected fixed control in BOTH dimensions; mechanism and cost evidence additionally required',
        full_gate_passed=False,reason='Directional gate is necessary but not sufficient; mechanism and cost checks still required.' if gate else 'At least one dimension fails the necessary directional optimization benefit gate.',
        confirmation_unopened=True)
    (out/'gate.json').write_text(json.dumps(gate_result,indent=2),encoding='utf-8')
    print(json.dumps(dict(selection=selection,gate=gate_result,comparisons=selected.to_dict('records'),equivalence=equivalence),ensure_ascii=False,indent=2))
    if args.diagnostics:
        diag=Path(args.diagnostics)
        cr=pd.concat([pd.read_csv(p) for p in diag.glob('*/calibration.csv')],ignore_index=True)
        dr=pd.concat([pd.read_csv(p) for p in diag.glob('*/decisions.csv')],ignore_index=True)
        cr.to_csv(out/'diagnostic_calibration_raw.csv',index=False);dr.to_csv(out/'diagnostic_decisions_raw.csv',index=False)
        cg=cr.groupby(['dim','history','calibrator','group'],as_index=False).agg(states=('t','size'),nonempty_states=('n',lambda x:int((x>0).sum())),
            candidates=('n','sum'),failures=('failures','sum'),failure=('failure_rate','mean'),
            loss=('quantile_loss','mean'),margin=('margin','mean'),neff=('neff','mean'),fallback=('fallback','mean'))
        cg['pooled_failure']=cg.failures/cg.candidates.replace(0,np.nan)
        dg=dr.groupby(['dim','history','calibrator','strategy'],as_index=False).agg(states=('t','size'),improvement=('normalized_improvement','mean'),
            opportunity_loss=('opportunity_loss','mean'),claim_frequency=('declared','mean'),claims=('declared','sum'),false_claims=('false_claim','sum'),
            success=('improvement_success','mean'),no_candidate=('no_improving_candidate','mean'))
        dg['fdp']=dg.false_claims/dg.claims.replace(0,np.nan)
        cg.to_csv(out/'calibration_aggregate.csv',index=False);dg.to_csv(out/'single_step_aggregate.csv',index=False)
        fig,ax=plt.subplots(1,2,figsize=(11,4))
        for j,dim in enumerate(cfg['dimensions']):
            simple=cg[(cg.dim==dim)&(cg.calibrator=='T')&cg.group.isin(['pool','top10','actual_selected'])]
            piv=simple.pivot(index='history',columns='group',values='failure')
            piv.plot.bar(ax=ax[j],rot=0);ax[j].axhline(.1,color='black',ls='--',lw=1);ax[j].set(title=f'D={dim}: T on shared histories',ylabel='Upper bound failure fraction')
        fig.tight_layout();fig.savefig(out/'selection_failure.png',dpi=180);fig.savefig(out/'selection_failure.pdf');plt.close(fig)


if __name__=='__main__':main()
