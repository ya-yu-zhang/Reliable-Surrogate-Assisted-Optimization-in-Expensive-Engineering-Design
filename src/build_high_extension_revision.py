"""Append complete high-extension evidence to the already integrated bilingual working papers."""
import hashlib,json
from pathlib import Path
from datetime import datetime,timedelta,timezone
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/application_high_report_v1'
ORDER=['greedy','fixed01','PEM_T','PEM_ST','sobol','cma_es','gp_ei','turbo_1']


def require_complete(root=ROOT):
    audit=json.loads((root/'results/application_high_analysis_v1/audit.json').read_text('utf-8'))
    assert audit['complete_design'] and audit['runs']==160 and audit['algorithm_evaluations']==160000
    assert audit['cv_fold_solves']==800000 and audit['post_completion_test_calls']==160
    assert audit['statistical_tests_added']==0 and audit['not_added_to_primary_three_test_family']
    hashes=json.loads((root/'results/application_high_analysis_v1/source_hashes.json').read_text('utf-8'))
    assert len(hashes)==640 and all(hashlib.sha256((root/n).read_bytes()).hexdigest()==v for n,v in hashes.items())
    return audit,hashes


def fmt(value):return f'{value:.4g}'


def table(frame,english):
    rows=[]
    for method in ORDER:
        g=frame[frame.method==method]
        rows.append(dict(Method=method,Validation=f'{fmt(g.best_validation_loss.median())} [{fmt(g.best_validation_loss.quantile(.25))}, {fmt(g.best_validation_loss.quantile(.75))}]',
                         MSPE=f'{fmt(g.test_mspe.median())} [{fmt(g.test_mspe.quantile(.25))}, {fmt(g.test_mspe.quantile(.75))}]',
                         F_score=f'{fmt(g.test_fscore.median())} [{fmt(g.test_fscore.quantile(.25))}, {fmt(g.test_fscore.quantile(.75))}]'))
    result=pd.DataFrame(rows).rename(columns={'Validation':'Validation median [Q1, Q3]' if english else '验证损失中位数[Q1,Q3]',
        'MSPE':'测试MSPE中位数[Q1,Q3]' if not english else 'Test MSPE median [Q1, Q3]',
        'F_score':'测试F-score中位数[Q1,Q3]' if not english else 'Test F-score median [Q1, Q3]'})
    return result.to_markdown(index=False)


def mechanism(frame,english):
    columns=[]
    for method in ['greedy','fixed01','PEM_T','PEM_ST']:
        g=frame[frame.method==method]
        claims=int(g.claims.sum());false=int(g.false_claims.sum())
        columns.append(dict(Method=method,Failure=fmt(g.selected_failure.mean()),QLoss=fmt(g.selected_qloss.mean()),
            Explore=fmt(g.selected_exploration.mean()),Fallback=fmt(g.selected_fallback.mean()),
            Claims=claims,FDP=fmt(false/claims) if claims else 'NA'))
    result=pd.DataFrame(columns)
    if not english:result=result.rename(columns={'Failure':'失效率','QLoss':'0.9分位损失','Explore':'探索比例','Fallback':'回退比例','Claims':'声明数'})
    return result.to_markdown(index=False)


def figures(frame,curves):
    OUT.mkdir(parents=True,exist_ok=True)
    values=[frame[frame.method==m].best_validation_loss for m in ORDER]
    med=np.array([v.median() for v in values]);lo=np.array([v.quantile(.25) for v in values]);hi=np.array([v.quantile(.75) for v in values])
    fig,ax=plt.subplots(figsize=(8.0,4.6));x=np.arange(8);ax.errorbar(x,med,yerr=[med-lo,hi-med],fmt='o',capsize=4)
    ax.set_xticks(x,ORDER,rotation=28,ha='right');ax.set_ylabel('Final raw validation loss');ax.set_title('300-D synt_high: 20 optimization runs');ax.grid(axis='y',alpha=.25)
    if np.all(lo>0):ax.set_yscale('log')
    fig.tight_layout()
    for ext in ['png','pdf']:fig.savefig(OUT/f'high_endpoint.{ext}',dpi=220)
    plt.close(fig)
    fig,ax=plt.subplots(figsize=(8.0,4.8))
    for method in ORDER:
        pivot=curves[curves.method==method].pivot(index='budget_fraction',columns='rep',values='best_validation_loss')
        median=pivot.median(axis=1);ax.plot(pivot.index,median,label=method)
    ax.set_xlabel('Paid budget fraction');ax.set_ylabel('Median best raw validation loss');ax.set_title('300-D synt_high convergence');ax.grid(alpha=.25);ax.legend(ncol=2,fontsize=8)
    if (curves.best_validation_loss>0).all():ax.set_yscale('log')
    fig.tight_layout()
    for ext in ['png','pdf']:fig.savefig(OUT/f'high_convergence.{ext}',dpi=220)
    plt.close(fig)


