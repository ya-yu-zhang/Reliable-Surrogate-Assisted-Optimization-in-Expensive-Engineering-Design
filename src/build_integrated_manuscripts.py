"""Evidence-gated bilingual manuscripts; never accept partial scientific batches."""
import hashlib
import importlib.metadata
import json
from datetime import datetime,timezone,timedelta
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd

from .run_solo_cost import process_inventory

ROOT=Path(__file__).resolve().parents[1]
CORE=ROOT/'.venv312/Scripts/python.exe'


def require_complete(root=ROOT):
    processes={p['ProcessId'] for p in process_inventory()}
    for stem in ['reference_completion_v1','application_completion_v1']:
        status=json.loads((root/'results'/stem/'status.json').read_text('utf-8'))
        assert status['stage']=='complete' and status['failure'] is None and status['pid'] not in processes
    audit=json.loads((root/'results/solo_cost_analysis_v1/integrity_audit.json').read_text('utf-8'))
    assert audit['runs']==54 and audit['algorithm_evaluations']==12600 and audit['complete_design']
    audit=json.loads((root/'results/application_analysis_v1/audit.json').read_text('utf-8'))
    assert audit['runs']==480 and audit['algorithm_evaluations']==240000 and audit['complete_design']
    assert not any('-m '+module in (p['CommandLine'] or '') for p in process_inventory()
        for module in ['src.run_gp_batch','src.gp_references','src.run_solo_cost','src.solo_cost',
                       'src.run_application_batch','src.application_experiment'])
    expected={'numpy':'2.2.6','scipy':'1.15.3','pandas':'3.0.2','matplotlib':'3.10.3','tabulate':'0.9.0'}
    assert all(importlib.metadata.version(name)==version for name,version in expected.items())


def run(module,*args):
    result=subprocess.run([str(CORE),'-m',module,*args],cwd=ROOT,capture_output=True,
        text=True,encoding='utf-8',errors='replace')
    if result.returncode:raise RuntimeError(f'{module} failed before manuscript export: '+result.stderr[-2000:])


def verify_internal_sources():
    audit=ROOT/'results/mechanism_validation_analysis_v1/full_source_hashes.json'
    rows=json.loads(audit.read_text('utf-8'));assert len(rows)==3888
    for row in rows:
        directory=ROOT/'results/mechanism_validation_v1'/row['runid']
        for name,key in [('events.jsonl','journal'),('summary.json','summary'),('candidate_pools.npz','candidate_archive')]:
            assert hashlib.sha256((directory/name).read_bytes()).hexdigest()==row[key]
        if 'diagnostic_archive' in row:
            directory=ROOT/'results/mechanism_validation_diagnostics_v1'/row['runid']
            for name,key in [('hidden_labels.npz','diagnostic_archive'),('decisions_before_diagnostic_labels.jsonl','diagnostic_pre')]:
                assert hashlib.sha256((directory/name).read_bytes()).hexdigest()==row[key]


def table(frame):
    def format_value(value):
        if isinstance(value,(float,np.floating)):
            if not np.isfinite(value):return 'NA'
            if value and (abs(value)<.001 or abs(value)>=100000):return f'{value:.3e}'
            return f'{value:.4f}'
        return str(value)
    return frame.map(format_value).to_markdown(index=False)


def cost_plot(costs):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    out=ROOT/'results/integrated_paper_report_v1';out.mkdir(parents=True,exist_ok=True)
    colors=['#777777','#aaaaaa','#e6550d','#31a354','#756bb1','#bcbddc']
    methods=['greedy','fixed01','PEM_T','PEM_ST','gp_ei','turbo_1']
    points=np.r_[0,np.geomspace(.001,60,100)]
    fig,axes=plt.subplots(1,3,figsize=(11,3.2))
    for ax,dim in zip(axes,[10,20,40]):
        for method,color in zip(methods,colors):
            group=costs[(costs.dim==dim)&(costs.method==method)]
            modeled=np.median(group.nonobjective_seconds.to_numpy()[:,None]+group.algorithm_evaluations.to_numpy()[:,None]*points,axis=0)
            assert np.isfinite(modeled).all() and (modeled>0).all()
            ax.plot(points,modeled,label=method,color=color,lw=1.2)
        ax.set_xscale('symlog',linthresh=.01);ax.set_yscale('log')
        ax.set_title(f'D={dim}, B={10*dim}');ax.set_xlabel('Assumed objective cost c (seconds)')
        ax.set_ylabel('Modeled nonobjective time + Bc (seconds)');ax.grid(alpha=.2)
    axes[-1].legend(fontsize=6,ncol=2);fig.tight_layout()
    for suffix in ['png','pdf']:fig.savefig(out/('objective_cost_scenarios.'+suffix),dpi=240,bbox_inches='tight')
    plt.close(fig)


