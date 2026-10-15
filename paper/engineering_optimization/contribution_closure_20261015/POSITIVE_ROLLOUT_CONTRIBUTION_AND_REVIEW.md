# 正响应 rollout：本轮实际成果与保存状态

科学基线仍为 `58f539c2d0738b20c7d0d4889fe8d808a03a3019`，本轮输入工作提交为 `5fe178cc9d699670a7776e511cee5b123e146857`。原 Gaussian 结果、物理预算与 H1/H5 门槛不变。

## 已实际完成的算法工作

已实现一个新的、范围明确的优化子问题求解流程：在固定第一动作菜单与原 mean 续跑规则下，选择两次评价后模型期望终端改进接近最优的第一动作。它输出数值选择误差界，超出了原先仅返回可能动作集合的能力；它不等于连续域全局优化或真实工程 regret 证书。

1. 用原超参数的正响应 log-GP 作为规划概率模型，保留所有训练点和原 mean 续跑规则，不重新拟合超参数。
2. 对一个参考续跑动作直接扫描强支配响应区间，先计算固定两点价值，并以区间外概率控制遗漏的响应适应。
3. 当这个界不足以确定第一动作时，只对仍竞争的分支进行完整响应动作投影。
4. 用显式条件价值曲率、固定二进制核 posterior residual bounds、向外 MPFR 特殊函数和积分误差形成选择区间。
5. 单独 reader 检查强支配、平坦 tie、动作域/积分叶片覆盖、重新求和及最终选择。不接受未经检查的 producer flag；对抗 tie 测试会拒绝无效局部证明并回退。

## 数学核心

正响应令终端改进位于 [0,m0]。若续跑动作在 D 内确定为 j，固定两点价值 G 满足

`|V-G| <= m0 * P(first_response outside D)`。

若存在 lower-index rival 在整个正测度区间与 j 平坦并列，仅有非严格不等式不足以保证选择 j，reader 必须拒绝。

对一个动作及同一个 incumbent 分段，令 h=exp(a+b*x)<=m0、mu=c+d*x、k=(log(h)-mu)/sigma。条件收益

`q=m0-h*Phi(-k)-exp(mu+sigma^2/2)*Phi(k-sigma)`，

其二阶导数满足

`|q''| <= m0 * (b^2+d^2+(b-d)^2/(sigma*sqrt(2*pi)))`。

正态加权插值余项、尾界和多动作不确定区与 posterior 参数误差一并封闭。最终检查

`max(0, max_other upper(V)-lower(V_selected)) <= m0/1000000`。

上述一般概率界、插值余项、lognormal EI、区间选择和 inverse residual 都有经典基础；不能拆成独立原创贡献。候选算法贡献在于局部响应稳定性化简、可靠回退与完整数值误差/检查链的集成及实证。未声称世界首次或期刊必然接受。

## 真实计算结果

全部 60 个元数据状态保留：43 个非平凡状态、114 分支、17 个别名状态，均为已观察开发材料。

| 同保证算法 | 接受状态 | 完整投影 | 条件端点计算 | 含 reader 的数值阶段秒数 |
|---|---:|---:|---:|---:|
| 直接完整分区 | 43/43 | 114 | 1724 | 10.529803 |
| 局部稳定性化简 | 43/43 | 25 | 1372 | 10.229626 |

时间为三次旋转顺序、逐状态中位数之和；全部 258 次最终数值运行通过。完整投影减少 78.1%，端点计算减少 20.4%，细化次数反而从 544 增到 646。含单独检查后的速度比只有 1.029，不能宣传大幅或普遍加速。

另有一次 15.76 秒 posterior enclosure 准备成本，以及历史 raw coefficient 形成成本，未混入上述配对数值阶段。此前仅 solver 的 1.103 倍、point-parameter 的 1.152 倍属于不同较弱范围，不能替代最终结果。

43 个训练系统和有限 posterior covariance 均通过 residual/正定性检查。最大参数区间宽度约 5.19e-6（latent units）。86 份保留证书有 2822 个积分叶片；reader 检查 91047 条局部支配约束，全部 228 个 branch/method 区间包含普通高精度 nominal 参考值。reader 与 producer 共享算术和曲率实现，不冒充所有数学层面的独立实现。

## 工程后果仍然混合

所有 checked choices 与冻结的 positive reference 在 43 状态一致，因此可复用已付的原 mean 两步记录。

| 对照第一动作 | 更好 | 平局 | 更差 | 平均柔顺度差 / initial |
|---|---:|---:|---:|---:|
| 原 mean | 1 | 41 | 1 | +0.744% |
| 原 EI | 2 | 40 | 1 | -0.452% |
| 同正响应模型的一步 EI | 1 | 40 | 2 | +1.153% |

正差更差，中位数均为零。不能宣称真实策略优越或独立闭环验证通过。当前可辩护的论文主张是“有数值保证的有限菜单 rollout 求解算法”，而非“已证明更好的物理设计”。

## 保存状态：必须区别计算完成与远端完整备份

**本提交仅保存这个方法/结果汇总及结构化 checkpoint。原始逐状态结果、执行过的源码和本机新稿尚未全部上传。**

本机报 `No space left on device`，连只读文件导出也被 sandbox mount helper 阻断。提权清理请求被当前 Granular 策略自动拒绝；Library 导出同样失败，未形成新的已保存文件。GitHub 连接器仍可用，因此先保存可从已完成工具输出核实的汇总，不编造缺失文件或哈希。工作区内生成文件需要保留，不能据此认定已完成材料备份。

结构化 checkpoint 位于同目录 `POSITIVE_ROLLOUT_REMOTE_CHECKPOINT.json`，明确标注汇总范围、已知源码/证书哈希和未保存项。当前远端主稿仍为先前版本；本机主稿已开始整合新方法，但参考文献整合未完成，不能作为最终可编译稿。

## 范围与计费

本轮新增 43 个 positive reference 根系统和 43 个 posterior enclosure 根系统；三个数值合同比较无额外 GP 构造，共 774 次重复数值求解，不是新的工程样本。此前 raw shortcut 的 172 次、直接 raw value 的 43 次根构造分别保留；这条记录链累计 301 次构造，仍只有 43 个不同非平凡状态。

新增物理评估、bound query、超参数拟合、物理 retry/replacement 和独立 optimization sample 均为 0。两次 witness 仍已耗尽。没有 PDF/ZIP，没有旧 228-case 强比较或完整排除证书重跑，没有 H5 扩展，没有 main 分支修改或公开操作。kernel-function evaluation、统计校准、物理/PDE 误差均未认证；`final_submit_ready=false`。

## 已核查的经典来源

- Lee et al. (2020), Efficient Rollout Strategies for Bayesian Optimization: https://proceedings.mlr.press/v124/lee20a.html
- Ling, Low and Jaillet (2016), epsilon-GPP: https://ojs.aaai.org/index.php/AAAI/article/view/10210
- Watanabe (2024), log-objective EI derivation: https://arxiv.org/abs/2411.18095
- SMAC3 官方 EI 文档: https://automl.github.io/SMAC3/v2.4.1/api/smac/acquisition/function/expected_improvement/
- MPFR 官方引用与正确取整实现基础: https://www.mpfr.org/credit.html

当前已具备具体算法、误差命题和工程状态上的数值验证；对最接近文献的原创性充分程度、跨问题适用性及期刊可接受性仍需审稿判断。不能把小提速或证书数量本身当作创新充分性的证明。
