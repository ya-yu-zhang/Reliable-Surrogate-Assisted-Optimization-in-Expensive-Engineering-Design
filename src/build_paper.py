"""Populate a manuscript exclusively from completed, audited data."""
from pathlib import Path
import json
import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
AN=ROOT/'results/analysis_v1'


def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+
                     ['| '+' | '.join(map(str,r))+' |' for r in rows])


def main():
    score=pd.read_csv(AN/'endpoint_scores.csv');comparison=pd.read_csv(AN/'paired_comparisons.csv')
    functions=pd.read_csv(AN/'function_scores.csv');metrics=pd.read_csv(AN/'closed_loop_metrics.csv')
    calibration=pd.read_csv(AN/'calibration_aggregate.csv');single=pd.read_csv(AN/'single_step_aggregate.csv')
    raw=pd.read_csv(AN/'runs.csv');audit=json.loads((AN/'audit.json').read_text('utf-8'))
    counts=json.loads((ROOT/'results/diagnostics_v1/counts.json').read_text('utf-8'))
    assert audit['audited_runs']==1872 and counts['runs']==432
    assert comparison[comparison.comparator=='fixed01'].mean_log_delta.gt(0).all()
    # Add descriptive raw error/IQR, retaining all 9 runs in each function/dimension.
    raw.groupby(['dim','fid','method'],as_index=False).agg(n=('error','size'),median_error=('error','median'),
        q25=('error',lambda x:x.quantile(.25)),q75=('error',lambda x:x.quantile(.75))).to_csv(AN/'raw_endpoint_iqr.csv',index=False)
    main_methods=['greedy','fixed01','PEM_T','PEM_ST','error_only','stagnation_only']
    finaltable=table(['维度','均值贪心','固定10%','PEM-T','PEM-ST','仅失效率','仅停滞'],
        [[d]+[f'{score[(score.dim==d)&(score.method==m)].log_relative_error.iloc[0]:.4f}' for m in main_methods] for d in [10,20]])
    paired=table(['维度','对数差值','95%重采样区间','几何误差比','胜 负','Holm p'],
        [[r.dim,f'{r.mean_log_delta:.4f}',f'[{r.ci_low:.3f}, {r.ci_high:.3f}]',f'{r.error_ratio_geometric:.3f}',f'{r.wins}  {r.losses}',f'{r.p_holm:.5f}']
         for r in comparison[comparison.comparator=='fixed01'].itertuples()])
    fm=functions[functions.method.isin(['fixed01','PEM_T'])].pivot(index=['dim','fid'],columns='method',values='log_relative_error')
    functiontable=table(['维度','函数','固定10%','PEM-T','PEM-T 减 固定'],
        [[d,f'f{f}',f'{r.fixed01:.4f}',f'{r.PEM_T:.4f}',f'{r.PEM_T-r.fixed01:.4f}'] for (d,f),r in fm.iterrows()])
    rows=[]
    for d in [10,20]:
        for m in ['fixed01','PEM_T','PEM_ST','error_only','stagnation_only']:
            local=metrics[(metrics.dim==d)&(metrics.method==m)]
            n=int(local.claims.sum());false=int(local.false_claims.sum())
            rows.append([d,m,f'{local.explore_frequency.mean():.3f}',f'{local.upper_failure.mean():.3f}',n,false,f'{false/n:.3f}' if n else 'NA'])
    managementtable=table(['维度','配置','探索比例','失效率','声明数','错误数','合并FDP'],rows)
    rows=[]
    for d in [10,20]:
        for h in ['greedy','fixed03','pool_random']:
            local=calibration[(calibration.dim==d)&(calibration.history==h)&(calibration.calibrator=='T')].set_index('group')
            rows.append([d,h]+[f'{local.loc[g,"failure"]:.3f}' for g in ['pool','top10','actual_selected']])
    calibrationtable=table(['维度','历史策略','候选池失效','前10%失效','实际选中失效'],rows)
    rows=[]
    for d in [10,20]:
        for h in ['greedy','fixed03','pool_random']:
            local=single[(single.dim==d)&(single.history==h)&(single.calibrator=='T')].set_index('strategy')
            rows.append([d,h]+[f'{local.loc[g,"improvement"]:.4f}' for g in ['mean','fixed','feedback']])
    steptable=table(['维度','历史策略','均值改善','固定30%改善','完整反馈改善'],rows)
    rows=[]
    for d in [10,20]:
        for v in ['G','T','S','ST']:
            local=calibration[(calibration.dim==d)&(calibration.calibrator==v)&(calibration.group=='actual_selected')]
            rows.append([d,v]+[f'{local[col].mean():.4f}' for col in ['loss','margin','neff','fallback']])
    calibrators=table(['维度','校准器','归一化损失','上界余量','有效样本量','回退比例'],rows)
    rare=calibration[(calibration.calibrator=='T')&(calibration.group=='pool_declared')]
    raretable=table(['维度','历史策略','非空状态数','声明候选数','失效数','合并失效'],
        [[r.dim,r.history,f'{r.nonempty_states}/288',r.candidates,r.failures,f'{r.pooled_failure:.3f}' if r.candidates else 'NA'] for r in rare.itertuples()])
    # Primary plot excludes sparse declared subsets; their denominators are in the table.
    fig,ax=plt.subplots(1,2,figsize=(11,4),sharey=True)
    for j,d in enumerate([10,20]):
        local=calibration[(calibration.dim==d)&(calibration.calibrator=='T')&calibration.group.isin(['pool','top10','actual_selected'])]
        local.pivot(index='history',columns='group',values='failure').rename(columns={'pool':'Candidate pool','top10':'Top predicted 10%','actual_selected':'Actually selected'}).plot.bar(ax=ax[j],rot=0)
        ax[j].axhline(.1,color='black',ls='--',lw=1);ax[j].set(title=f'D={d}: T, 288 states per history',xlabel='Frozen history policy',ylabel='Mean state upper failure fraction',ylim=(0,.20))
        ax[j].legend(fontsize=8,loc='upper right')
    fig.tight_layout();fig.savefig(AN/'selection_failure.png',dpi=180);fig.savefig(AN/'selection_failure.pdf');plt.close(fig)
    text=(ROOT/'paper/论文正文模板.md').read_text('utf-8')
    abstract='在8个预定BBOB函数、10/20维及实例1–3上的开发实验中，我们执行1,872条闭环轨迹与432条共同历史，另取得442,368个隔离诊断标签。主原型相对开发集选出的固定10%探索策略，函数级几何终点误差比分别为1.919和1.517，两个维度均为0胜8负；Holm校正后的p值均为0.15625。这些结果不支持将该原型作为优化改进方法。等价性审计得到两组各144/144条相同轨迹；共同历史结果表明，误差差异方向依赖历史策略，空间局部化降低部分分位数损失也未转化为闭环优势。本文据此将研究结论限定为该原型的机制与失败分析，不给出覆盖保证或一般高维优势声明。'
    results=f'''## 7.1 实验完成与数据审计

13个闭环配置各144运行，共1,872运行，算法真实评价280,800次，无异常失败。共同历史3策略各144运行，共432运行、64,800次算法评价。诊断4状态/运行，共1,728状态及442,368次额外候选标签评价；标签独立保存且源日志哈希不变。两批合计执行2,304运行、345,600次算法评价。

共同历史中的均值贪心与fixed03分别重复了闭环中的144条轨迹，用于逐轮保存候选池；这些重复不增加优化统计样本量。两批共有2,016条不同方法配置/种子轨迹，优化统计只使用闭环集合。开发和机制运行均没有调用保留确认实例。

PEM-T与去除上界模式全部144条轨迹完全相同；fixed03与T加固定管理全部144条轨迹完全相同。这与第5.2节代数分析一致，不能将二者各自包装为有效选点消融。

## 7.2 闭环终点效果

表1给出函数等权的终点对数相对误差，越小越好。固定探索候选中10%最好；均值贪心在两个维度的总体指标也略优于固定10%。完整反馈及局部化版本未优于这些内部对照。

表1 开发集终点指标

{finaltable}

表2为PEM-T相对固定10%的配对函数级效果。误差比大于1表示PEM-T终点误差较大；这表示跨函数相对误差的几何汇总，不表示每一次运行都具有相同比例。两个维度分别0胜8负。重采样区间未包含0，但Holm检验未达0.05；两者口径不同，且全部为开发结果，不能选择性报告其中一种以宣称确认性显著结论。

表2 PEM-T相对固定10%的开发效果

{paired}

表3公开每个函数汇总，避免总分掩盖异质性。原始误差的中位数及IQR另保存于补充数据。

```{{=latex}}
\\begingroup\\small
```

表3 分函数终点指标

{functiontable}

```{{=latex}}
\\endgroup
```

![开发集收敛曲线。每轮对所有开发函数、实例与运行的归一化对数误差取中位数，聚合口径不同于表1的函数级实例汇总；曲线末端不能读成表1指标。图中没有确认实验。](../results/analysis_v1/convergence.png)

## 7.3 探索分配与稀疏改善声明

PEM-T的实际探索比例为10维36.6%、20维33.4%，均明显高于固定10%；上界失效率约为9.9%和9.5%，接近目标10%并未对应更好的最终解。单看失效率无法判断评价分配是否有效。

表4联合报告探索、失效、声明与错误数。PEM-T在10维总共只有3次声明，20维没有声明。因此不能将20维没有错误写成可靠改善或FDP控制；FDP应为NA。PEM-ST在20维有32次声明、2次错误，但其终点指标仍较差，声明表现没有证明优化改进。

表4 闭环决策指标 失效率为平均运行率 FDP为合并声明比例

{managementtable}

仅失效率反馈版本比完整反馈终点更好，但仍没有达到相对固定10%的总体优势。这提示宽度与停滞驱动的额外探索可能需要重新设计；现有消融同时移除两个反馈项，不能据此精确分配两项的独立因果贡献。

## 7.4 共同历史误差诊断

表5使用同历史、同模型、同候选池的T上界。fixed03历史下，实际选中点失效率高于候选池；贪心历史下则出现相反方向。因而支持“评价对象会改变误差表现”，不支持“筛选必然使覆盖恶化”这种单向陈述。每个维度/历史有288个冻结状态，实际选中组每状态1点，候选池每状态256点，前10%组每状态26点。

表5 T校准器在不同筛选对象上的失效率

{calibrationtable}

![共同历史下的单侧失效率。虚线为目标10%；每组状态相关，不将每个候选标签当作独立统计问题。](../results/analysis_v1/selection_failure.png)

表6只针对实际选中点，三种历史等权平均，显示局部化降低了部分归一化分位数损失与余量；这仍是给定共同历史下的估计表现。不能把表6的改进解释为闭环性能改进，也不能称达到名义覆盖。10维首次检查点因支持不足而回退，平均回退约25%；20维这些检查点不回退。

表6 实际选中点的校准器表现

{calibrators}

改善声明子集非常稀疏，表7同时列出非空状态与候选数。比例分母以声明候选数合并，不与图2的状态平均混淆。这些数据仅作机制诊断，不能估计稳定的声明成功概率。

表7 T上界的池内声明子集及样本支持

{raretable}

## 7.5 共同状态单步决策

表8为同一冻结候选池上所选点的归一化真实改善。T下经验上界策略与均值贪心完全等价，故不重复一列。完整反馈在全部6个维度/历史组合中，平均单步改善低于均值贪心，也低于预定fixed=.3参考规则；增加最大距离探索在这些共同状态中没有带来即时改善优势。

表8 共同状态下归一化单步改善

{steptable}

单步结果不排除探索可能改善未来模型，但闭环结果没有提供该后续收益的支持。当前不应将“高误差导致多探索”解释为已修复模型。

## 7.6 开销与路线门槛

原始并行负载下，PEM-T单运行总耗时中位数约0.78秒（10维）和1.82秒（20维）；PEM-ST约0.84秒和1.97秒。候选生成是当前实现主要开销。上述为开发运行的观测耗时，未作独占成本比较；解析目标本身极快，不作为应用加速证据。

原计划第十四节要求开发集显示相对选定固定探索基线的优化收益，再进入确认实验。主原型在两个维度均未满足这一必要条件。因此本阶段判定不通过优化改进路线门槛，保留全部失败结果与已冻结协议，转向机制分析；不扩大BBOB确认、CEC和应用运行去替代这一判断。'''
    discussion='''本原型的失败有两类不同证据。第一，上界改善选点在T/G下存在结构性冗余，这是不依赖基准表现的代数性质，144条轨迹审计为实现提供了对应证据。第二，完整反馈增加了探索，而开发闭环和共同状态单步收益没有支持这些额外探索的价值；这是该设计和预算下的经验结果，不能推广为所有误差反馈策略都无效。

实验支持监测对象需分别报告，但差异方向依赖历史。池内前10%与实际选中点不是同一分布：fixed03既可能按均值选点，也可能按最大距离选点。将这种差异统称为“贪心筛选偏差”，会掩盖探索模式本身的作用。

空间余量可以改变候选排序，并降低部分共同历史分位数损失，但闭环空间版本仍没有总体收益。有效样本量仅检查权重集中程度，不衡量代理模型是否适合候选区域；它不能单独解决历史模型尺度迁移或远离历史的误差分布变化。

本阶段最明确的发现是误差估计、声明与预算分配不可混作同一个成功指标。PEM-T接近10%的失效率，同时声明几乎不发生且优化较差，说明低失效率可能不足以形成有用的改善决策。继续研究应先提出改变候选排序或按实际评价收益估计探索价值的明确机制，使用新开发阶段验证，而非直接叠加更多权重或继续调整同一批数据上的阈值。'''
    conclusion='''我们实现并审计了选择后单侧误差监测与反馈探索原型，完成三类隔离实验。结果确认候选无关加法上界在当前规则下保持均值选点排序，并显示不同监测对象的误差差异依赖历史策略。主原型的反馈探索未在预定开发集上改善最终优化，因此本文不保留优化改进或高维优势声明。阶段证据可支持该原型的机制与失败分析；完整竞争方法比较、保留实例验证及应用研究仍需进一步完成，当前稿件不是投稿终稿。'''
    completion='''本阶段已完成原计划分析、核心公开文献对照、基础框架、预算和信息隔离检查、预定开发集内部比较、共同历史A/B诊断、统计汇总、失败案例与正文阶段稿。未完成项包括付费全文/可靠代码核查、外部基线、BBOB确认、CEC2017、LassoBench、预算敏感性、一般高维适用范围、独占时间与峰值内存测量，以及英文投稿稿。后续首先处理机制研究的文献差异与新验证协议，而非将本次开发失败隐藏后继续声称PEM-T优化改进。'''
    for key,value in dict(ABSTRACT_RESULTS=abstract,RESULTS=results,DISCUSSION=discussion,CONCLUSION=conclusion,COMPLETION=completion).items():
        text=text.replace('{{'+key+'}}',value)
    assert '{{' not in text
    # Native table captions stay with their longtable, including across pages.
    text=re.sub(r'^表[1-8] (.+)$',r'Table: \1',text,flags=re.MULTILINE)
    (ROOT/'paper/论文阶段稿.md').write_text(text,encoding='utf-8')
    short=f'''# 第一阶段实验报告

日期：2026-09-17。

原型不通过优化改进路线的开发门槛。这个结论来自原计划要求的开发集，不代表所有选择后误差反馈方法无效。

## 已完成实验

闭环1,872运行，算法评价280,800次；共同历史432运行，算法评价64,800次；额外诊断标签442,368个，保持与优化数据隔离。无异常失败。共同历史中288运行与闭环重复，不增加优化统计重复数。

## 核心结果

{paired}

固定概率由开发集从.1/.3/.5/.8选出.1。PEM-T在每维8函数汇总均较差，多重校正检验未显著；不得将开发选择后的比较当作确认性推断。

PEM-T与去除上界模式144/144轨迹等价；T_fixed(.3)与fixed03也144/144等价。原因是T/G在同一轮的上界修正不依赖候选位置。

PEM-T实际探索比例约36.6%/33.4%，失效率约9.9%/9.5%，但优化较差；10维只有3个改善声明、1个错误，20维没有声明，FDP为NA。

## 路线调整

按原计划第十四节，停止将当前原型包装成优化改进，阶段稿转为机制分析和失败报告。BBOB保留实例、CEC与应用实验尚未开展，待新的科学问题与验证协议确定后处理。全文/代码的竞争证据缺口仍需补齐。

完整方法、图表及讨论见 `paper/论文阶段稿.md`；原始汇总与所有统计口径见 `results/analysis_v1/`。'''
    (ROOT/'docs/第一阶段实验报告.md').write_text(short,encoding='utf-8')
    print('Manuscript and stage report generated from audited data.')


if __name__=='__main__':main()
