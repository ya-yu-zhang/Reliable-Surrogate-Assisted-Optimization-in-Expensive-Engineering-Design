"""Descriptive reference integration, only after both complete GP audits."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INTERNAL = ROOT/'results/mechanism_validation_analysis_v1'
OUT = ROOT/'results/all_reference_report_v1'
METHODS = ['greedy','fixed01','fixed03','pool_random','PEM_T','PEM_ST',
           'sobol','cma_es','gp_ei','turbo_1']


def combine_runs(internal,external):
    internal=internal.copy();external=external.copy()
    keys=['dim','fid','instance','rep']
    expected_internal_budget=10*internal.dim
    if 'algorithm_evaluations' in internal:
        assert (internal.algorithm_evaluations==expected_internal_budget).all()
    internal['algorithm_evaluations']=expected_internal_budget
    assert len(internal)==3888 and internal.algorithm_evaluations.sum()==907200
    assert len(external)==2592 and (external.algorithm_evaluations==10*external.dim).all()
    denominator=internal[internal.method=='fixed01'][keys+['initial_error']]
    assert len(denominator)==648 and not denominator.duplicated(keys).any()
    normalized=external.merge(denominator,on=keys,validate='many_to_one')
    assert len(normalized)==2592 and np.isfinite(normalized.initial_error).all() and (normalized.initial_error>0).all()
    normalized['log_relative_error']=np.log10(np.maximum(normalized.error/normalized.initial_error,1e-12))
    combined=pd.concat([internal,normalized],ignore_index=True)
    assert len(combined)==6480 and not combined.duplicated(keys+['method']).any()
    assert set(combined.method)==set(METHODS)
    assert (combined.groupby('method').size()==648).all()
    assert combined.algorithm_evaluations.sum()==1512000
    return combined


def main():
    audit = json.loads((INTERNAL/'full_integrity_audit.json').read_text('utf-8'))
    assert audit['runs'] == 3888 and audit['complete_cartesian_design']
    internal = pd.read_csv(INTERNAL/'runs.csv')
    parts = []; fingerprints = {}
    for stem in ['basic_references','gp_ei_reference','turbo_reference']:
        directory = ROOT/'results'/f'{stem}_analysis_v1'
        audit_file = directory/'audit.json'
        verified = json.loads(audit_file.read_text('utf-8'))
        expected = 1296 if stem == 'basic_references' else 648
        assert verified.get('audited_runs',verified.get('runs')) == expected
        assert verified['algorithm_evaluations'] == (302400 if stem == 'basic_references' else 151200)
        file = directory/'runs.csv'; frame = pd.read_csv(file)
        assert len(frame) == expected
        parts.append(frame)
        for path in [audit_file,file]:
            fingerprints[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    external = pd.concat(parts,ignore_index=True)
    combined=combine_runs(internal,external)
    instances = combined.groupby(['dim','fid','instance','method']).log_relative_error.median()
    functions = instances.groupby(['dim','fid','method']).mean().reset_index()
    expected_internal = pd.read_csv(INTERNAL/'function_scores.csv').sort_values(['dim','fid','method'])
    actual_internal = functions[functions.method.isin(internal.method)].sort_values(['dim','fid','method'])
    assert np.allclose(actual_internal.log_relative_error,expected_internal.log_relative_error,rtol=0,atol=1e-12)
    assert len(functions) == 720
    summary = functions.groupby(['dim','method']).log_relative_error.mean().unstack('method')[METHODS]
    wide = functions.pivot(index=['dim','fid'],columns='method',values='log_relative_error')[METHODS]
    ranks = wide.rank(axis=1,method='average').groupby('dim').mean()
    dispersion = combined.groupby(['dim','fid','method']).error.agg(
        median='median',q25=lambda s:s.quantile(.25),q75=lambda s:s.quantile(.75))
    OUT.mkdir(parents=True,exist_ok=True)
    combined.to_csv(OUT/'common_scale_runs.csv',index=False)
    functions.to_csv(OUT/'common_scale_function_scores.csv',index=False)
    summary.to_csv(OUT/'endpoint_summary.csv'); ranks.to_csv(OUT/'descriptive_mean_ranks.csv')
    dispersion.to_csv(OUT/'raw_error_iqr.csv')
    for path in [INTERNAL/'runs.csv',INTERNAL/'function_scores.csv',INTERNAL/'full_integrity_audit.json',Path(__file__)]:
        fingerprints[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    (OUT/'source_hashes.json').write_text(json.dumps(fingerprints,indent=2),encoding='utf-8')
    report = dict(runs=6480,external_runs=2592,internal_runs=3888,
        algorithm_evaluations=int(combined.algorithm_evaluations.sum()),functions=24,dimensions=[10,20,40],
        normalize_before_within_instance_median=True,denominator_exposed_only_to_analysis=True,
        descriptive_only=True,new_significance_tests=0,all_ten_methods_retained=True)
    assert report['algorithm_evaluations'] == 1512000
    (OUT/'audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes = plt.subplots(1,3,figsize=(13.6,4.2),sharey=True)
    names = {'greedy':'Greedy','fixed01':'Fixed .1','fixed03':'Fixed .3','pool_random':'Random pool',
        'PEM_T':'PEM-T','PEM_ST':'PEM-ST','sobol':'Sobol','cma_es':'CMA-ES','gp_ei':'GP-EI','turbo_1':'TuRBO'}
    for ax,dim in zip(axes,[10,20,40]):
        scores = summary.loc[dim]
        ax.bar(range(10),scores.values,color=['#999999']*4+['#e6550d','#31a354']+['#3182bd']*4)
        ax.set_xticks(range(10),[names[m] for m in METHODS],rotation=65,ha='right',fontsize=7)
        ax.set_title(f'D={dim}'); ax.grid(axis='y',alpha=.2)
    axes[0].set_ylabel('Function-mean log-relative\\nendpoint (lower is better)',labelpad=10,fontsize=9)
    fig.subplots_adjust(left=.14,right=.995,bottom=.30,top=.88,wspace=.08)\n    fig.savefig(OUT/'reference_endpoints.png',dpi=240,bbox_inches='tight',pad_inches=.08)
    fig.savefig(OUT/'reference_endpoints.pdf',bbox_inches='tight',pad_inches=.08); plt.close(fig)
    text = '# 全部外部参照描述性整合\n\n全部内部与四项基础/GP参照共6,480运行，1,512,000次计费算法评价。每次外部运行先用匹配内部初始化误差归一化，再按重复中位数、实例平均及函数等权汇总。已知最优只用于完成后的统计。\n\n'
    text += summary.round(5).to_markdown()+'\n\n平均排名是描述性辅助结果，未增加显著性家族。GP-EI是本文经典实现，TuRBO保留作者搜索机制；外部初始化与内部不同。相同预算不能解释为共同历史因果对照，四项参照也不替代Temporal CP-SAEA、SADE-SS或BGP-SAEA可靠复现。共享负载时间不能作为独占成本。\n'
    (ROOT/'docs/全部外部参照整合报告.md').write_text(text,encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
