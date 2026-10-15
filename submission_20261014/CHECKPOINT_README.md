**最近方法/工程诊断已完成（2026-10-15）：**当前稿定位为认证数值实现与验证研究。经典包络核心已明确归因；228 个案例的 band 与 nominal 索引全部相同，未观察到额外动作挽救。不能据计算加速宣称已达到新优化方法的原创性门槛。最终解释见 `paper/engineering_optimization/contribution_closure_20261015/RESULT_AND_CONTRIBUTION.md`，逐案例与预定例子见 `results/nominal_band_diagnostic_20261015/`。旧输入包需与当前分支更新配合；本轮不生成或上传 PDF/ZIP。

# 当前贡献裁决和可恢复源码

**2026-10-15 更新：**当前科学稿优先阅读
`paper/engineering_optimization/contribution_closure_20261015/RESULT_AND_CONTRIBUTION.md`
和 `submission_20261014/CONTRIBUTION_CHECK_20261015.json`。
当前 TeX 已聚焦整数动作集、优化成对强对照和标量证书路由。下面的 31/37 页
PDF 与旧计时属于早前版本，不能当作本次新稿或新计时结果。根据用户新指示，
不再上传 PDF/ZIP；它们由用户本地保存。当前源码和派生结果保存在同一私有分支。

科研基线保持58f539c2d0738b20c7d0d4889fe8d808a03a3019。本分支是研究与稿件增量，不表示已提交、已录用、已证明优化收益或整个仓库已可公开。

优先阅读 submission_20261014/CONTRIBUTION_DECISION_20261014.md。
当前正文和补充源码在 submission_20261014/source/paper/engineering_optimization/。
本分支保存代码、完整稿件文本及图件、既有计时与本轮零求解诊断的派生表。已渲染核验的正文PDF（31页）和补充PDF（37页）在 submission_20261014/pdf/。当前原始GP ZIP及全部原始/新证书由用户已保存的 Paper_project_closure_20261014.zip 或当前审稿复核附件提供。它不是全原始数据镜像，不替代用户保存的历史大档案。

重建缺少的图（从固定计时记录重建，不重新计时），并从本仓库基线路径恢复其他图：

```sh
python3 -m src.restore_contribution_checkpoint
```

官方 interact.cls、tfcad.bst 不随本增量分发。按 REVIEW_REPRODUCTION.md 使用官方模板。之后在当前源码目录执行 latexmk 编译。作者单位b/c仍待真实信息。

重放新增下界诊断需要本地已有GP数据：把已保存完整结项包恢复为其中记录的工作目录布局，运行 prepare_gp_attachment，再运行 diagnose_h1_bound_bottlenecks。不要调用物理求解或优化入口。

```sh
python3 -m src.prepare_gp_attachment
python3 -m src.diagnose_h1_bound_bottlenecks
python3 -m unittest tests.test_h1_bound_bottlenecks -v
```

配对网格22/25原始文件可用、3份缺失。已有派生表不能补造其响应/时序。两次witness额度已用完，无retry/replacement/新独立优化样本。

公开条件审计和整仓许可证选择不包含在这次私人源码保存中。