def additional_section(english,reference,costs,endpoints,effects,monitoring):
    if english:
        text='''# 9 Complete references, exclusive cost, and application transfer

## 9.1 Full descriptive BBOB reference evidence

Both frozen GP-EI and author TuRBO-1 batches complete 648 runs and 151,200 paid evaluations each, without reducing functions, repeats, GP training, or acquisition candidates. Together with the six internal and two basic references, all ten methods include 6,480 runs and 1,512,000 paid evaluations. External methods retain their own search and initialization. The matching internal initial-error denominator enters analysis only; normalization precedes within-instance medians. The 24 function scores are equally weighted. These descriptive comparisons add no significance family and do not reproduce the unavailable SAEA competitors.

GP-EI implements classical expected improvement [10] using the explicitly frozen kernel and search; it is not an exact reproduction of original EGO software. TuRBO-1 uses the author local trust-region implementation [11] with an external paid-call guard.

Table: Full ten-method function-mean log-relative endpoint scores. Lower is better.

'''
        text+=table(reference)+'\n\n![Complete BBOB background reference endpoints; no partial runs or resource-precheck instances.](../results/all_reference_report_v1/reference_endpoints.png)\n\n## 9.2 Exclusive cost evidence\n\n'
        text+='The frozen resource design contains 54 fresh, serial process measurements on f1/instance4 across D=10/20/40 and three repeats of six methods. Their 12,600 paid calls are reported as cost observations, excluded from benchmark effect estimation. Actual process and background-CPU guards precede measurements. Runtime includes journaling and each method retains its own initialization. Greedy/fixed controls still perform temporal monitoring, so these are implemented-system costs, not stripped-down ideal algorithm costs.\n\n'
    else:
        text='''# 9 完整参照、独占成本与应用迁移

## 9.1 完整BBOB描述性参照

冻结GP-EI及作者TuRBO-1各完成648运行/151,200次计费评价，保留全部函数、重复及原GP/候选搜索。与六内部及两基础参照合计十方法、6,480运行和1,512,000次算法评价。外部保留自身初始化与搜索；匹配内部初始误差分母仅在完成后的分析中读取，先按每运行归一化再取实例内重复中位数，24函数等权。不增加显著性家族，也不将这些参照冒充缺失的关键SAEA复现。

GP-EI采用经典期望改善思路[10]及明确冻结的核与搜索，不称原作者EGO软件精确复现。TuRBO-1使用作者局部信赖域实现[11]，由外部入口严格限制付费调用。

Table: 全部十方法函数级对数相对终点均值，越低越好。

'''
        text+=table(reference)+'\n\n![全部BBOB外部背景终点，排除部分运行与资源预检实例。](../results/all_reference_report_v1/reference_endpoints.png)\n\n## 9.2 独占成本\n\n'
        text+='冻结成本设计为f1/实例4上三个维度、六方法、三重复的54次独立串行进程测量，共12,600次付费评价，不进入基准效果统计。测量前检查实际进程与背景CPU负载；运行耗时含日志，各方法保留自身初始化。贪心/固定策略仍执行时间监测，因此是当前系统实现成本，不是去除所有监测后的理想成本。\n\n'
    names=['algorithm_seconds','nonobjective_seconds','peak_memory_gib','mean_post_initialization_preparation']
    for dim in [10,20,40]:
        subset=costs[costs.dim==dim].groupby('method')[names].median().reset_index()
        subset.columns=['Method','Algorithm s','Nonobjective s','Peak GiB','Post-init prep s']
        text+=f'Table: D={dim}; '+('three-run medians; full min/max and per-process observations remain in the supplement CSV.' if english else '三重复中位数，完整min/max与独立进程原值保留CSV。')+'\n\n'+table(subset)+'\n\n'
    text+=('![Hypothetical objective-cost scenarios from serial measurements; all methods use the same B in a dimension.](../results/integrated_paper_report_v1/objective_cost_scenarios.png)\n\nAt an assumed objective cost c, total time is modeled as measured nonobjective time plus Bc. This scenario is not an observed application acceleration. Equal evaluation budgets have equal objective-cost slopes and cannot establish evaluation savings.\n\n## 9.3 LassoBench mechanism transfer\n\n'
        if english else '![基于串行测量的假设评价成本情境，各维度所有方法预算相同。](../results/integrated_paper_report_v1/objective_cost_scenarios.png)\n\n假设单评价耗时c，时间模型为已测非目标开销加Bc，不是实测应用加速。同预算的评价成本斜率相同，不能从该图声称节省评价。\n\n## 9.3 LassoBench机制迁移\n\n')
    text+=('A separate protocol is frozen before formal seed42 labels. Three original tasks (D=60/100/180), eight methods, twenty optimization repeats, and 500 evaluations yield 480 runs and 240,000 full configuration evaluations (1,200,000 CV-fold solves). Internal initialization is 140/220/380 paid calls; external initialization remains native. The author five-fold full-fidelity objective, fixed data/splits, solver settings, bounds, and target definitions are unchanged.\n\nUnknown optimum is never imputed. The main endpoint is original validation loss. After all 500 labels are saved, the first lowest-validation configuration receives exactly one author test call, adding 480 single fits separately. Synthetic test MSPE uses the author fixed oracle normalizer, while DNA uses absolute test MSE; these scales are not pooled. The synthetic constructor computes its fixed test normalizer, but no test-performance result enters any optimization feedback.\n\n'
        if english else '另立协议在正式seed42标签前冻结。三个原任务60/100/180维、八方法、20优化重复、500评价共480运行/240,000完整配置评价（1,200,000个CV折求解）；内部启动140/220/380次全部计费，外部保持自身初始化。作者5折全保真目标、固定数据/分割、求解器、边界与目标定义均未修改。\n\n最优未知，直接报告原验证损失。完整500标签保存后，以最低验证值选配置，并列取首次，只调用一次作者test，480次额外单拟合另列。合成测试MSPE使用固定oracle归一化，DNA为绝对测试MSE，不跨尺度平均。合成构造器预计算固定测试归一化常数，但测试表现没有进入优化反馈。\n\n')
    for ds in ['synt_simple','synt_medium','DNA']:
        subset=endpoints[endpoints.dataset==ds][['method','median','q25','q75','test_mspe','test_fscore']].copy()
        subset.columns=['Method','CV median','Q1','Q3','Test MSPE median','F-score median']
        text+='Table: '+ds+'; '+('twenty optimization-run dispersion and post-completion test medians.' if english else '20优化运行离散程度与优化后测试中位数。')+'\n\n'+table(subset)+'\n\n'
    shown=effects[['dataset','median_raw_loss_difference','ci_low','ci_high','holm_p','losses','wins','ties']].copy()
    shown.columns=['Task','Median difference','CI low','CI high','Holm p','Loss','Win','Tie']
    text+=('Table: Prespecified application family, PEM-T minus fixed .1 raw final validation loss. Positive favors the fixed control. Intervals are unadjusted paired-run bootstrap.\n\n' if english else 'Table: 预定应用家族：PEM-T减固定.1原终点验证损失，正差表示反馈更差；区间为未经多重校正的配对运行重采样。\n\n')+table(shown)+'\n\n'
    descriptions=[]
    for row in effects.itertuples():
        direction=('higher' if row.median_raw_loss_difference>0 else 'lower' if row.median_raw_loss_difference<0 else 'equal') if english else ('更高' if row.median_raw_loss_difference>0 else '更低' if row.median_raw_loss_difference<0 else '相等')
        descriptions.append(f'{row.dataset}: {direction}, Holm p={row.holm_p:.3g}')
    text+=('; '.join(descriptions) if english else '；'.join(descriptions))+'.\n\n'
    text+=('The three comparisons form an application-only Holm family, separate from the nine BBOB mechanism tests. Twenty repeats describe optimization randomness on one fixed dataset and split per task, not twenty independent datasets. The Wilcoxon and paired bootstrap assumptions and limits are retained regardless of significance or direction.\n\n![Application original validation endpoints with run-IQR bars; unknown-optimum error is never constructed.](../results/application_report_v1/application_endpoints.png)\n\n![Application original-loss median and IQR curves. The dotted line marks internal initialization; external designs differ. Zero fraction displays the first paid label.](../results/application_report_v1/application_convergence.png)\n\n'
        if english else '三个应用比较独立进行Holm校正，不与BBOB九项机制检验混成一个家族。每任务20重复只对应同一固定数据及划分的优化随机性，不是20个独立数据集；无论方向与显著性，均保留signed-rank及配对bootstrap假设限制。\n\n![原验证目标终点及运行IQR，不构造未知最优误差。](../results/application_report_v1/application_endpoints.png)\n\n![原验证目标中位数/IQR曲线，虚线为内部启动结束，外部设计不同；0比例显示首次付费标签。](../results/application_report_v1/application_convergence.png)\n\n')
    shown=monitoring[['dataset','method','selected_failure','selected_quantile_loss','claims','false_claims','pooled_fdp','no_claim_runs']].copy()
    shown.columns=['Task','Method','Failure','Q-loss','Claims','False','Pooled FDP','No-claim runs']
    text+=('Table: Descriptive post-initialization selected-point monitoring; no hidden pool objectives are acquired.\n\n' if english else 'Table: 初始化后实际选择点监测，均为描述性；没有调用候选池隐藏目标。\n\n')+table(shown)+'\n\n'
    text+=('These closed-loop histories differ between methods and do not identify same-pool causal effects. Zero declarations give NA FDP, with counts disclosed. The 300-dimensional synt_high extension requires 620 internal initialization evaluations, so it cannot use the original 500 budget unchanged; its separate resource/budget protocol remains unfinished. Application findings cannot undo the failed original development gate.\n\n'
        if english else '各方法闭环历史不同，不能从这些指标识别同池因果效应。零声明FDP记NA且公开数量。300维synt_high启动需要620次，无法直接使用原500预算；独立扩展资源与预算仍未完成。应用结果不倒改原开发集失败门槛。\n\n')
    return text


