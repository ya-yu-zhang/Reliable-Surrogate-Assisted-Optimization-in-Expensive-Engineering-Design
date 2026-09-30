"""Budget and event audit, descriptive per-function reference results."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--out',required=True)
    args=ap.parse_args();source,out=Path(args.source),Path(args.out);out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((source/'manifest.json').read_text('utf-8'))
    config=manifest['config'];files=sorted(source.glob('*/summary.json'))
    expected=len(config['functions'])*len(config['dimensions'])*len(config['instances'])*config['repeats']*len(config['methods'])
    assert len(files)==expected==1296
    assert not json.loads((source/'failures.json').read_text('utf-8'))
    rows=[];charged=0;digests=[]
    for file in files:
        summary=json.loads(file.read_text('utf-8'));sig=summary['signature']
        assert sig['code_hash']==manifest['code_hash']
        path=file.parent/'events.jsonl'
        events=[json.loads(v) for v in path.read_text('utf-8').splitlines()]
        assert events[0]['event']=='meta'
        pre,labels=events[1::2],events[2::2]
        assert len(pre)==len(labels)==sig['budget']==summary['algorithm_evaluations']
        best=np.inf
        for t,(a,b) in enumerate(zip(pre,labels),1):
            assert a['event']=='pre' and b['event']=='label'
            assert a['t']==b['t']==t and a['n_observed']==t-1 and 'y' not in a
            assert a['best_before']==(None if t==1 else best)
            point=np.array(a['x_unit']);assert np.isfinite(point).all() and np.all((point>=0)&(point<=1))
            assert np.isfinite(b['y'])
            best=min(best,b['y']);assert b['best_after']==best
        assert best==summary['best']
        charged+=len(labels)
        rows.append(dict(**{k:sig[k] for k in ['fid','dim','instance','rep','method']},
                         **{k:summary[k] for k in ['error','log_absolute_error','elapsed','exact_duplicate_calls']},
                         algorithm_evaluations=summary['algorithm_evaluations']))
        digests.append(dict(runid=summary['runid'],sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    frame=pd.DataFrame(rows);frame.to_csv(out/'runs.csv',index=False)
    instance=frame.groupby(['dim','fid','instance','method']).log_absolute_error.median()
    instance.groupby(['dim','fid','method']).mean().to_csv(out/'function_log_absolute_errors.csv')
    raw=frame.groupby(['dim','fid','method']).error.agg(median='median',q25=lambda s:s.quantile(.25),q75=lambda s:s.quantile(.75))
    raw.to_csv(out/'raw_error_iqr.csv')
    frame.groupby(['dim','method']).agg(runs=('fid','size'),evaluations=('algorithm_evaluations','sum'),
                                      exact_duplicate_calls=('exact_duplicate_calls','sum'),shared_elapsed_median=('elapsed','median')).to_csv(out/'resource_counts.csv')
    audit=dict(expected=expected,audited_runs=len(files),algorithm_evaluations=charged,failures=0,
               no_future_labels_in_pre=True,all_calls_charged=True,all_points_in_bounds=True,
               exact_duplicate_calls=int(frame.exact_duplicate_calls.sum()),
               descriptive_only=True,not_a_reproduction_of_temporal_CP_SAEA=True,
               shared_load_timing_not_solo_cost=True)
    assert charged==302400
    (out/'audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    (out/'source_journal_hashes.json').write_text(json.dumps(digests,indent=2),encoding='utf-8')
    functions=instance.groupby(['dim','fid','method']).mean().unstack('method')
    comparison=[]
    for dim,group in functions.groupby(level='dim'):
        delta=group['cma_es']-group['sobol']
        comparison.append(f'| {dim} | {int((delta<0).sum())} | {int((delta>0).sum())} | {int((delta==0).sum())} |')
    report='''# 基础外部参照实验报告

日期：2026-09-17。两项基础参照全部完成并通过原始日志审计；关键SAEA竞争方法的性能复现仍未完成。

## 范围与实现

Sobol和pycma CMA-ES分别648运行；BBOB全24函数，10/20/40维，实例11–13，每实例3重复，预算10D。两者使用各自搜索机制，未共享代理初始化。CMA-ES初始均值.5、标准差.3、默认人口与更新、边界[0,1]；按预算继续更新，最后不足整代时仅评价剩余个体，未将部分代传给tell。Sobol使用全域scrambled序列的预算前缀。配置事前冻结，未据这些结果调参。

## 审计

1,296/1,296运行、302,400算法评价、0异常失败、0精确重复点；全部目标调用付费且点在边界内，评价前记录没有未来标签。共享负载耗时包含日志，不作为独占速度比较。

## 描述性结果

每实例先取3运行终点对数误差中位数，再3实例平均；下表只比较同函数的两项参照，计数单位是函数。原始误差中位数/IQR与函数级表完整保存，未作新增显著性检验。这不是PEM原型与外部方法的胜负表。

| 维度 | CMA-ES误差较低 | Sobol误差较低 | 相同 |
| --- | --- | --- | --- |
'''+ '\n'.join(comparison)+'''

结果目录：`results/basic_references_analysis_v1/`。`runs.csv`保存单运行结果，`function_log_absolute_errors.csv`保存函数级估计，`raw_error_iqr.csv`公开绝对终点误差，`resource_counts.csv`保存次数与共享时间，`audit.json`和日志指纹提供完整性证据。单个函数的绝对误差量纲不能横跨函数直接比较。

下一步在独立机制验证真正完成后，与内部策略按相同问题展示。若使用共同初始化归一化，分母只在分析阶段读入，外部算法不获取内部标签；当前不提前给出该比较。
'''
    (Path(__file__).resolve().parents[1]/'docs/基础外部参照实验报告.md').write_text(report,encoding='utf-8')
    print(json.dumps(audit,indent=2))


if __name__=='__main__':main()
