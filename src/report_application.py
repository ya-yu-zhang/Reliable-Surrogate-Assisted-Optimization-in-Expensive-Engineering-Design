"""Full application report and standalone figures from audited complete data."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/application_report_v1'
LABELS={'greedy':'Greedy','fixed01':'Fixed .1','PEM_T':'PEM-T','PEM_ST':'PEM-ST',
        'sobol':'Sobol','cma_es':'CMA-ES','gp_ei':'GP-EI','turbo_1':'TuRBO'}


def load_complete(root=ROOT):
    config=json.loads((root/'configs/application_formal.json').read_text('utf-8'))
    source=root/config['out'];analysis=root/'results/application_analysis_v1'
    status=json.loads((source/'status.json').read_text('utf-8'))
    expected={(d,r,m) for d in config['datasets'] for r in range(config['repeats']) for m in config['methods']}
    assert status['stage']=='complete' and status['completed']==status['expected']==len(expected)==480 and not status['failed']
    audit=json.loads((analysis/'audit.json').read_text('utf-8'))
    assert audit['runs']==480 and audit['algorithm_evaluations']==240000 and audit['post_completion_test_calls']==480
    assert audit['bounds_and_management_replayed'] and audit['unknown_optimum_not_imputed'] and audit['statistical_family_size']==3
    hashes=json.loads((analysis/'source_hashes.json').read_text('utf-8'))
    assert len(hashes)==1920 and all(hashlib.sha256((root/name).read_bytes()).hexdigest()==digest for name,digest in hashes.items())
    frame=pd.read_csv(analysis/'runs.csv')
    assert len(frame)==480 and not frame.duplicated(['dataset','rep','method']).any()
    assert set(frame[['dataset','rep','method']].itertuples(index=False,name=None))==expected
    assert np.isfinite(frame.best_validation_loss).all() and (frame.best_validation_loss>=0).all()
    for row in frame.to_dict('records'):
        runid=f'{row["method"]}_{row["dataset"]}_r{row["rep"]:02}_b{row["budget"]}'
        summary=json.loads((source/runid/'summary.json').read_text('utf-8'))
        for field in ['best_validation_loss','objective_seconds','optimization_seconds']:
            assert np.isclose(row[field],summary[field],rtol=1e-12,atol=1e-12)
        assert np.isclose(row['test_mspe'],summary['test_metrics']['mspe'],rtol=1e-12,atol=1e-12)
    effects=pd.read_csv(analysis/'predefined_comparisons.csv')
    assert len(effects)==3 and set(effects.dataset)==set(config['datasets'])
    curves=pd.read_csv(analysis/'convergence.csv')
    assert len(curves)==480*101 and not curves.duplicated(['dataset','rep','method','budget_fraction']).any()
    # The figure data are checked against every charged raw prefix, not only shape.
    for (dataset,rep,method),group in curves.groupby(['dataset','rep','method']):
        budget=config['budgets'][dataset];runid=f'{method}_{dataset}_r{rep:02}_b{budget}'
        events=[json.loads(v) for v in (source/runid/'events.jsonl').read_text('utf-8').splitlines()]
        best=np.minimum.accumulate([v['y'] for v in events[2::2]])
        group=group.sort_values('budget_fraction');indices=np.maximum(1,np.ceil(np.linspace(0,1,101)*budget).astype(int))
        np.testing.assert_array_equal(group.evaluation,indices)
        np.testing.assert_allclose(group.best_validation_loss,best[indices-1],rtol=1e-12,atol=1e-12)
    return config,frame,effects,curves


def main():
    # Regenerate derived CSVs with the unchanged frozen auditor; no target calls.
    from .analyze_application import main as audit_complete_raw_journals
    audit_complete_raw_journals()
    config,frame,effects,curves=load_complete(ROOT)
    endpoint=frame.groupby(['dataset','method']).best_validation_loss.agg(
        median='median',q25=lambda s:s.quantile(.25),q75=lambda s:s.quantile(.75)).reset_index()
    test=frame.groupby(['dataset','method'])[['test_mspe','test_fscore']].median().reset_index()
    endpoint=endpoint.merge(test,on=['dataset','method'],validate='one_to_one')
    internal=frame[frame.method.isin(['greedy','fixed01','PEM_T','PEM_ST'])]
    summaries=[]
    for (dataset,method),group in internal.groupby(['dataset','method']):
        claims=int(group.claims.sum());false=int(group.false_claims.sum())
        summaries.append(dict(dataset=dataset,method=method,claims=claims,false_claims=false,
            pooled_fdp=false/claims if claims else np.nan,no_claim_runs=int(sum(group.claims==0)),
            selected_failure=group.selected_failure.mean(),selected_quantile_loss=group.selected_qloss.mean(),
            selected_margin=group.selected_margin.mean(),selected_neff=group.selected_neff.mean(),
            selected_fallback=group.selected_fallback.mean(),selected_exploration=group.selected_exploration.mean()))
    monitoring=pd.DataFrame(summaries)
    OUT.mkdir(parents=True,exist_ok=True)
    endpoint.to_csv(OUT/'endpoint_iqr_and_test_medians.csv',index=False)
    monitoring.to_csv(OUT/'monitoring_and_declarations.csv',index=False)
    effects.to_csv(OUT/'predefined_comparisons.csv',index=False)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    methods=config['methods'];colors=['#777777','#aaaaaa','#e6550d','#31a354','#3182bd','#6baed6','#756bb1','#bcbddc']
    fig,axes=plt.subplots(1,3,figsize=(12,3.8))
    conventions=[]
    for ax,dataset in zip(axes,config['datasets']):
        values=endpoint[endpoint.dataset==dataset].set_index('method').loc[methods]
        for k,(method,color) in enumerate(zip(methods,colors)):
            value=values.loc[method]
            ax.errorbar(k,value['median'],yerr=np.array([[value['median']-value.q25],[value.q75-value['median']]]),
                fmt='o',color=color,capsize=3,markersize=4)
        positive=bool((values.q25>0).all())
        if positive:ax.set_yscale('log')
        conventions.append(dict(dataset=dataset,endpoint_y_scale='log' if positive else 'linear'))
        ax.set_xticks(range(len(methods)),[LABELS[m] for m in methods],rotation=60,ha='right',fontsize=8)
        ax.set_title(f'{dataset}, D={config["dimensions"][dataset]}');ax.set_ylabel('Original validation loss; lower is better')
        ax.grid(axis='y',alpha=.2)
    fig.tight_layout()
    for suffix in ['png','pdf']:fig.savefig(OUT/('application_endpoints.'+suffix),dpi=240,bbox_inches='tight')
    plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(12,3.7))
    for ax,dataset in zip(axes,config['datasets']):
        for method,color in zip(methods,colors):
            group=curves[(curves.dataset==dataset)&(curves.method==method)].groupby('budget_fraction').best_validation_loss
            median=group.median();lower=group.quantile(.25);upper=group.quantile(.75)
            ax.plot(median.index,median,label=LABELS[method],color=color,lw=1.2)
            ax.fill_between(median.index,lower,upper,color=color,alpha=.06)
        ax.axvline((2*config['dimensions'][dataset]+20)/500,color='#999999',ls=':',lw=.8)
        ax.set_title(dataset);ax.set_xlabel('Fraction of charged 500 evaluations')
        ax.set_ylabel('Original validation loss');ax.grid(alpha=.2)
    axes[-1].legend(fontsize=6,ncol=2)
    fig.tight_layout()
    for suffix in ['png','pdf']:fig.savefig(OUT/('application_convergence.'+suffix),dpi=240,bbox_inches='tight')
    plt.close(fig)
    sources=[ROOT/'configs/application_formal.json',Path(__file__),ROOT/'results/application_analysis_v1/audit.json',
        ROOT/'results/application_analysis_v1/source_hashes.json',ROOT/'results/application_analysis_v1/runs.csv',
        ROOT/'results/application_analysis_v1/predefined_comparisons.csv',ROOT/'results/application_analysis_v1/convergence.csv']
    (OUT/'source_hashes.json').write_text(json.dumps({p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sources},indent=2),encoding='utf-8')
    (OUT/'audit.json').write_text(json.dumps(dict(runs=480,algorithm_evaluations=240000,
        complete_raw_prefixes_verified=True,unknown_optimum_not_imputed=True,axis_conventions=conventions,
        new_statistical_tests=0,conditional_fixed_data=True),indent=2),encoding='utf-8')
    text='# LassoBench正式机制迁移结果\n\n完整480运行与240,000次配置评价经原始日志审计。每任务固定同一数据/划分；20重复仅代表优化随机性。最终验证损失中位数及Q1/Q3为主终点，测试仅在优化完成后对最低验证配置调用一次。合成与DNA的测试MSPE尺度不同，分别解释，不跨任务平均。\n\n'
    text+=endpoint.to_markdown(index=False)+'\n\n三项预定PEM-T减fixed01最终原损失比较，正差表示反馈更差；配对bootstrap区间未经多重校正，Holm只作用于本三个应用比较。\n\n'
    text+=effects.to_markdown(index=False)+'\n\n内部实际选择点监测与声明如下，零声明FDP记NA，合并FDP不是运行FDP平均；未作池内目标诊断。\n\n'
    text+=monitoring.to_markdown(index=False)+'\n\n终点误差条为20重复IQR。终点纵轴仅在Q1均严格正时用log，以原始目标值作刻度；不构造真实最优误差。曲线为原始验证目标中位数与IQR，0预算比例对应第1次评价。虚线为内部2D+20启动结束，不假设外部同样初始化。高维扩展与关键SAEA基线缺口不被本表替代，共享运行耗时不称独占加速。\n'
    (ROOT/'docs/LassoBench正式机制迁移结果.md').write_text(text,encoding='utf-8')
    print('Complete application report and standalone figures written.')


if __name__=='__main__':main()
