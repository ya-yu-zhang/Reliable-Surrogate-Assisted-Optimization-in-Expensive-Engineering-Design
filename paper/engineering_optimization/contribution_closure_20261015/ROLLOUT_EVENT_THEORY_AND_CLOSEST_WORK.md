# 响应事件 rollout 候选：推导与最近方法关口

本记录针对 `MINIMAL_NEW_OPTIMIZATION_METHOD_PLAN.md`，不是已经成立的新优化方法声明。唯一科学基线仍为 58f539c2d0738b20c7d0d4889fe8d808a03a3019。

## 推导

固定根状态概率模型、第一动作 a、指定第二步规则 pi(z) 和参考动作 j0。令 Z 的密度为 p，条件边缘 Y_i|Z=z 为 N(mu_i(z),sigma_i^2)。不要求 pi 是根状态模型下的最优第二步规则；它可以采用原先重新归一化的 mean 更新，但不能将其内部预测分布与根状态联合分布混同。

定义 f_z(y)=m0-min(m0,z,y)。对任意 y,y'，|f_z(y)-f_z(y')|<=|y-y'|。用共同标准正态 W 耦合两个条件边缘，得到

    |E[f_z(Y_i)]-E[f_z(Y_j0)]|
       <= E|mu_i(z)-mu_j0(z)+(sigma_i-sigma_j0)W|
       <= |mu_i(z)-mu_j0(z)|+sqrt(2/pi)|sigma_i-sigma_j0|.

若 R_i 包含所有满足 pi(z)=i 的响应，则以指示函数分解 V-G、再用三角不等式及非负性，可得

    |V-G| <= sum_{i!=j0} integral_{R_i}
             (|mu_i(z)-mu_j0(z)|+sqrt(2/pi)|sigma_i-sigma_j0|)p(z) dz.

重叠区间只使该界更保守。仿射均值差的绝对值可以在零点分段。若 Z~N(m,s^2)，线性项的积分为

    integral_l^u (alpha+beta*z)p(z)dz
       =(alpha+beta*m)(Phi(U)-Phi(L))+beta*s*(phi(L)-phi(U)),

其中 L=(l-m)/s，U=(u-m)/s。端点无穷使用相应极限。方差为零的点质量需单独处理，不能使用除以 s 的公式。

完整高斯支持包含负响应，必须覆盖正负两半轴。本次以 t=-z 变换复用原整数区间算法得到负半轴集合；没有擅自截断负概率。来源系数带保障的是指定二进制 GP 选择规则，不能扩展成物理保证或所有 native floating predictions 的保证。

若将来得到可靠的 V 上下界，lower(V_a*)>=max_a upper(V_a)-delta 可推出 V_a*>=max_a V_a-delta。这是标准区间比较结论，不单独作为创新。候选创新必须来自事件界计算机制、与最接近算法的区别及实际计算收益。

本推导说明候选不等式有效，但不说明其在工程状态上足够紧，也不证明首次性。下面的可行性筛查使用普通浮点，未实现向外高斯概率/积分/协方差封闭，因此没有输出数值误差证书。

## 原始来源核查及差异

| 原始研究 | 已有内容 | 对本候选的限制与仍可区分的对象 |
|---|---|---|
| Frazier, Powell, Dayanik (2009)，KG 与作者软件 | 仿射包络及相应期望计算 | 原包络几何不能重算创新；候选 V 包含第二次实际评价而非仅未来 posterior mean |
| Lee et al. (2020)，UAI，方法与 policy-search 部分 | rollout、QMC/控制变量、有限策略选择、基于既有条件的期望改进结论 | rollout 或有限菜单本身不新；本候选拟用声明的动作事件界控制近似，尚无有用实现证据 |
| Jiang et al.，BINOCULARS 作者稿，§2.2/§3/§5 | batch-informed 序贯设计、最优 adaptive/batch 价值关系 | 不能称为首次 batch 简化。指定 mean 续跑不必优于固定 j0，因此必须用双侧误差界 |
| Ling, Low, Jaillet (2016)，AAAI/作者稿，§3、Theorems 2/3、Appendix H | Lipschitz 型观测区间近似及带 epsilon 保证的 anytime GP 规划 | 一般 epsilon 保证、尾部控制与 branch-and-bound 已有。候选仅能主张按指定 mean 选择事件构造的专门误差界，不能宣称首次认证非近视优化 |

这些对象与本候选的精确输出合同不完全相同，但“不同合同”本身不能认证足够新颖性。一般 Lipschitz 耦合、区间支配和标准积分也不能分别当作创新。当前可推导的专门界没有通过工程可行性关口，因此不进入整套新方法实现或改写主贡献。

原始来源：

- KG：DOI 10.1287/ijoc.1080.0314；软件 DOI 10.1287/ijoc.1080.0314.cd。
- Lee et al.：https://proceedings.mlr.press/v124/lee20a/lee20a.pdf
- BINOCULARS 作者稿：https://arxiv.org/html/1909.04568v3
- Ling et al. 作者稿：https://arxiv.org/pdf/1511.06890 ，正式页 https://ojs.aaai.org/index.php/AAAI/article/view/10210
- MPFR 官方文档：https://www.mpfr.org/mpfr-current/mpfr.html 。环境有 libmpfr.so.6；没有因本关口失败而继续开发数值封闭层。

没有转存或分发上述第三方论文 PDF。
