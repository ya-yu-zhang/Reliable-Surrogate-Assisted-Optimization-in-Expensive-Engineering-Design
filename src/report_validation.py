"""Report independently audited mechanism results, with no method selection."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .analyze import function_scores

ROOT=Path(__file__).resolve().parents[1]


def table(frame):
    f=frame.copy()
    for column in f:
        f[column]=f[column].map(lambda v:'NA' if pd.isna(v) else
                               (f'{v:.2e}' if 0<abs(v)<.0001 else f'{v:.4f}') if isinstance(v,float) else str(v))
    return '\n'.join(['| '+' | '.join(f.columns)+' |','| '+' | '.join(['---']*len(f.columns))+' |']+
                     ['| '+' | '.join(row)+' |' for row in f.itertuples(index=False,name=None)])


def save(fig,directory,name):
    fig.savefig(directory/(name+'.png'),dpi=240,bbox_inches='tight')
    fig.savefig(directory/(name+'.pdf'),bbox_inches='tight');plt.close(fig)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',default='results/mechanism_validation_analysis_v1')
    ap.add_argument('--out',default='results/mechanism_validation_report_v1');args=ap.parse_args()
    source,out=ROOT/args.source,ROOT/args.out;out.mkdir(parents=True,exist_ok=True)
    audit=json.loads((source/'audit.json').read_text('utf-8'))
    full=json.loads((source/'full_integrity_audit.json').read_text('utf-8'))
    assert full['runs']==3888 and full['complete_cartesian_design'] and full['frozen_sources_unchanged']
    assert audit['executed_runs']==3888 and audit['algorithm_evaluations']==907200
    assert audit['diagnostic_evaluations']==1990656 and audit['source_journals_unchanged']
    stats=pd.read_csv(source/'prespecified_comparisons.csv')
    assert len(stats)==9 and set(stats.functions)=={24}
    functions=pd.read_csv(source/'prespecified_function_contrasts.csv')
    calibration=pd.read_csv(source/'calibration_aggregate.csv')
    steps=pd.read_csv(source/'single_step_aggregate.csv')
    metrics=pd.read_csv(source/'closed_loop_metrics.csv')
    runs=pd.read_csv(source/'runs.csv')
    fig,axes=plt.subplots(1,3,figsize=(12,4),sharey=True)
    endpoint=functions[functions.comparison=='P2_endpoint_PEM_T_minus_fixed01']
    for ax,dim in zip(axes,[10,20,40]):
        group=endpoint[endpoint.dim==dim].sort_values('fid')
        ax.bar(group.fid,group.contrast,color=np.where(group.contrast<0,'#3182bd','#e6550d'))
        ax.axhline(0,color='black',lw=.8);ax.set_title(f'D={dim}; 24 functions')
        ax.set_xlabel('BBOB function');ax.set_xticks([1,5,10,15,20,24]);ax.grid(axis='y',alpha=.2)
    axes[0].set_ylabel('PEM-T minus fixed .1 (log-relative error)')
    fig.tight_layout();save(fig,out,'endpoint_function_effects')
    fig,axes=plt.subplots(1,3,figsize=(12,3.5),sharey=True)
    history=['greedy','fixed03','pool_random'];names=['Greedy','Fixed .3','Pool random']
    c=calibration[(calibration.calibrator=='T') & calibration.group.isin(['pool','actual_selected'])]
    cw=c.pivot(index=['dim','history'],columns='group',values='failure_rate')
    for ax,dim in zip(axes,[10,20,40]):
        group=cw.loc[dim].reindex(history)
        delta=group.actual_selected-group.pool
        ax.bar(names,delta,color='#756bb1');ax.axhline(0,color='black',lw=.8)
        ax.set_title(f'D={dim}');ax.tick_params(axis='x',rotation=20)
    axes[0].set_ylabel('Selected minus pool failure fraction')
    fig.tight_layout();save(fig,out,'history_object_differences')
    states=pd.read_csv(source/'calibration_states.csv')
    ess=states[(states.group=='actual_selected') & states.calibrator.isin(['T','ST'])].copy()
    checkpoint={}
    for runid,group in ess.groupby('runid'):
        checkpoint.update({(runid,t):j+1 for j,t in enumerate(sorted(group.t.unique()))})
    ess['checkpoint']=[checkpoint[(r,t)] for r,t in zip(ess.runid,ess.t)]
    fig,axes=plt.subplots(1,3,figsize=(12,3.4),sharey=True)
    for ax,dim in zip(axes,[10,20,40]):
        for calibrator,color in [('T','#3182bd'),('ST','#31a354')]:
            group=ess[(ess.dim==dim)&(ess.calibrator==calibrator)].groupby('checkpoint').agg(ESS=('neff','mean'),fallback=('fallback','mean'))
            ax.plot(group.index,group.ESS,marker='o',label=calibrator,color=color)
        ax.axhline(20,color='gray',ls='--',lw=1);ax.set_xticks([1,2,3,4]);ax.set_xlabel('Actual checkpoint order')
        ax.set_title(f'D={dim}');ax.grid(alpha=.2)
    axes[0].set_ylabel('State-mean effective sample size');axes[0].legend();fig.tight_layout();save(fig,out,'effective_support')
    ess.groupby(['dim','calibrator','checkpoint'])[['neff','fallback']].mean().to_csv(out/'support_by_checkpoint.csv')
    comparisons=stats[['dim','comparison','estimate','ci_low','ci_high','positive','negative','holm_p']].copy()
    comparisons['comparison']=comparisons['comparison'].map({
        'P1_history_interaction':'历史差异之差',
        'P2_endpoint_PEM_T_minus_fixed01':'终点误差差',
        'P2_step_feedback_minus_mean':'单步改善差'})
    assert comparisons['comparison'].notna().all()
    comparisons.columns=['维度','比较','估计','区间下限','区间上限','正方向函数','负方向函数','Holm p']
    selection=cw.reset_index()[['dim','history','pool','actual_selected']]
    selection.columns=['维度','历史','候选池失效','实际选中失效']
    declarations=metrics.groupby(['dim','method']).agg(claims=('claims','sum'),false=('false_claims','sum'),
                                                     exploration=('explore_frequency','mean'),failure=('upper_failure','mean')).reset_index()
    declarations['fdp']=declarations.false/declarations.claims.replace(0,np.nan)
    declarations.to_csv(out/'closed_loop_decision_summary.csv',index=False)
    # Only AFTER independent internal analysis: normalize reference endpoints by
    # the same common initial errors; take medians after run-level normalization.
    reference=ROOT/'results/basic_references_analysis_v1/runs.csv'
    if reference.exists():
        ref=pd.read_csv(reference)
        denominator=runs[runs.method=='fixed01'][['dim','fid','instance','rep','initial_error']]
        merged=ref.merge(denominator,on=['dim','fid','instance','rep'],validate='many_to_one')
        assert len(merged)==len(ref)==1296
        merged['log_relative_error']=np.log10(np.maximum(merged.error/merged.initial_error,1e-12))
        combined=pd.concat([runs,merged],ignore_index=True)
        combined.to_csv(out/'combined_internal_basic_reference_runs.csv',index=False)
        function_scores(combined).to_csv(out/'combined_internal_basic_reference_function_scores.csv',index=False)
    primary=stats[stats.comparison=='P2_endpoint_PEM_T_minus_fixed01'].copy()
    primary['几何误差比']=10**primary.estimate
    primary=primary[['dim','estimate','几何误差比','positive','negative','holm_p']]
    primary.columns=['维度','终点对数差','几何误差比','误差较大函数','误差较小函数','Holm p']
    text=f'''---
title: 独立机制验证实验报告
subtitle: 冻结协议结果；不与开发集混合
date: 2026年9月17日
---

# 1 范围与数据审计

全24个BBOB函数，10/20/40维，实例11–13，各3重复；六种内部配置共3,888运行、907,200算法评价。三种预定历史共1,944轨迹、7,776冻结状态，独立取得1,990,656额外标签。完整日志、共同初始化、评价前信息顺序和源指纹通过全量检查。原计划实例6–10未读取。本阶段不调参数、不删除函数、不并入开发集统计，也不倒置开发门槛的失败结论。

# 2 预定主要比较

估计正负需按指标解释：P1为fixed03的选中-池内失效差减greedy的对应差；闭环P2为PEM-T减固定.1的终点对数误差，负值更好；单步P2为反馈减均值的归一化真实改善，正值更好。24函数配对，9项统一Holm；分层重采样区间未作多重校正，不能替代校正检验。

Table: 9项预定比较完整结果

{table(comparisons)}

Table: 主原型闭环终点效果

{table(primary)}

![逐函数终点差。橙色表示PEM-T误差更大，蓝色表示误差更小；每维24函数均保留。](../results/mechanism_validation_report_v1/endpoint_function_effects.png)

# 3 历史与监测对象

Table: T上界的候选池与实际选中失效率

{table(selection)}

![不同历史的实际选中减候选池失效率。方向由结果决定，不预设筛选必然恶化。不同历史并非同池反事实，图中差异不解释为历史策略的独立因果效应。](../results/mechanism_validation_report_v1/history_object_differences.png)

# 4 样本支持与声明

![时间及局部时空上界的状态平均ESS。每轨迹四个实际检查点；首个检查点分别41/100、61/200、101/400。虚线20是工程支持阈值，不是覆盖保证。](../results/mechanism_validation_report_v1/effective_support.png)

检查点支持与回退完整表另存CSV。闭环声明汇总表联合保存声明总数、错误数、探索、失效及FDP；无声明FDP为NA。稀疏池内声明表另公开非空状态数、候选数及合并失败比例，不从零错误或低失败比例推出稳定声明成功概率。

# 5 解释边界与后续整合

本报告公开全部预定方向、区间与校正检验。需要根据这些实际结果逐项判断原经验命题是否外推，任何反向或接近零结果应进入正文讨论。排序等价性仍为固定规则的代数性质；经验失败不能扩展到所有校准或探索方法。共同状态即期收益不能证明长期因果机制。

与已完成Sobol/CMA-ES参照的共同归一化表仅在本阶段审计后生成；初始误差分母不向外部算法提供。该描述性展示不追加未经协议规定的显著性检验。GP-EI/TuRBO及关键SAEA、应用和独占资源证据仍需补齐。当前报告不等于投稿终稿，完整结果解读和中英文稿更新为下一步工作。
'''
    (ROOT/'paper/独立机制验证报告.md').write_text(text,encoding='utf-8')
    print('Validation tables, three figures, and source-separated report generated.')


if __name__=='__main__':main()
