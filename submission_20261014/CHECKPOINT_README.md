# 当前贡献裁决和可恢复源码

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
