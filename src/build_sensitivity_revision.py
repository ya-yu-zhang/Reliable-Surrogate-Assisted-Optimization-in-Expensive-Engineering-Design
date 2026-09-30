"""Append complete model sensitivity evidence to the high-extension working manuscripts."""
import hashlib,json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/model_sensitivity_report_v1'
ORDER=['base','cap128','cap512','scale125','scale500']


def require_complete(root=ROOT):
    audit=json.loads((root/'results/model_sensitivity_analysis_v1/audit.json').read_text('utf-8'))
    assert audit['complete_design'] and audit['runs']==450 and audit['algorithm_evaluations']==135000
    assert audit['diagnostic_evaluations']==0 and audit['raw_file_hashes']==1350
    assert audit['twenty_dim_base_cap512_invariant_runs']==45 and audit['statistical_tests_added']==0
    hashes=json.loads((root/'results/model_sensitivity_analysis_v1/source_hashes.json').read_text('utf-8'))
    assert len(hashes)==1350 and all(hashlib.sha256((root/n).read_bytes()).hexdigest()==v for n,v in hashes.items())
    return audit,hashes


def fmt(v):return f'{v:.4g}'


def make_tables(runs,metrics,effects,english):
    endpoint=[]
    for dim in [20,40]:
        for variant in ORDER:
            g=runs[(runs.dim==dim)&(runs.variant==variant)]
            endpoint.append(dict(D=dim,Variant=variant,Endpoint=f'{fmt(g.log_relative_error.median())} [{fmt(g.log_relative_error.quantile(.25))}, {fmt(g.log_relative_error.quantile(.75))}]',
                                 AUC=f'{fmt(g.auc_log_relative.median())} [{fmt(g.auc_log_relative.quantile(.25))}, {fmt(g.auc_log_relative.quantile(.75))}]'))
    endpoint=pd.DataFrame(endpoint).rename(columns={'Endpoint':'终点中位数[Q1,Q3]' if not english else 'Endpoint median [Q1, Q3]',
                                                    'AUC':'AUC中位数[Q1,Q3]' if not english else 'AUC median [Q1, Q3]'})
    effect=effects.copy();effect['Difference']=effect.apply(lambda r:f'{fmt(r.median_difference)} [{fmt(r.q1)}, {fmt(r.q3)}]',axis=1)
    effect=effect[['dim','variant','Difference','negative','positive','zero']]
    effect.columns=['D','Variant','差值中位数[Q1,Q3]' if not english else 'Difference median [Q1, Q3]',
                    '负' if not english else 'Negative','正' if not english else 'Positive','零' if not english else 'Zero']
    mechanism=[]
    for dim in [20,40]:
        for variant in ORDER:
            g=metrics[(metrics.dim==dim)&(metrics.variant==variant)]
            mechanism.append(dict(D=dim,Variant=variant,Capped=int(g.capped_fits.sum()),Failure=fmt(g.upper_failure.mean()),
                                   Explore=fmt(g.explore_frequency.mean()),Fallback=fmt(g.fallback.mean())))
    mechanism=pd.DataFrame(mechanism)
    if not english:mechanism=mechanism.rename(columns={'Capped':'截断拟合数','Failure':'失效率','Explore':'探索比例','Fallback':'回退比例'})
    return endpoint.to_markdown(index=False),effect.to_markdown(index=False),mechanism.to_markdown(index=False)


def figures(runs):
    OUT.mkdir(parents=True,exist_ok=True);fig,axes=plt.subplots(1,2,figsize=(10,4.3),sharey=True)
    for ax,dim in zip(axes,[20,40]):
        groups=[runs[(runs.dim==dim)&(runs.variant==v)].log_relative_error for v in ORDER]
        ax.boxplot(groups,tick_labels=ORDER,showfliers=False);ax.tick_params(axis='x',rotation=28)
        ax.set_title(f'D={dim}');ax.grid(axis='y',alpha=.25)
    axes[0].set_ylabel('Final log10 relative error');fig.suptitle('PEM_T model and training-cap sensitivity');fig.tight_layout()
    for ext in ['png','pdf']:fig.savefig(OUT/f'sensitivity_endpoint.{ext}',dpi=220)
    plt.close(fig)