def section(frame,effect,resources,english):
    if english:
        return f'''# 11 Predefined 300-D Extension

The predefined `synt_high` extension used 1,000 paid evaluations because the unchanged internal initialization requires 620, exceeding the 500-evaluation primary-application budget. Eight methods completed 20 optimization runs on one fixed seed42 data set and split (160 runs; 160,000 validation evaluations; 800,000 CV-fold solves), followed by exactly one held-out test call per completed run. The low-effective-dimensional synthetic construction and different budget preclude a general high-dimensional or cross-task superiority claim.

## 11.1 Endpoints and convergence

{table(frame,True)}

![High-dimensional endpoints](../results/application_high_report_v1/high_endpoint.png)

![High-dimensional convergence](../results/application_high_report_v1/high_convergence.png)

The prespecified descriptive PEM_T-minus-fixed01 median raw-loss difference was {effect.median_raw_loss_difference:+.4g}, with paired-run bootstrap interval [{effect.ci_low:.4g}, {effect.ci_high:.4g}] and {effect.wins}/{effect.losses}/{effect.ties} negative/positive/zero differences. No p-value was computed and this contrast was not added to the three-test primary application family. The interval conditions on one fixed data set and split.

## 11.2 Selected-point feedback and resource boundary

{mechanism(frame,True)}

Feedback summaries cover the 380 post-initialization selections per internal run. They describe each closed-loop history and do not establish same-pool causal effects or conformal error control. Before formal labels, eight separate full-budget resource runs completed {int(resources.algorithm_evaluations.sum()):,} validation evaluations and zero test calls. Their mixed-load timings supported feasibility only; formal optimization times are reported as observed process costs rather than exclusive speedups.

'''
    return f'''# 11 预定300维扩展

预定`synt_high`扩展采用1,000次付费评价，因为未修改的内部初始化需要620次，超过主要应用的500预算。八方法在固定seed42数据与划分上各完成20次优化（160运行、160,000次验证评价、800,000次CV折求解），每个完整运行随后恰调用一次留出测试。该合成任务具有低有效维结构且预算不同，不能据此宣称一般高维能力或跨任务优势。

## 11.1 终点与收敛

{table(frame,False)}

![高维终点](../results/application_high_report_v1/high_endpoint.png)

![高维收敛](../results/application_high_report_v1/high_convergence.png)

预定的PEM_T减fixed01原验证损失中位差为{effect.median_raw_loss_difference:+.4g}，配对运行重采样区间为[{effect.ci_low:.4g}, {effect.ci_high:.4g}]，负/正/零差分别{effect.wins}/{effect.losses}/{effect.ties}。没有计算p值，也未把该比较加入三个主要应用的检验家族；区间条件于同一固定数据和划分。

## 11.2 选择点反馈与资源边界

{mechanism(frame,False)}

反馈汇总覆盖每个内部运行初始化后的380个选择点，仅描述各自闭环历史，不支持同池因果效应或共形错误控制。在正式标签前，八项独立满预算资源运行共完成{int(resources.algorithm_evaluations.sum()):,}次验证评价且零次test。其混合负载计时只用于可行性；正式优化时间按观测进程成本报告，不解释为独占加速。

'''


def main():
    audit,hashes=require_complete();frame=pd.read_csv(ROOT/'results/application_high_analysis_v1/runs.csv')
    curves=pd.read_csv(ROOT/'results/application_high_analysis_v1/convergence.csv')
    effect=pd.read_csv(ROOT/'results/application_high_analysis_v1/descriptive_paired_difference.csv').iloc[0]
    resources=pd.read_csv(ROOT/'results/application_high_method_resource_analysis_v1/resource_costs.csv')
    assert len(frame)==160 and len(curves)==16160 and len(resources)==8 and resources.test_method_calls.sum()==0
    figures(frame,curves)
    sources=[ROOT/'paper/english_integrated_manuscript.md',ROOT/'paper/论文综合机制稿.md']
    assert all(p.exists() for p in sources)
    outputs=[]
    for source,english,name in [(sources[0],True,'english_high_extension_manuscript.md'),(sources[1],False,'论文高维扩展机制稿.md')]:
        text=source.read_text('utf-8');marker='# 11 Conclusion' if english else '# 11 结论';assert text.count(marker)==1
        text=text.replace(marker,section(frame,effect,resources,english)+('# 12 Conclusion' if english else '# 12 结论'),1)
        if english:
            text=text.replace('Reliable SAEA comparisons and the predefined extension remain required','Reliable SAEA comparisons remain required')
            text=text.replace('Reliable competitive SAEA and the predefined high-dimensional extension remain incomplete.','The predefined high-dimensional extension is reported in Section 11; reliable competitive SAEA remains incomplete.')
        else:
            text=text.replace('可靠关键SAEA与预定扩展仍需完成','预定扩展已在第11节完成；可靠关键SAEA仍需完成')
            text=text.replace('关键竞争方法可靠复现与预定300维扩展仍未完成','预定300维扩展已完成，关键竞争方法可靠复现仍未完成')
        now=datetime.now(timezone.utc)+timedelta(hours=8)
        if english:
            lines=text.splitlines();lines=[('date: '+now.strftime('%d %B %Y')) if v.startswith('date: ') else v for v in lines];text='\n'.join(lines)+'\n'
        else:
            lines=text.splitlines();lines=[('date: '+now.strftime('%Y年%m月%d日')) if v.startswith('date: ') else v for v in lines];text='\n'.join(lines)+'\n'
        out=ROOT/'paper'/name;out.write_text(text,encoding='utf-8');outputs.append(out)
    inputs=[ROOT/'results/application_high_analysis_v1'/n for n in ['audit.json','runs.csv','convergence.csv','descriptive_paired_difference.csv','source_hashes.json']]
    inputs += [ROOT/'results/application_high_method_resource_analysis_v1'/n for n in ['audit.json','resource_costs.csv','source_hashes.json']]
    inputs += sources+[Path(__file__)]+[OUT/f'high_{kind}.{ext}' for kind in ['endpoint','convergence'] for ext in ['png','pdf']]+outputs
    record={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    (ROOT/'paper/high_extension_manuscripts_source_hashes.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print('Bilingual high-extension working manuscripts generated; every PDF page remains to be inspected.')


if __name__=='__main__':main()
