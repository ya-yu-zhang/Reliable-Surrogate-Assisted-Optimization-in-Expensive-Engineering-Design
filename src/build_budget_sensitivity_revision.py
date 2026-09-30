"""Append prespecified budget-performance evidence and recovery accounting."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/budget_performance_sensitivity_report_v1"
ORDER = [
    "greedy", "fixed01", "fixed03", "pool_random", "PEM_T", "PEM_ST",
    "sobol", "cma_es", "gp_ei", "turbo_1",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_complete(root=ROOT):
    analysis = root / "results/budget_performance_sensitivity_analysis_v1"
    audit = json.loads((analysis / "audit.json").read_text("utf-8"))
    assert audit["complete_design"] and audit["runs"] == 2700
    assert audit["algorithm_evaluations"] == 810000
    assert audit["diagnostic_evaluations"] == 0
    assert audit["raw_file_hashes"] == 7020
    assert audit["pre_information_verified"]
    assert audit["internal_bounds_and_management_replayed"]
    assert audit["internal_budget_prefix_invariant_runs"] == 540
    assert 0 <= audit["external_prefix_equal_runs"] <= 360
    assert audit["statistical_tests_added"] == 0
    assert audit["not_used_for_parameter_selection"]
    assert audit["source_hashes_verified"]
    hashes = json.loads((analysis / "source_hashes.json").read_text("utf-8"))
    assert len(hashes) == 7020
    assert all(digest(root / name) == value for name, value in hashes.items())

    freeze_root = root / "docs/frozen_second_recovery_audit_v1"
    recovery_hashes = json.loads((freeze_root / "sha256.json").read_text("utf-8"))
    assert len(recovery_hashes) == 80
    assert all(digest(freeze_root / name) == value for name, value in recovery_hashes.items())
    recovery = json.loads(
        (freeze_root / "results/interruption_20260919_v2/second_recovery_audit.json").read_text("utf-8")
    )
    assert recovery["objective_calls_by_this_auditor"] == 0
    assert recovery["recovered_runs"] == 8
    assert recovery["canonical_algorithm_evaluations"] == 2800
    assert recovery["second_generation_saved_labels"] == 2014
    assert recovery["second_generation_new_physical_calls"] == 786
    assert recovery["redundant_recovery_validation_calls"] == 1
    assert not recovery["redundant_call_entered_optimizer_history"]
    assert recovery["redundant_point_and_label_exactly_equal_to_first_archive"]
    assert recovery["all_canonical_trajectories_complete"]
    budget_recovery = json.loads(
        (root / "results/budget_interruption_20260924_v1/recovery.json").read_text("utf-8")
    )
    assert budget_recovery["completed_before_resume"] == 1910
    assert budget_recovery["partial_run_count"] == 8
    interrupted_physical = 0
    for relative in budget_recovery["partial_runs_archived"]:
        journal = root / "results/budget_interruption_20260924_v1/partial_runs" / relative / "events.jsonl"
        events = [json.loads(line) for line in journal.read_text("utf-8").splitlines()]
        interrupted_physical += sum(event.get("event") == "label" for event in events)
    assert interrupted_physical == 1791
    return audit, hashes, recovery, recovery_hashes, budget_recovery, interrupted_physical


def fmt(value):
    return f"{value:.4g}"


def endpoint_table(scores, english):
    rows = []
    for method in ORDER:
        row = {"Method": method}
        for dim in [20, 40]:
            for multiplier in [5, 10, 15]:
                selected = scores[
                    (scores.method == method)
                    & (scores.dim == dim)
                    & (scores.budget_multiplier == multiplier)
                ]
                assert len(selected) == 1
                row[f"D{dim}-{multiplier}D"] = fmt(selected.log_relative_error.iloc[0])
        rows.append(row)
    table = pd.DataFrame(rows)
    if not english:
        table = table.rename(columns={"Method": "方法"})
    return table.to_markdown(index=False)


def prefix_table(prefix, english):
    rows = []
    for method in ORDER:
        selected = prefix[prefix.method == method]
        assert len(selected) == 90
        equal = int(selected.all_budget_prefixes_equal.sum())
        rows.append(
            {
                "Method" if english else "方法": method,
                "Equal 5D/10D/15D prefixes" if english else "5D/10D/15D前缀相同": f"{equal}/90",
                "Required invariant" if english else "是否为规定不变量": (
                    "yes" if english else "是"
                ) if method in ORDER[:6] else ("no" if english else "否"),
            }
        )
    return pd.DataFrame(rows).to_markdown(index=False)


def figures(scores, curves):
    OUT.mkdir(parents=True, exist_ok=True)
    colors = plt.cm.tab10(np.linspace(0, 1, len(ORDER)))
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.5), sharey=True)
    for ax, dim in zip(axes, [20, 40]):
        for method, color in zip(ORDER, colors):
            selected = scores[(scores.method == method) & (scores.dim == dim)].sort_values("budget_multiplier")
            assert len(selected) == 3
            ax.plot(selected.budget_multiplier, selected.log_relative_error, marker="o", label=method, color=color)
        ax.set_title(f"D={dim}")
        ax.set_xlabel("Total paid budget / D")
        ax.set_xticks([5, 10, 15])
        ax.grid(alpha=.25)
    axes[0].set_ylabel("Hierarchical mean final log10 relative error")
    axes[1].legend(ncol=2, fontsize=7.5, loc="best")
    fig.suptitle("Prespecified budget-performance sensitivity")
    fig.tight_layout()
    for ext in ["png", "pdf"]:
        fig.savefig(OUT / f"budget_endpoints.{ext}", dpi=220)
    plt.close(fig)

    hierarchical = (
        curves.groupby(
            ["method", "dim", "budget_multiplier", "fid", "instance", "budget_fraction"],
            as_index=False,
        ).log_relative_error.median()
        .groupby(["method", "dim", "budget_multiplier", "budget_fraction"], as_index=False)
        .log_relative_error.mean()
    )
    fig, axes = plt.subplots(2, 3, figsize=(12.0, 7.0), sharex=True, sharey=True)
    for row, dim in enumerate([20, 40]):
        for column, multiplier in enumerate([5, 10, 15]):
            ax = axes[row, column]
            for method, color in zip(ORDER, colors):
                selected = hierarchical[
                    (hierarchical.method == method)
                    & (hierarchical.dim == dim)
                    & (hierarchical.budget_multiplier == multiplier)
                ].sort_values("budget_fraction")
                assert len(selected) == 101
                ax.plot(selected.budget_fraction, selected.log_relative_error, color=color, label=method)
            ax.set_title(f"D={dim}, B={multiplier}D")
            ax.grid(alpha=.22)
            if row == 1:
                ax.set_xlabel("Paid-budget fraction")
            if column == 0:
                ax.set_ylabel("Hierarchical mean log10 relative error")
    axes[0, 2].legend(ncol=2, fontsize=7, loc="best")
    fig.suptitle("Independent-run convergence at each total budget")
    fig.tight_layout()
    for ext in ["png", "pdf"]:
        fig.savefig(OUT / f"budget_convergence.{ext}", dpi=220)
    plt.close(fig)


def section(scores, prefix, recovery, budget_recovery, interrupted_physical, english):
    endpoints = endpoint_table(scores, english)
    prefixes = prefix_table(prefix, english)
    external_equal = int(prefix[~prefix.method.isin(ORDER[:6])].all_budget_prefixes_equal.sum())
    if english:
        return f'''# 13 Prespecified Budget-Performance Sensitivity

## 13.1 Design and aggregation

Five prespecified BBOB structure representatives (f1, f6, f10, f15, and f20), dimensions 20/40, instances 17–19, and three repeats were run independently at total budgets 5D, 10D, and 15D. Six internal configurations and four external references completed all 2,700 runs and 810,000 paid evaluations, with no diagnostic labels. Each endpoint uses the matching fixed01 common-initialization error as a post-run denominator. We first take the repeat median within each function-instance cell, then average the three instances within each function and the five function scores with equal weight. No hypothesis test, confidence interval, or parameter selection was added.

## 13.2 Endpoints and convergence

Lower values are better. Each table entry is the prespecified hierarchical mean final log10 relative error.

{endpoints}

![Budget-sensitivity endpoints](../results/budget_performance_sensitivity_report_v1/budget_endpoints.png)

![Budget-sensitivity convergence](../results/budget_performance_sensitivity_report_v1/budget_convergence.png)

Each budget is a separate optimization run. A longer-budget endpoint therefore supplies robustness evidence under a larger total allowance; it is not a continuation selected after observing the shorter run. The restricted five-function, two-dimension design and descriptive aggregation do not establish a new general ranking.

## 13.3 Prefix and information-order audit

{prefixes}

The budget-blind internal core was required to reproduce identical 5D and 10D prefixes inside the corresponding longer run; all 540 required comparisons passed. External prefix equality was recorded rather than required: {external_equal}/360 comparisons were equal. That count is an implementation observation, not an assumption used to validate external methods. Full audits replayed all 810,000 PRE/LABEL pairs, internal bounds and management states, and 7,020 raw-file hashes. No total-budget value entered the internal proposal rule.

## 13.4 Recovery accounting and evidence boundary

The budget-sensitivity interruption left {budget_recovery['partial_run_count']} incomplete units with {interrupted_physical:,} physically acquired labels. Their complete directories were archived before resumption, and each affected unit was rerun from its frozen seed. These labels never entered the 2,700 canonical trajectories. The budget-sensitivity physical ledger is therefore 811,791 calls: 810,000 canonical evaluations plus 1,791 disclosed interrupted-run calls. The additional calls are excluded from endpoints, convergence curves, and algorithm budgets.

The completed GP-EI performance batch contains 151,200 canonical algorithm evaluations. During interruption recovery, one GP-EI point (evaluation 349 of `gp_ei_f02_d40_i13_r2_b400`) was physically queried a second time because the newer partial journal contained 348 labels while an earlier archive contained 349. The point and returned label matched exactly; the label entered the optimizer history once, so the canonical 400-step trajectory and endpoint are unchanged. The physical GP-EI ledger is therefore 151,201 calls: 151,200 canonical evaluations plus one disclosed recovery-validation call. The extra call is excluded from algorithm budgets, performance curves, and exclusive-cost analysis. The read-only recovery audit made zero objective calls and verified eight recovered trajectories ({recovery['canonical_algorithm_evaluations']:,} canonical evaluations), {recovery['second_generation_saved_labels']:,} saved second-generation labels, and {recovery['second_generation_new_physical_calls']:,} second-generation physical calls, one of which overlaps the earlier archive.

This section does not reverse the failed development benefit gate. CEC confirmation and reliable implementations of the named competitive SAEAs remain absent; the manuscript remains a working evidence record rather than a submission-ready superiority claim.

'''
    return f'''# 13 预定预算性能敏感性

## 13.1 设计与汇总

在预选BBOB五类结构代表（f1、f6、f10、f15、f20）、20/40维、实例17–19和3次重复上，分别以5D、10D、15D总预算独立运行。六种内部配置和四种外部参照共完成2,700运行、810,000次付费评价，未调用诊断标签。每个终点在运行后使用匹配fixed01共同初始化误差作分母；先在函数—实例单元内取3重复中位数，再在函数内平均3实例，最后等权平均5个函数分数。未新增假设检验、置信区间或参数选择。

## 13.2 终点与收敛

数值越低越好。每格为预定层级汇总后的最终log10相对误差均值。

{endpoints}

![预算敏感性终点](../results/budget_performance_sensitivity_report_v1/budget_endpoints.png)

![预算敏感性收敛](../results/budget_performance_sensitivity_report_v1/budget_convergence.png)

每个预算对应独立优化运行；较长预算终点只提供更大总额度下的稳健性证据，并非观察短预算后选择性续跑。有限的五函数、两维度范围及描述性汇总不能建立新的普遍排序。

## 13.3 前缀与信息顺序审计

{prefixes}

不读取总预算的内部核心必须在对应长运行内逐位复现5D与10D前缀；540项规定比较全部通过。外部前缀相同性只记录而不作为门槛，共{external_equal}/360项相同；该数是实现观察，不是验证外部方法的假设。全量审计重放810,000对PRE/LABEL、内部上界与管理状态，并核对7,020个原始文件哈希。内部提议规则没有读取总预算。

## 13.4 恢复调用总账与证据边界

预算敏感性实验中断时留下{budget_recovery['partial_run_count']}个未完成单元，已经物理取得{interrupted_physical:,}个标签。恢复前将其完整目录归档，随后按冻结seed从头重跑受影响单元；这些标签从未进入2,700条规范轨迹。因此预算敏感性物理调用总账为811,791次：810,000次规范评价加1,791次公开的中断运行调用。额外调用不进入终点、收敛曲线或算法预算。

完成后的GP-EI性能批次包含151,200次规范算法评价。中断恢复时，`gp_ei_f02_d40_i13_r2_b400`第349点因新一代部分日志只有348个标签、而更早归档已有349个标签，被再次物理查询。候选点与返回标签完全相同，标签只进入优化历史一次，故规范400步轨迹和终点不变。GP-EI物理调用总账为151,201次：151,200次规范评价加1次公开的恢复验证调用。额外调用不进入算法预算、性能曲线或独占成本分析。只读恢复审计自身零目标调用，核对8条恢复轨迹（{recovery['canonical_algorithm_evaluations']:,}次规范评价）、{recovery['second_generation_saved_labels']:,}个第二代保存标签和{recovery['second_generation_new_physical_calls']:,}次第二代物理调用，其中1次与更早归档重叠。

本节不推翻开发阶段优化收益门槛失败的结论。CEC确认与文中所列关键竞争SAEA的可靠实现仍缺失；本文仍是证据工作稿，不作投稿就绪或普遍优越性声明。

'''


def main():
    audit, hashes, recovery, recovery_hashes, budget_recovery, interrupted_physical = require_complete()
    analysis = ROOT / "results/budget_performance_sensitivity_analysis_v1"
    runs = pd.read_csv(analysis / "runs.csv")
    curves = pd.read_csv(analysis / "convergence.csv")
    prefix = pd.read_csv(analysis / "prefix_checks.csv")
    functions = pd.read_csv(analysis / "function_scores.csv")
    scores = pd.read_csv(analysis / "endpoint_scores.csv")
    assert len(runs) == 2700 and len(curves) == 272700
    assert len(prefix) == 900 and len(functions) == 300 and len(scores) == 60
    assert set(scores.method) == set(ORDER)
    figures(scores, curves)

    sources = [
        ROOT / "paper/english_complete_mechanism_manuscript.md",
        ROOT / "paper/论文完整机制稿.md",
    ]
    assert all(path.exists() for path in sources)
    outputs = []
    for source, english, name in [
        (sources[0], True, "english_budget_complete_manuscript.md"),
        (sources[1], False, "论文预算完整机制稿.md"),
    ]:
        text = source.read_text("utf-8")
        marker = "# 13 Conclusion" if english else "# 13 结论"
        assert text.count(marker) == 1
        text = text.replace(
            marker,
            section(scores, prefix, recovery, budget_recovery, interrupted_physical, english) + ("# 14 Conclusion" if english else "# 14 结论"),
            1,
        )
        if english:
            text = text.replace(
                "budget sensitivity remains a gap; the predefined extension and model/training-cap sensitivity are reported in Sections 11–12.",
                "the predefined extension, model/training-cap sensitivity, and budget-performance sensitivity are reported in Sections 11–13.",
            )
            text = text.replace(
                "GP/background, exclusive cost, and three-task application evidence are complete. Reliable SAEA comparisons remain required; this remains a working manuscript.",
                "GP/background, exclusive cost, three-task application, and prespecified budget-performance evidence are complete. Reliable SAEA comparisons remain required; this remains a working manuscript.",
            )
            text = text.replace(
                "Source, LaTeX and PDF integration still require final visual verification.",
                "Source, LaTeX, and PDF integration have been completed and visually verified for this working manuscript.",
            )
        else:
            text = text.replace(
                "预定扩展与模型/训练截断敏感性见第11–12节；预算性能敏感性仍是缺口。",
                "预定扩展、模型/训练截断敏感性与预算性能敏感性见第11–13节。",
            )
            text = text.replace(
                "完整GP/背景参照、独占成本与三个主要应用的全部预定运行均已完成；预定扩展已在第11节完成；",
                "完整GP/背景参照、独占成本、三个主要应用与预算性能敏感性的全部预定运行均已完成；预定扩展已在第11节完成；",
            )
            text = text.replace(
                "预定300维扩展已完成，关键竞争方法可靠复现仍未完成；",
                "预定300维扩展与预算性能敏感性已完成，最终双语工作稿PDF已逐页视觉核查；关键竞争方法可靠复现仍未完成；",
            )
        now = datetime.now(timezone.utc) + timedelta(hours=8)
        lines = text.splitlines()
        if english:
            lines = [("date: " + now.strftime("%d %B %Y")) if line.startswith("date: ") else line for line in lines]
        else:
            lines = [("date: " + now.strftime("%Y年%m月%d日")) if line.startswith("date: ") else line for line in lines]
        output = ROOT / "paper" / name
        output.write_text("\n".join(lines) + "\n", encoding="utf-8")
        outputs.append(output)

    inputs = [analysis / name for name in [
        "audit.json", "runs.csv", "convergence.csv", "prefix_checks.csv",
        "function_scores.csv", "endpoint_scores.csv", "source_hashes.json",
    ]]
    inputs += [
        ROOT / "docs/frozen_second_recovery_audit_v1/sha256.json",
        ROOT / "results/budget_interruption_20260924_v1/recovery.json",
        Path(__file__),
        *sources,
        *[OUT / f"budget_{kind}.{ext}" for kind in ["endpoints", "convergence"] for ext in ["png", "pdf"]],
        *outputs,
    ]
    inputs += [
        ROOT / "results/budget_interruption_20260924_v1/partial_runs" / relative / "events.jsonl"
        for relative in budget_recovery["partial_runs_archived"]
    ]
    record = {path.relative_to(ROOT).as_posix(): digest(path) for path in inputs}
    record["verified_raw_result_hash_count"] = len(hashes)
    record["verified_recovery_freeze_hash_count"] = len(recovery_hashes)
    (ROOT / "paper/budget_complete_manuscripts_source_hashes.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("Budget-complete bilingual working manuscripts generated; all PDF pages remain to be inspected.", flush=True)


if __name__ == "__main__":
    main()
