"""Supplement built only from the completed development data."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from .diagnostics import load_events

ROOT=Path(__file__).resolve().parents[1]


def save(fig,name):
    out=ROOT/'results/supplement_v1';out.mkdir(exist_ok=True)
    fig.savefig(out/(name+'.png'),dpi=220,bbox_inches='tight')
    fig.savefig(out/(name+'.pdf'),bbox_inches='tight')
    plt.close(fig)


def table(frame):
    return '\n'.join(['| '+' | '.join(map(str,frame.columns))+' |',
                      '| '+' | '.join(['---']*len(frame.columns))+' |']+
                     ['| '+' | '.join(map(str,row))+' |' for row in frame.itertuples(index=False,name=None)])


def main():
    audit=json.loads((ROOT/'results/analysis_v1/audit.json').read_text('utf-8'))
    assert audit['audited_runs']==1872 and not audit['future_label_in_pre']
    metrics=pd.read_csv(ROOT/'results/analysis_v1/closed_loop_metrics.csv')
    methods=['fixed01','PEM_T','PEM_ST','error_only','stagnation_only']
    aggregate=metrics[metrics.method.isin(methods)].groupby(['dim','method'])[['claims','false_claims']].sum()
    fig,axes=plt.subplots(1,2,figsize=(10,3.4),sharey=True)
    for ax,d in zip(axes,[10,20]):
        frame=aggregate.loc[d].reindex(methods)
        successful=frame.claims-frame.false_claims
        ax.bar(np.arange(5),successful,label='True improvement',color='#4292c6')
        ax.bar(np.arange(5),frame.false_claims,bottom=successful,label='False claim',color='#ef6548')
        for j,row in enumerate(frame.itertuples()):
            ax.text(j,row.claims+.5,str(int(row.claims)),ha='center',fontsize=9)
        ax.set_xticks(np.arange(5),['Fixed .1','PEM-T','PEM-ST','Error only','Stagnation'],rotation=22,ha='right')
        ax.set_title(f'D={d}: 72 runs per method')
        ax.set_ylabel('Declared candidates (count)')
        ax.set_ylim(0,38)
    axes[0].legend(fontsize=8);fig.tight_layout();save(fig,'declarations')
    fig,ax=plt.subplots(figsize=(10,4.3));ax.set_xlim(0,10);ax.set_ylim(0,5);ax.axis('off')
    def box(x,y,w,label,color='#e8f0f7'):
        ax.add_patch(FancyBboxPatch((x,y),w,.8,boxstyle='round,pad=.1',facecolor=color,edgecolor='#45667c'))
        ax.text(x+w/2,y+.4,label,ha='center',va='center',fontsize=10)
    def arrow(x,y,a,b):ax.annotate('',xy=(a,b),xytext=(x,y),arrowprops=dict(arrowstyle='->',lw=1.4,color='#45667c'))
    box(.2,3.7,2.4,'Observed history\n(t - 1 labels)')
    box(3.6,3.7,2.7,'RBF + candidates\n+ original residuals')
    box(7.3,3.7,2.3,'Decision + PRE log\nflush before oracle')
    box(7.3,1.9,2.3,'One algorithm label\ncharged to budget', '#e8f5e9')
    box(3.6,1.9,2.7,'LABEL log + update\nhistory / monitoring','#e8f5e9')
    box(.2,.25,6.1,'Frozen checkpoint copy -> independent diagnostic oracle\nextra labels / analysis only', '#fff3dd')
    arrow(2.7,4.1,3.5,4.1);arrow(6.4,4.1,7.2,4.1);arrow(8.5,3.6,8.5,2.8)
    arrow(7.2,2.3,6.4,2.3);arrow(3.5,2.3,1.4,3.6)
    arrow(4.9,3.6,2.8,1.15)
    ax.text(6.7,.5,'No label path\nback to optimizer',fontsize=10,color='#b44730')
    save(fig,'information_flow')
    case={}
    fig,axes=plt.subplots(3,1,figsize=(9,6),sharex=True)
    for method,color in [('fixed01','#2374ab'),('PEM_T','#d1495b')]:
        directory=ROOT/'results/development_v1'/f'{method}_f20_d10_i1_r0_b100'
        summary=json.loads((directory/'summary.json').read_text('utf-8'))
        meta,pre,post=load_events(directory)
        t=np.arange(1,101)
        curve=np.log10(np.maximum(np.minimum.accumulate([b['y'] for b in post])-summary['optimum'],1e-12)/summary['initial_error'])
        axes[0].plot(t,curve,label=method,color=color)
        pairs=[(a,b) for a,b in zip(pre,post) if a['t']>40]
        tt=[a['t'] for a,b in pairs]
        pp=[a['p'] for a,b in pairs]
        axes[1].plot(tt,pp,color=color,label=method)
        explored=[a['t'] for a,b in pairs if a['mode']=='explore']
        axes[2].scatter(explored,[0 if method=='fixed01' else 1]*len(explored),color=color,marker='|',s=120)
        case[method]=dict(runid=directory.name,error=summary['error'],log_relative=summary['log_relative_error'],
                          exploration_count=len(explored),post_initialization_evaluations=60,
                          upper_failures=sum(b['upper_failure'] for a,b in pairs),
                          claims=sum(a['declared'] for a,b in pairs),false_claims=sum(b['false_claim'] for a,b in pairs))
    axes[0].set_ylabel('log10(error / initial error)');axes[0].legend()
    axes[1].set_ylabel('Exploration probability');axes[1].set_ylim(0,.85)
    axes[2].set_yticks([0,1],['Fixed .1','PEM-T']);axes[2].set_ylabel('Exploration calls');axes[2].set_xlabel('Charged evaluations')
    for ax in axes:ax.axvline(40,ls='--',lw=1,color='gray');ax.grid(alpha=.15)
    fig.tight_layout();save(fig,'canonical_case')
    (ROOT/'results/supplement_v1/case.json').write_text(json.dumps(case,indent=2),encoding='utf-8')
    case_table=pd.DataFrame([dict(方法=m,终点误差=f'{v["error"]:.6f}',探索次数=v['exploration_count'],
                                   上界失效次数=v['upper_failures'],声明数=v['claims'],错误数=v['false_claims']) for m,v in case.items()])
    settings=json.loads((ROOT/'results/development_v1/manifest.json').read_text('utf-8'))['settings']
    setting_table=pd.DataFrame([dict(参数=k,数值=v) for k,v in settings.items()])
    text=f'''---
title: 补充材料：选择后误差监测的开发实验与完整性审计
subtitle: 与论文阶段稿配套；独立验证结果尚未并入
date: 2026年9月17日
---

# S1 信息可见性与数据隔离

优化器只读取截至上一轮的已付费标签。每次评价前保存并刷新所选点预测、上界、已知最优、目标尺度、模式和随机状态；标签返回后才更新历史与监测。图1给出优化与诊断两条路径。诊断不向优化器提供反馈，候选池标签不作为免费训练数据。

![算法与诊断的信息路径。PRE日志先于真实标签保存，离线诊断读取冻结状态。虚构廉价标签或事后重新计算训练残差均不属于本实验。](../results/supplement_v1/information_flow.png)

## S1.1 一轮执行的明确顺序

1. 读取历史，按预定规则截断训练子集；拟合RBF并保存训练索引与标签尺度。
2. 生成256候选，预测均值；从原预测残差计算G/T/S/ST上界与支持回退。
3. 读取已完成监测窗口与停滞次数，计算探索概率；仅由当前可见信息选择一个点。
4. 保存候选检查点及所选点PRE记录，刷新文件；随后调用目标函数一次。
5. 写LABEL记录，以原预测及原尺度构成残差；更新监测、停滞、历史。
6. 达到预算即停止；已知最优值仅在结束后的统计中读取。

启动阶段前D+10次训练、后D+10次在线预测评价，全部付费；不将训练残差充作监测残差。内部方法共享初始化，后续独立轨迹即使整数种子相同也不拥有同一候选池。

# S2 冻结实现参数

Table: 开发v1参数（实现选择，不作为创新）

{table(setting_table)}

标签尺度使用当前所选训练子集的总体标准差，为零时置1。距离为归一化欧氏距离。分位数逆经验CDF不插值，负上侧分位数截为零。反馈窗口包括启动在线预测记录。并列按原索引，重复容差与越界反射规则固定；额外Sobol补齐不获取目标标签。

开发实验B=10D，D=10/20时预算100/200，完整初始化40/60。每轨迹检查点分别41/50/75/100和61/100/150/200；首个检查点经过初始化修正，不能称25%预算。诊断每状态256额外标签，所有校准器和策略复用同一组隐藏标签，不重复收集付费优化数据。

# S3 声明支持与错误数量

图2公开各方法声明总数和真假改善数量。声明不是概率保证，上界失效目标10%不意味着声明子集90%成功。零声明时FDP为NA，不能写成零错误率证明可靠。

![开发闭环中的改善声明计数。每维每方法72运行；柱高是声明数，颜色表示实际改善与错误声明。PEM-T在20维没有声明，图中零柱不是可靠性优势。](../results/supplement_v1/declarations.png)

只有原型的受监测声明使用当前原预测上界，数值阈值为当前尺度乘1e-6。所有假声明都经日志核查满足上界失效事件包含关系；该包含关系不控制FDP分母，也不保证每轮成功概率。

# S4 可追溯的单轨迹例子

事后展示f20、D=10、实例1、重复0。示例选择发生在开发结果汇总之后，未按单次最大差距挑选；它是描述性例子，不能估计典型性或替代正文8函数总体统计。两方法初始化与初始误差相同；最终PEM-T误差稍高，不能据一条轨迹判断机制普遍失效。

Table: 固定展示轨迹，后初始化阶段60次评价

{table(case_table)}

![f20、10维、实例1、重复0的真实轨迹。上：当前最优误差；中：评价前探索概率；下：实际空间探索评价。虚线为初始化结束；后续差异来自独立闭环，不能解释为同池选点差异。](../results/supplement_v1/canonical_case.png)

原始轨迹目录为`results/development_v1/PEM_T_f20_d10_i1_r0_b100`与对应fixed01目录。所展示数据保存于`results/supplement_v1/case.json`，图形由标签日志和PRE模式生成，没有平滑或删除评价。

# S5 完整性与阶段边界

开发1,872轨迹、280,800算法评价；共同历史432轨迹、64,800算法评价；其中288轨迹为保存完整候选池而重复执行，不增加统计样本。诊断1,728状态、442,368标签，与算法隔离。所有完成标记、预算计数、初始化配对及标签顺序已核查。两组144/144轨迹等价性支持当前实现的代数分析。

统计单位为函数，重复用于实例内中位数；正文采用8函数配对比较、20项Holm校正及配对分层重采样。开发集用于选定固定概率，不能将该比较写成独立确认。软件锁、硬件记录和原型指纹分别保存在docs下，异常环境安装记录保留。

本材料不包含正在运行的新机制验证标签。新阶段先冻结协议与统计脚本，采用全24函数、10/20/40维、实例11–13；结果应另行审计、单列，不与开发数据合并。原计划实例6–10仍未读取。外部竞争方法的完整性能复现、CEC和应用未完成。

作者代码预算审查的TuRBO控制流反例另存于`results/author_code_audit/`，不与BBOB优化结果混合。完整性检查不能替代算法有效性；开发门槛失败如实报告。
'''
    (ROOT/'paper/补充材料_开发阶段.md').write_text(text,encoding='utf-8')
    print('Development supplement and three source-derived figures written.')


if __name__=='__main__':main()