def section(runs,metrics,effects,english):
    endpoint,effect,mechanism=make_tables(runs,metrics,effects,english)
    if english:return f'''# 12 Prespecified Model and Training-Cap Sensitivity

Five preselected BBOB structure representatives (f1, f6, f10, f15, f20), dimensions 20/40, instances 14–16, and three optimization repeats evaluated PEM_T under the base setting and four one-factor perturbations. All 450 runs and 135,000 paid evaluations completed; no hidden diagnostic labels or inferential tests were added. This local sensitivity study does not select a replacement default.

{endpoint}

![Model and training-cap sensitivity](../results/model_sensitivity_report_v1/sensitivity_endpoint.png)

Paired differences below are variant minus base in final log10 relative error. Negative values favor the variant descriptively.

{effect}

The 45 D=20 base/cap512 pairs had identical PRE/LABEL trajectories and candidate arrays, as neither cap was reached. Thus that equality is an implementation invariant rather than evidence that caps never matter. At D=40, cap512 is untruncated only within this 400-evaluation scope.

{mechanism}

Feedback metrics follow each variant's distinct closed-loop history. The limited function/instance set, shared initialization, and absence of multiplicity-adjusted inference restrict these results to robustness description.

'''
    return f'''# 12 预定模型与训练截断敏感性

在预选BBOB五类结构代表（f1、f6、f10、f15、f20）、20/40维、实例14–16和3个优化重复上，比较PEM_T默认配置与四个单因素扰动。450运行和135,000次付费评价全部完成；没有隐藏诊断标签或新增推断检验。本局部敏感性不用于选择新的默认参数。

{endpoint}

![模型与训练截断敏感性](../results/model_sensitivity_report_v1/sensitivity_endpoint.png)

下表配对差为变体减base的最终log10相对误差；负值在描述上有利于变体。

{effect}

20维45组base/cap512的PRE/LABEL与候选数组逐位一致，因为两者均未触及上限；这是实现不变量，不表示训练上限永不影响结果。40维cap512只在本400评价范围内等同不截断。

{mechanism}

反馈指标来自各变体不同的闭环历史。有限函数/实例、共享初始化及无多重校正推断，使结论仅限于稳健性描述。

'''


def main():
    audit,hashes=require_complete();runs=pd.read_csv(ROOT/'results/model_sensitivity_analysis_v1/runs.csv')
    metrics=pd.read_csv(ROOT/'results/model_sensitivity_analysis_v1/mechanism_metrics.csv')
    effects=pd.read_csv(ROOT/'results/model_sensitivity_analysis_v1/descriptive_paired_differences.csv')
    assert len(runs)==len(metrics)==450 and len(effects)==8;figures(runs)
    sources=[ROOT/'paper/english_high_extension_manuscript.md',ROOT/'paper/论文高维扩展机制稿.md'];assert all(p.exists() for p in sources)
    outputs=[]
    for source,english,name in [(sources[0],True,'english_complete_mechanism_manuscript.md'),(sources[1],False,'论文完整机制稿.md')]:
        text=source.read_text('utf-8');marker='# 12 Conclusion' if english else '# 12 结论';assert text.count(marker)==1
        text=text.replace(marker,section(runs,metrics,effects,english)+('# 13 Conclusion' if english else '# 13 结论'),1)
        text=text.replace('model/budget sensitivity and the predefined extension continue as gaps.','budget sensitivity remains a gap; the predefined extension and model/training-cap sensitivity are reported in Sections 11–12.') if english else text
        text=text.replace('模型/预算敏感性与预定扩展继续作为缺口。','预定扩展与模型/训练截断敏感性见第11–12节；预算性能敏感性仍是缺口。') if not english else text
        out=ROOT/'paper'/name;out.write_text(text,encoding='utf-8');outputs.append(out)
    inputs=[ROOT/'results/model_sensitivity_analysis_v1'/n for n in ['audit.json','runs.csv','mechanism_metrics.csv','descriptive_paired_differences.csv','source_hashes.json']]
    inputs+=sources+[Path(__file__),OUT/'sensitivity_endpoint.png',OUT/'sensitivity_endpoint.pdf']+outputs
    (ROOT/'paper/complete_mechanism_source_hashes.json').write_text(json.dumps({p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},indent=2),encoding='utf-8')
    print('Sensitivity revision generated; PDF compilation and all-page inspection remain.',flush=True)


if __name__=='__main__':main()