def append_references(text,english):
    references='''[10] D. R. Jones, M. Schonlau, W. J. Welch. Efficient Global Optimization of Expensive Black-Box Functions. Journal of Global Optimization 13, 455–492, 1998. <https://doi.org/10.1023/A:1008306431147>.

[11] D. Eriksson, M. Pearce, J. Gardner, R. D. Turner, M. Poloczek. Scalable Global Optimization via Local Bayesian Optimization. Advances in Neural Information Processing Systems 32, 2019. <https://proceedings.neurips.cc/paper/2019/hash/6c990b7aca7bc7058f5e98ea909e924b-Abstract.html>.

[12] K. Šehić, A. Gramfort, J. Salmon, L. Nardi. LassoBench: A High-Dimensional Hyperparameter Optimization Benchmark Suite for Lasso. Proceedings of the First International Conference on Automated Machine Learning, PMLR 188:2/1–24, 2022. <https://proceedings.mlr.press/v188/sehic22a.html>.

'''
    marker='# Reproducibility and completion status' if english else '# 附录 可复现性与完成状态'
    assert marker in text
    return text.replace(marker,references+marker,1)


def main():
    require_complete(ROOT)
    verify_internal_sources()
    primary=ROOT/'results/mechanism_validation_analysis_v1/prespecified_comparisons.csv'
    original_primary_hash=hashlib.sha256(primary.read_bytes()).hexdigest()
    run('src.validate_mechanisms','--source','results/mechanism_validation_v1',
        '--diagnostics','results/mechanism_validation_diagnostics_v1','--out','results/mechanism_validation_analysis_v1')
    assert hashlib.sha256(primary.read_bytes()).hexdigest()==original_primary_hash, 'Original nine-test evidence changed'
    # Fresh immutable auditors rebuild all derived evidence before export.
    run('src.analyze_basic_references','--source','results/basic_references_v1','--out','results/basic_references_analysis_v1')
    for stem in ['gp_ei_reference','turbo_reference']:
        run('src.analyze_gp_references','--source',f'results/{stem}_v1','--out',f'results/{stem}_analysis_v1')
    run('src.analyze_solo_cost');run('src.report_all_references');run('src.report_application')
    reference=pd.read_csv(ROOT/'results/all_reference_report_v1/endpoint_summary.csv').set_index('dim').T.reset_index()
    reference=reference.rename(columns={'index':'Method',10:'D=10',20:'D=20',40:'D=40'})
    costs=pd.read_csv(ROOT/'results/solo_cost_analysis_v1/runs.csv')
    assert len(costs)==54 and costs.algorithm_evaluations.sum()==12600
    endpoints=pd.read_csv(ROOT/'results/application_report_v1/endpoint_iqr_and_test_medians.csv')
    effects=pd.read_csv(ROOT/'results/application_report_v1/predefined_comparisons.csv')
    monitoring=pd.read_csv(ROOT/'results/application_report_v1/monitoring_and_declarations.csv')
    cost_plot(costs)
    english=(ROOT/'paper/english_mechanism_manuscript.md').read_text('utf-8')
    chinese=(ROOT/'paper/论文机制研究稿.md').read_text('utf-8')
    assert '# 9 Discussion' in english and '# 10 Conclusion' in english
    assert '# 9 讨论' in chinese and '# 10 结论' in chinese
    english=english.replace('# 9 Discussion',additional_section(True,reference,costs,endpoints,effects,monitoring)+'# 10 Discussion',1)
    english=english.replace('# 10 Conclusion','# 11 Conclusion',1)
    english=english.replace('subtitle: Development and independent mechanism evidence — working manuscript',
        'subtitle: Development, independent mechanism, cost, and application evidence — working manuscript')
    english=english.replace('Complete competitive, resource, and application evidence remains unfinished.',
        'Complete GP/background references, exclusive costs, and three-task application evidence are reported separately. Reliable competitive SAEA reproduction and the predefined high-dimensional extension remain unfinished.')
    english=english.replace('Their complete outcomes are not included until all runs and audits finish.',
        'Their complete audited outcomes are now included in Section 9.')
    english=english.replace('complete GP-EI/TuRBO, competitive SAEA, exclusive resource, and application evidence remain unfinished.',
        'complete GP-EI/TuRBO, exclusive resource, and three-task application evidence are reported in Section 9; reliable competitive SAEA and the high-dimensional extension remain gaps.')
    english=english.replace('Complete competitive/application evidence is still required; this remains a working manuscript.',
        'GP/background, exclusive cost, and three-task application evidence are complete. Reliable SAEA comparisons and the predefined extension remain required; this remains a working manuscript.')
    english=english.replace('Competitive/application/resource evidence remains incomplete.',
        'Reliable competitive SAEA and the predefined high-dimensional extension remain incomplete. The failed development gate prevents claiming completion of the original optimization-improvement confirmation or CEC route. Source, LaTeX and PDF integration still require final visual verification.')
    chinese=chinese.replace('# 9 讨论',additional_section(False,reference,costs,endpoints,effects,monitoring)+'# 10 讨论',1)
    chinese=chinese.replace('# 10 结论','# 11 结论',1)
    chinese=chinese.replace('subtitle: 开发失败与独立机制验证；论文工作稿','subtitle: 开发失败、独立机制、成本与应用迁移；论文工作稿')
    chinese=chinese.replace('完整竞争、应用与独占资源证据尚待补齐。','完整GP/背景参照、独占成本与三主要应用已另行报告；可靠关键SAEA复现与预定300维扩展仍待补齐。')
    chinese=chinese.replace('正式GP-EI/TuRBO完整批次尚在执行，不以部分完成的结果作排名。','正式GP-EI/TuRBO全部批次与原始日志审计已完成，第9节仅使用完整结果作描述性展示。')
    chinese=chinese.replace('完整竞争、应用及独占成本证据仍需完成，本文为可审计工作稿，未宣称投稿就绪。','完整GP/背景参照、独占成本与三个主要应用的全部预定运行均已完成；可靠关键SAEA与预定扩展仍需完成，本文为可审计工作稿，未宣称投稿就绪。')
    chinese=chinese.replace('GP-EI/TuRBO完整参照、独占计时、关键竞争方法可获得性与应用证据仍未全部完成；','GP-EI/TuRBO完整参照、独占计时与三任务应用均有完整审计，关键竞争方法可靠复现与预定300维扩展仍未完成；')
    chinese=chinese.replace('在未完成独占计时及实际应用前，不能把评价次数相同或减少解释为墙钟加速。正式实验还需要评估峰值内存、候选生成与训练集截断开销。',
        '第9节补齐独占计时、峰值与三个主要应用，但同预算及假设评价成本仍不能解释为实测墙钟加速，模型/预算敏感性与预定扩展继续作为缺口。')
    english=english.replace('A separate protocol is frozen before formal seed42 labels.',
        'LassoBench [12] provides the application objectives. A separate protocol is frozen before formal seed42 labels.',1)
    chinese=chinese.replace('另立协议在正式seed42标签前冻结。','采用LassoBench[12]应用目标，另立协议在正式seed42标签前冻结。',1)
    english=append_references(english,True);chinese=append_references(chinese,False)
    application_directions='; '.join(f'{r.dataset}: median raw loss difference {r.median_raw_loss_difference:+.3g}, Holm p={r.holm_p:.3g}' for r in effects.itertuples())
    application_directions_zh='；'.join(f'{r.dataset}原损失差中位数{r.median_raw_loss_difference:+.3g}，Holm p={r.holm_p:.3g}' for r in effects.itertuples())
    english=english.replace('\nKeywords:','\nEight methods complete 480 application runs with 500 evaluations each on fixed data/splits; the application-only comparisons yield '+application_directions+'. Optimization randomness, independent testing, and cross-task scale differences are reported separately.\n\nKeywords:',1)
    chinese=chinese.replace('关键词：','八方法另完成三个主要应用480运行，每次500评价且固定数据/划分；应用独立家族结果为'+application_directions_zh+'。这些重复仅代表优化随机性，独立测试与跨任务尺度分别解释。\n\n关键词：',1)
    now=datetime.now(timezone.utc)+timedelta(hours=8)
    date=now.strftime('%d %B %Y')
    english=english.replace('date: 17 September 2026','date: '+date,1)
    chinese=chinese.replace('date: 2026年9月17日','date: '+now.strftime('%Y年%m月%d日'),1)
    paths=[ROOT/'paper/english_integrated_manuscript.md',ROOT/'paper/论文综合机制稿.md']
    for path,text in zip(paths,[english,chinese]):path.write_text(text,encoding='utf-8')
    inputs=[ROOT/'paper/english_mechanism_manuscript.md',ROOT/'paper/论文机制研究稿.md',Path(__file__),
        ROOT/'results/all_reference_report_v1/audit.json',ROOT/'results/all_reference_report_v1/endpoint_summary.csv',
        ROOT/'results/solo_cost_analysis_v1/integrity_audit.json',ROOT/'results/solo_cost_analysis_v1/runs.csv',
        ROOT/'results/application_analysis_v1/audit.json',ROOT/'results/application_report_v1/source_hashes.json',
        ROOT/'results/application_report_v1/endpoint_iqr_and_test_medians.csv',ROOT/'results/application_report_v1/predefined_comparisons.csv',
        ROOT/'results/application_report_v1/monitoring_and_declarations.csv']
    hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs+paths}
    (ROOT/'paper/integrated_manuscripts_source_hashes.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
    print('Bilingual integrated working manuscripts generated. Compile and inspect every PDF page before delivery.')


if __name__=='__main__':main()
