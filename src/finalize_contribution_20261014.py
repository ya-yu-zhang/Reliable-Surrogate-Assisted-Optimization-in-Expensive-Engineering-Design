"""Close the contribution judgment without changing historical experiments."""
import hashlib
import json
from pathlib import Path
from .diagnose_h1_bound_bottlenecks import run

MAIN_NOTE = r'''\paragraph{Which information blocks the engineering certificate?}
Let $T=B-\epsilon$, where $B$ is the paid H1 baseline and $\epsilon$ the declared absolute margin. For the existing relaxed lower-bound certificate in Eq.~\eqref{eq:joint_lower}, $J\geq T$ holds if and only if $m_{\mathrm{init}}\geq T$ and, for every retained action, both $\max(p,\inf R_i)\geq T$ and $\lambda_i\geq T$. This is a decomposition of the supplied certificate, not a new optimization theorem. A post hoc exact-rational check finds both information sources blocking all71 nonbaseline contrasts in each response domain. Of281 retained action terms per domain,71 pending-response terms and276 next-point bounds lie below their branch's threshold. The median, across contrasts, of the weakest retained next-point bound divided by its threshold is0.1622. Thus the present certificate cannot be repaired by increasing only one class of lower bounds while holding the relaxed action sets fixed. Changing the sets, exploiting coupled coefficient information or acquiring different physical information is outside this comparison. Failure of this sufficient certificate does not imply that the true action is inferior.

'''

SUPP_NOTE = r'''\section{H1 threshold decomposition and contribution closure}\label{supp:h1_bottleneck}

This descriptive analysis reads the existing exact action intervals, point bounds and paid baseline endpoints. It reads no additional physical response, evaluates no physical bound and changes no protocol. For branch threshold $T=B-\epsilon$, the main-text joint lower bound is at least $T$ exactly when the initial incumbent and both terms for every retained action are at least $T$. The proof is the elementary equivalence between a minimum exceeding a threshold and all of its arguments exceeding that threshold. The result describes sufficiency of the supplied relaxed certificate; it is not an impossibility result for the coupled GP or true engineering objective.

Both predeclared domains give71 nonbaseline contrasts and281 retained action terms. All71 contrasts have at least one pending term and one next-point term below threshold. There are71 failing pending terms and276 failing next-point terms. These are dependent descriptive counts; the two domains do not double the independent sample size. The median weakest next-point-bound/threshold ratio is0.1622233735904155. Raising only pending terms, or only next-point terms, cannot make the fixed-set certificate pass. Actual stronger physical information could change response domains or action sets, so no extrapolated impossibility claim is made.

The reader is \path{src/diagnose_h1_bound_bottlenecks.py}. Its output includes branch- and action-level rational thresholds, input SHA-256 hashes and a summary. Four synthetic checks cover the closed margin boundary, separate information bottlenecks, distinct blocking actions and the independent incumbent constraint. These checks contain no engineering optimization samples. The original31-test record remains separate.

The contribution judgment remains limited: numerical certificate production and its scoped computational improvement are supported; positive independent decision efficacy and full deployment savings are not. This additional diagnosis locates the physical-information bottleneck, but does not turn that negative outcome into an optimizer-performance claim or certify a journal novelty threshold.
'''

