# Two-witness diagnosis 与 GP reachability 开发结果

执行基线：[main 的 58f539c2d0738b20c7d0d4889fe8d808a03a3019](https://github.com/ya-yu-zhang/Reliable-Surrogate-Assisted-Optimization-in-Expensive-Engineering-Design/commit/58f539c2d0738b20c7d0d4889fe8d808a03a3019)。

**研究决定：不进入新的独立优化实验。** 两个 witness 显示点界偏松；GP 可达集合显著缩小并提高联合下界，但没有新增 H1 分类或选择认证，没有已验证的完整成本收益，也没有 H5 reachable-history extension。独立研究门槛未通过，`submission_ready=false`。

## Preflight 与执行边界

已阅读 README、work_status、physical-bound screen 的结果与 next gate、冻结 GP 协议、配置、plan、相关源码及 unit-test record。先完成只读 preflight，再执行物理诊断。204 个冻结来源哈希、两个 witness 的元数据排序选点、坐标、point key、Sobol 池与根平局门槛均通过核验。诊断前结果目录只有原始 `plan.json`，两个 witness 均未读真值。

通过仓库的无损归档恢复了 83 个 budget records 和 96 个 common-continuation records，全部哈希一致，恢复新增物理调用为 0。已有 physical-bound screen 的输出和两次参考求解作为冻结输入保留；本轮复用已存 trial-space Gram 数据构造下一步全池对照，没有运行旧 screen 的求解或分析入口。

本机 Python 3.12.14、NumPy 2.3.5、SciPy 1.17.0、scikit-learn 1.8.0、EngiBench 0.2.0、CVXOPT 1.3.2。冻结 plan 记录 NumPy 2.5.3、SciPy 1.18.1；差异如实保留。三个物理引擎源码哈希和声明的 Sobol 池哈希一致，未将旧实验改标为当前环境重跑结果。

## 两个 witness 的 true-response diagnosis

按冻结入口执行一次，两个 witness 各求解一次，网格均为已有 100×50 离散目标。

| 数据 / 固定 state | 已存二维试验下界 | 根平局所需下界 | 真响应 | 相对平衡残差 |
|---|---:|---:|---:|---:|
| archived_common_mean / gp_ei_shared_init_r0_t101 | 232.5285149112 | 2872.9449164865 | 14324.7435408532 | 1.06776e-10 |
| previous_holdout / beam_holdout_r11_ei | 200.5953747176 | 1420.9406735824 | 9639.9247638608 | 5.55836e-11 |

两次残差均通过预定 1e-5 门槛。点界分别只有真响应的 1.6233% 和 2.0809%；两处真响应均高于根平局门槛，因此支持“试验点界偏松”，不能以这两个真响应否决整个 full-pool superset，也不能由此认定扩大位移基足够修复全池。

物理尝试 **2/2**，剩余 **0**；失败、retry、replacement、recovery、新增独立样本、新增 optimization samples 均为 **0**。项目累计物理尝试从 **55,307** 增至 **55,309**。GP 阶段新增物理尝试为 **0**。

原 runner 在结果行中继承了 plan 的 `witness_true_response_read=false` 冻结前标记。原始日志未改写；实际已读真值由两条 `true_response` 事件、`witness_status.complete=true` 和 `diagnosis.json` 的 `current_true_response_read=true` 记录。

## GP reachable action set 开发分析

全部既有完整组作为开发数据保留，未重新称为独立验证。60 个 metadata states 全部保留；17 个动作别名状态按预声明规则不做边界工作，43 个非平凡 mean contexts 共 114 个 distinct first-action branches。

构造只读取不含后续响应的 initial plans：初始 X/y、固定 theta/alpha、first-action 坐标和源特定 step-1 Sobol pool。全部 114 分支、两种响应范围的动作集合及哈希持久化完成后，才读取既有 first/next responses 进行 grading。没有 refit kernel hyperparameters。

| 数据 | 保留的完整种子组 / metadata states | 有非平凡状态的组 | 非平凡 states / branches | 每个 1024 点池保留动作（最小 / 中位 / 最大） | 实际 next-action 包含 |
|---|---:|---:|---:|---:|---:|
| archived_common_mean | 10 / 30 | 10 | 26 / 72 | 2 / 4 / 7 | 72/72 |
| previous_holdout | 10 / 30 | 6 | 17 / 42 | 2 / 3 / 6 | 42/42 |

上表两种冻结响应范围的汇总相同：`[0,infinity)` 和 `[pending trial lower,infinity)`。此前 holdout 的四个仅含别名状态的组仍保留在输入、metadata 和 exclusions 中；原 `summary.csv` 的 `seed_groups` 是非平凡状态贡献组数。

逆矩阵残差门槛失败 0；未解决排除 0；来源初始/下一步预测复现 flags 为 0，当前 native argmin 也全部被包含。两个范围共 **232,564** 个排除证明在构造时核验，并在 JSON 序列化后再次核验通过。每条证明与二进制系数区间、可行响应区间和保留索引均存于 `construction/`。

两个读取器使用完全相同的点界和 pending-point 下界，并进行 within-state exact cache sharing。H1 目标严格为“first action + 一步 mean continuation”，使用同一 H1 horizon 的已付费完成 baseline endpoint；不作为 H5 认证。

| 数据 | 全池联合下界 / initial 的中位数 | 可达集联合下界 / initial 的中位数 | 新增非基线 H1 分类 | 新增基线选择认证 |
|---|---:|---:|---:|---:|
| archived_common_mean | 5.9786% | 11.3742% | 0/46 | 0/26 |
| previous_holdout | 9.2066% | 20.1462% | 0/25 | 0/17 |

全部 114 分支的 next-point envelope 与 joint two-response lower 均提高，但 71 个非基线对照在两个读取器下仍全部 abstain。已存响应下区间有效、没有分类错误；这不提供新的工程误差认证。

三个读取器在选择未认证时均回退至已付费 baseline，H1 之后新增 selected-completion requests 为 0。开发数据上的平均 / 最大选择损失（占 initial 的百分比）为旧共同数据 **1.7312% / 31.5694%**、此前 holdout **0 / 0**；全池与两个 GP 读取器完全相同。该描述性损失不是独立验证或选择证书。

## 完整成本与研究门槛

本比较实际取得完整全池边界库：**44,146** 个 state/design 边界请求及 2×2 reduced-system attempts，低于冻结 45,000 上限。边界库覆盖 43×1024 个下一步候选点及 114 个 pending points。旧参考位移和 Gram 仅复用，没有新增参考求解。

| 读取器 | 逻辑边界请求 | 按 state/design 缓存后的请求 | 缓存命中 |
|---|---:|---:|---:|
| 同信息全池 strong comparator | 116,850 | 44,146 | 72,704 |
| GP / nonnegative | 568 | 498 | 70 |
| GP / trial_lower | 568 | 498 | 70 |

GP 子集请求数是 **离线反事实账**。本轮实际支付了全池边界库成本及额外 GP/证明成本，不能称为已经实现的部署节省。

本机记录：pool construction 0.063456 秒；density mapping 87.252092 秒；point-bound evaluation 61.769262 秒；pending-bound 总计 0.398821 秒（属于前述点界时间的子集）；GP kernel construction 0.245046 秒；系数区间及 outer-set construction 21.019126 秒；独立 rational recheck 4.000773 秒。构造总计 176.433648 秒；grading 总计 5.936882 秒，其中 native-GP replay 0.710110 秒、序列化后证明核验 4.115163 秒。两次 witness 物理求解共 0.281339 秒。环境准备、来源恢复、单元测试与交付验证另计；这些时间不构成跨机器或工业提速证据。

发展阶段 rational infeasibility 调用共 697,692 次：outer-set 内部检查、构造重检和序列化后重检各 232,564 次。固定核系统构造 114 次、native replay conditioning 228 次，hyperparameter fit 为 0。验证了 228 条历史 first/next response 记录，GP 阶段未新增 oracle labels。

独立实验 gate：

| 条件 | 结果 |
|---|---|
| 已存真实动作、来源预测及证明核验 | 通过 |
| 有用的新增下游分类或选择判断 | 未通过 |
| 相对同信息 strong comparator 的完整成本收益 | 未通过 |
| 原 H5 目标的 reachable-history extension | 未实现 |
| 开启新独立优化实验 | **否** |

上述对象是给定二进制 kernel matrix 的固定核后验均值外集。没有认证 transcendental kernel error、每个可能 z 的 native floating prediction error、PDE/mesh error 或原工程收益门槛；没有迁移到 EI/PI、hyperparameter refit 或任意更长自适应历史。摘要、旧标签、旧统计家族和工程优势主张未升级。

## 复核记录与交付

原核心 11 项测试加执行层 6 项测试共 **17 项通过**。交付核验检查了 204 个冻结来源、43 个 construction record hashes、原 witness journal 与执行源码哈希、物理/边界账本和 gate；交付核验新增物理调用与 bound queries 均为 0。

复核包含完整 witness 日志、两种范围的 construction/coefficients/exclusion proofs、CSV、analysis/review/diagnosis JSON、更新的 work_status、执行层源码与单元测试。基线 config、PROTOCOL 与 plan 保持冻结内容。

GitHub 自动审批拒绝发布新代码和研究结果，原因是本次请求授权分析而没有明确授权发布生成的研究内容。没有新内容提交；已创建的研究分支 `research/gp-reachability-20261013-c5d11c` 仍指向指定基线，main 也仍为指定 SHA。本交付包提供可审阅的完整增量。
