"""Chinese work draft integrating separate development/validation evidence."""
import hashlib
import json
from pathlib import Path
import pandas as pd
from .report_validation import table

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'results/mechanism_validation_analysis_v1'
REPORT = ROOT/'results/mechanism_validation_report_v1'


def main():
    audit = json.loads((DATA/'full_integrity_audit.json').read_text('utf-8'))
    assert audit['runs'] == 3888 and audit['diagnostic_evaluations'] == 1990656
    stats = pd.read_csv(DATA/'prespecified_comparisons.csv')
    endpoint = stats[stats.comparison == 'P2_endpoint_PEM_T_minus_fixed01'].sort_values('dim')
    assert len(stats) == 9 and len(endpoint) == 3
    assert (endpoint.estimate>0).all() and (stats.holm_p<.002).all()
    assert (stats[stats.comparison=='P1_history_interaction'].estimate>0).all()
    assert (stats[stats.comparison=='P2_step_feedback_minus_mean'].estimate<0).all()
    effects = '；'.join(f"{int(r.dim)}维终点几何误差比{10**r.estimate:.3f}，Holm p={r.holm_p:.2e}"
                       for r in endpoint.itertuples())
    source = (ROOT/'paper/论文阶段稿.md').read_text('utf-8')
    lines = source.splitlines()
    for j, line in enumerate(lines[:10]):
        if line.startswith('title:'): lines[j] = 'title: 代理辅助黑箱优化中选择后误差监测的决策作用'
        if line.startswith('subtitle:'): lines[j] = 'subtitle: 开发失败与独立机制验证；论文工作稿'
    source = '\n'.join(lines)+'\n'
    begin, end = source.index('# 摘要'), source.index('关键词：')
    source = source[:begin]+f'''# 摘要

代理辅助黑箱优化的候选池、实际评价点和改善声明子集对应不同误差对象，低整体失效率不自动意味着有效预算分配。本文将共同历史误差诊断、共同状态单步决策和独立闭环优化分开，分析评价前预测残差的经验单侧上界及反馈探索。精确实数下，候选无关加法修正在指定规则中保持预测均值排序；数值平局与实际轨迹另作审计。原型在8个BBOB函数、10/20维开发集上未通过优化收益门槛，因而转向机制与失败分析。

独立冻结验证保留全部24函数、10/20/40维、实例11–13和3重复，共3,888运行、907,200计费评价及1,990,656隔离诊断标签。PEM-T相对开发选定固定10%探索的终点几何误差比为1.468、1.258和1.159；反馈即期改善也更低，九项预定比较统一Holm校正后均小于.002。对象失效差异方向依赖历史策略。本文公开全部函数、声明分母、支持回退及Sobol/CMA-ES背景结果，不合并开发与验证统计，不改变原失败门槛，不主张共形保证或一般高维优势。完整竞争、应用与独占资源证据尚待补齐。

'''+source[end:]
    source = source.replace('# 7 结果', '# 7 开发阶段结果', 1)
    source = source.replace('已知最优值$b_{t-1}$', '当前观测最优值$b_{t-1}$')
    source = source.replace('对G/T，同轮内权重', '在精确实数运算下，对G/T，同轮内权重', 1)
    report = (ROOT/'paper/独立机制验证报告.md').read_text('utf-8')
    report = report.split('---', 2)[2].strip()
    for number in range(1, 6):
        report = report.replace(f'# {number} ', f'## 8.{number} ', 1)
    report = report[:report.index('## 8.5 ')]+'''## 8.5 结果解读与外部背景

预定历史差异之差在三个维度均为正，并通过9项家族Holm校正；固定.3历史的实际选中-池内失效差大于贪心历史的对应差。与此同时，贪心和池内随机历史的实际选中失效低于池内整体失效，而固定.3相反。这支持方向依赖历史与决策策略的限定性命题，不支持“筛选必然导致失效增加”的泛化。不同历史不共享池，不能把差异解释为固定池上的独立因果效应。

PEM-T相对开发选定固定.1的终点差在三个维度均为正，共同状态反馈减均值的即期改善差均为负，九项预定比较的校正p均小于.002。该结果独立支持当前反馈规则未带来优化收益的判断；它不证明所有反馈探索无效，即期收益也不识别完整长期因果机制。

'''
    closed = pd.read_csv(REPORT/'closed_loop_decision_summary.csv')
    closed = closed[closed.method.isin(['fixed01', 'PEM_T', 'PEM_ST'])]
    closed = closed[['dim', 'method', 'exploration', 'failure', 'claims', 'false', 'fdp']]
    closed.columns = ['维度', '配置', '探索频率', '上界失效', '声明数', '错误数', '合并FDP']
    declaration_note = '；'.join(f"{int(r['维度'])}维PEM-T作出{int(r['声明数'])}个声明，"
                                f"其中{int(r['错误数'])}个错误，合并FDP为{r['合并FDP']:.1%}"
                                for r in closed[closed['配置']=='PEM_T'].to_dict('records'))
    combined = pd.read_csv(REPORT/'combined_internal_basic_reference_function_scores.csv')
    background = combined.groupby(['dim', 'method']).log_relative_error.mean().unstack().reset_index()
    background = background[['dim', 'fixed01', 'PEM_T', 'PEM_ST', 'sobol', 'cma_es']]
    background.columns = ['维度', '固定.1', 'PEM-T', 'PEM-ST', 'Sobol', 'CMA-ES']
    secondary = json.loads((REPORT/'secondary_metric_conventions.json').read_text('utf-8'))
    report += f'''Table: 独立闭环探索、失效与声明分母。FDP为合并错误数/声明数，不是运行FDP平均。

{table(closed)}

{declaration_note}。约10%的总体失效率没有转化为约10%的声明错误比例；声明子集很小，不能直接由总体比例推断逐声明可靠性，也不能把这些稀疏FDP估计看作稳定的概率保证。

![独立验证收敛曲线。先各实例3重复中位数，再实例和24函数平均；从共同初始化完成后展示。](../results/mechanism_validation_report_v1/convergence_curves.png)

原冻结实现的次要AUC/曲线先将绝对误差截在10^{{-12}}再除以初始误差；主终点先除再截。近零误差时二者可不同，图中保持冻结AUC规则，不为贴合终点而改值。实际共有{secondary['curve_entries_below_minus12']}个初始化后曲线条目低于-12，{secondary['runs_ending_at_exact_optimum']}个运行终点达到记录的精确最优值。该补充仅公开计算约定，不新增显著性检验。

Table: 全24函数的描述性背景终点均值，越低越好。

{table(background)}

Sobol/CMA-ES共1,296运行、302,400次计费评价，另通过全量日志审计；保留自身初始化和搜索。背景归一化仅在分析阶段使用匹配问题/seed的内部共同初始误差，先单运行归一化再取中位数，分母不传给外部算法。它不是同历史因果对照，也不替代关键SAEA竞争方法。正式GP-EI/TuRBO完整批次尚在执行，不以部分完成的结果作排名。

## 8.6 数值、支持与适用边界

加法修正的严格排序等价是精确实数命题。浮点中将公共常数10^16加到均值[1,0]会得到相等上界，从而改变首索引平局选择；这个教学反例不进入基准统计。开发轨迹一致性及新验证全部G/T决策索引审计属于各自已执行范围的实现证据。本次独立诊断记录{len(audit['diagnostic_G_T_ordering_disagreements'])}项G/T上界与均值索引不一致。

本次实际有{audit['fits_with_training_truncation']}次拟合发生256训练点截断。空间校准分位数损失、余量、ESS、回退、稀疏声明及五组预定BBOB结构表均完整公开；不依据有利子组更换主方法。40维不是一般高维能力证明。共享负载耗时不作为独占加速证据，廉价解析目标也不能替代真实应用时间节省。

'''
    source = source.replace('# 8 讨论', '# 8 独立机制验证\n\n'+report+'# 9 讨论', 1)
    source = source.replace('# 9 结论', '# 10 结论', 1)
    start = source.index('# 10 结论')
    end = source.index('# 参考文献', start)
    source = source[:start]+f'''# 10 结论

本文将共同历史误差、共同状态选点评价和独立闭环终点分开，并审计预测前信息与真实评价预算。精确实数下的候选无关加法修正在规定规则中保持均值排序，其实现边界另由数值及轨迹证据说明。开发阶段反馈原型未通过优化收益门槛；独立全24函数验证继续观察到PEM-T相对固定.1的终点误差更大、反馈即期改善更低，并支持对象差异方向依赖历史策略。{effects}。这些结果支持当前规则的机制与失败分析，不证明一般反馈或共形优化无效。完整竞争、应用及独占成本证据仍需完成，本文为可审计工作稿，未宣称投稿就绪。

'''+source[end:]
    source = source.replace('若$q_t(x)$和$s_t$均与候选无关', '在精确实数运算下，若$q_t(x)$和$s_t$均与候选无关')
    appendix = source.index('# 附录 可复现性与完成状态')
    source = source[:appendix]+'''# 附录 可复现性与完成状态

原始评价日志、候选池、独立诊断标签、代码哈希、依赖锁、种子、失败记录、函数级统计及预定比较均保留在工作区。开发阶段与新机制验证各有独立冻结协议和全量审计；新验证没有读取原保留实例6–10，诊断标签不进入任何优化器。本文的优化排序命题限于精确实数运算和指定规则，已执行索引/轨迹一致性另有证据。

已完成开发与独立机制数据、两种基础参照、中英文工作稿及补充材料。GP-EI/TuRBO完整参照、独占计时、关键竞争方法可获得性与应用证据仍未全部完成；未根据这些缺口或活批次结果宣称投稿就绪。原优化改进路线门槛失败，因此不机械扩大原CEC或应用协议去替代这一判断。
'''
    path = ROOT/'paper/论文机制研究稿.md'; path.write_text(source, encoding='utf-8')
    sources = [ROOT/'paper/论文阶段稿.md', ROOT/'paper/独立机制验证报告.md', DATA/'prespecified_comparisons.csv',
               DATA/'full_integrity_audit.json', REPORT/'secondary_metric_conventions.json']
    (ROOT/'paper/论文机制研究稿_源指纹.json').write_text(json.dumps(
        {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        ensure_ascii=False, indent=2), encoding='utf-8')
    print(path)


if __name__ == '__main__':
    main()