DECISION = '''# 贡献裁决与项目收尾 — 2026-10-14

唯一当前科研基线：`58f539c2d0738b20c7d0d4889fe8d808a03a3019`。

**裁决：计算贡献已核验；优化收益及充分原创性尚未得到证据支持。当前不能标记为 Engineering Optimization 科学门槛已通过。**

## 已经做成的工作

两次冻结 witness 已完成真响应诊断，额度2/2用完。基于完整保留的GP开发记录，数值系数带、闭响应域、精确行动区间及短排除证书形成可执行方法。在114分支、两个预定响应域上，所有行动集与冻结成对参考一致；232,564项新排除通过独立有理数检查。构造阶段约3.19倍加速，另加独立证书重放约2.62倍。它是计算阶段结果，不是物理求解节省或优化终点改善。

## 为什么工程决策门槛仍未过

新完成的零求解诊断给出明确原因：每个响应域的71个非基线对比，全部同时受到待观测响应项与下一点物理下界的限制。281个保留动作项中，71个待响应项、276个下一点下界未达到“不比已支付基线好超过容差”的认证阈值。每分支最弱下一点下界/阈值的中位数为0.1622233735904155。

这是现有保守认证公式的缺口，不是真实动作劣于基线的证明。固定现有行动区间时，单独改善一种下界不足；若更强信息能改变区间或利用系数耦合，本结论不能推广。新诊断未创造独立阳性样本，也未改变H1/H5失败门槛。

## 与最接近工作的区别及剩余风险

Frazier、Powell、Dayanik（2009）的仿射包络几何及其作者代码已经存在。此次读取作者仓库的`ckg/AffineBreakpoints.m`和`ckg/AffineBreakpointsPrep.m`：前者针对单组精确仿射线计算接受区间，后者按斜率排序并处理重复斜率。作者代码中交点使用普通数值运算。不能把仿射更新、排序包络或O(M log M)本身宣传为新思想。

本实现添加的是针对数值系数带的可执行契约：上带包络与每条原始下带候选分开处理、保留闭区间单点动作、独立重放排除证书。这个区别是真实的，但现有对比只覆盖冻结成对实现；尚未证明相对最强现有同目标实现的原创性或速度优势。这次源码核对不是全领域查新结论。

2026年的PALM-Mean公开预印本研究固定已训练GP均值在连续设计变量域内的确定性全局优化，目标与本项目“一个未知响应、有限下一动作”的问题不同。它提醒我们“认证GP优化”不是空白领域；不声称该预印本不能扩展到本问题，也未在其基准上复现本方法。

## 今天可完成与不能承诺的结果

可以完成：现有证据支持的计算方法与受限工程评估论文、完整的当前GP复核附件、清楚的数据缺口说明、源码的独立GitHub分支保存。

不能通过排版、换标题或更多同类核验宣布已完成：新的有效优化策略、独立阳性决策优势、完整部署节省、所有历史原始记录恢复、目标期刊创新充分性或录用。

如果坚持以“已证实更有效的工程优化方法”为主要贡献，目前需要方法和研究协议层面的新工作。现有两次物理评估上限没有剩余额度，本项目不能自行重试、替换witness或新增独立优化样本。若保持现有约束，收尾应坚持数值认证方法与明确局限的定位。

作者单位b/c按用户选择继续待补。实际投稿事实与目标刊细则未解决的项目仍列在现有准备记录，不能伪造为已通过。没有执行期刊投稿或改变仓库可见性。

## 保存范围

独立GitHub分支保存本轮代码、稿件文本源、派生结果和裁决；它不替代你已下载的`Paper_project_closure_20261014.zip`与历史原始大档案。当前配对网格仍缺3份原始记录；不能从汇总表或哈希恢复其内容。主分支仍保留唯一基线。下载包的持久保存状态以本轮收据为准，不能以链接代替成功保存。

## 本轮读取的原始来源

- 作者历史软件仓库：https://github.com/INFORMSJoC/1080.0314
- 作者包络实现：https://github.com/INFORMSJoC/1080.0314/blob/main/ckg/AffineBreakpoints.m
  blob SHA：247c7ccb477e3f9a37c91e8a1d0d9a293de0104c
- 作者准备实现：https://github.com/INFORMSJoC/1080.0314/blob/main/ckg/AffineBreakpointsPrep.m
  blob SHA：591156d70110d5d41f669f6b19ab45beb00f2d54
- PALM-Mean作者公开预印本（未当作已发表论文）：https://arxiv.org/html/2605.00855v1
- 工程优化期刊范围：https://www.tandfonline.com/journals/geno20
'''


def finalize(root):
    root = Path(root)
    result = run(root)
    paper = root/'submission_20261014/source/paper/engineering_optimization'
    manuscript = paper/'EO_manuscript.tex'
    s = manuscript.read_text()
    marker = r'\paragraph{Which information blocks the engineering certificate?}'
    if marker not in s:
        at = s.index(r'\hypertarget{frozen-state-intervention-on-gp-acquisition-policies}')
        s = s[:at]+MAIN_NOTE+s[at:]
        manuscript.write_text(s)
    note = paper/'integrated_evidence/h1_bound_bottleneck_closure.tex'
    note.write_text(SUPP_NOTE)
    supplement = paper/'EO_supplementary.tex'
    s = supplement.read_text()
    command = r'\input{integrated_evidence/h1_bound_bottleneck_closure.tex}'
    s = s.replace(command+'\n', '')
    s = s.replace(r'\bibliographystyle{tfcad}', command+'\n\n'+r'\bibliographystyle{tfcad}')
    supplement.write_text(s)
    prep = root/'submission_20261014'
    (prep/'CONTRIBUTION_DECISION_20261014.md').write_text(DECISION)
    verification = json.loads((prep/'SOURCE_VERIFICATION.json').read_text())
    for row in verification['source_files']:
        p = prep/row['path']
        row.update(bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    rel = note.relative_to(prep).as_posix()
    if not any(x['path'] == rel for x in verification['source_files']):
        verification['source_files'].append({'path': rel, 'bytes': note.stat().st_size,
                                            'sha256': hashlib.sha256(note.read_bytes()).hexdigest()})
    verification['new_readonly_H1_threshold_diagnosis'] = True
    verification['core_algorithm_or_historical_empirical_results_changed'] = False
    (prep/'SOURCE_VERIFICATION.json').write_text(json.dumps(verification, indent=2)+'\n')
    readme = prep/'REVIEW_REPRODUCTION.md'
    s = readme.read_text()
    note = '\nAfter the preparation builder, apply the final read-only diagnosis and source addition:\n\n```sh\npython3 -m src.finalize_contribution_20261014\npython3 -m unittest tests.test_h1_bound_bottlenecks -v\n```\nThis reads already recorded bounds only. It adds no physical evaluation and leaves the original efficacy gate false.\n'
    if 'src.finalize_contribution_20261014' not in s:
        readme.write_text(s+note)
    print(json.dumps({'diagnosis': result['domains'], 'manuscript_sources_updated': True,
                      'new_physical_evaluations': 0, 'EO_scientific_gate_certified': False}))


if __name__ == '__main__':
    finalize(Path(__file__).resolve().parents[1])
