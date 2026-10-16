# 正文与补充材料六项深查及修订 — 2026-10-16

本轮以私有工作分支提交 `b62366e13d4f71fb30b5b149c090bb717f3ee802` 为编辑起点，科学基线仍为 `58f539c2d0738b20c7d0d4889fe8d808a03a3019`。当前活动正文、补充材料及递归输入共18份TeX文件已检查。没有追加实验、物理评估、bound query、拟合、retry、replacement或独立优化样本；没有生成、打包或上传PDF/ZIP。

## 1. 第一人称与句式

摘要和引言的两处“We develop”已改为被动表述。对展开后的正文、补充材料检查，英语第一人称代词匹配为0。数学指标、单位阵符号和两处I/O缩写保留，不作为第一人称处理。方法与结果改用明确的计算对象和操作描述，避免将所有无生命主语句机械改为被动句。摘要、投稿字段和单独摘要文本同步为142词。

## 2. AI检测要求

未运行AI检测，未将私有稿件发送至检测网站，不能将“低于10%”标成完成或保证结果。修订依据是研究事实、论证清晰度、具体机制及图文一致性，不以检测分数指导措辞，也未隐去实际AI协助披露。Turnitin的[官方说明](https://guides.turnitin.com/hc/en-us/articles/28294949544717-AI-writing-detection-model)将低于20%的输出作特殊显示，不能由此核验精确的10%阈值。论文质量与检测分数分别记录。

## 3. 贡献优势与EO scope

EO的[官方scope](https://www.tandfonline.com/journals/geno20/about-this-journal)强调优化创新与工程适用性。引言已明确算法如何将未解析延续区域的剩余收益纳入停止准则，在完整延续分区尚未构造时认证首动作选择。工程段落明确了定体积密度参数化、柔度目标，以及下一次有限元评价所对应的可行设计选择。

证据支持的优势是：有限菜单下带模型值遗憾保证的选择、按需构造条件后验、跨策略切换的分段误差处理，以及从清理训练输入开始的梁设计决策计算。区域界的单元操作640→585、条件后验161→157与两条路线各43/43认证结果保持原值。12.23秒对10.73秒的耗时增加和既有物理结果混合仍保留。没有改写为物理优化效果更优、加速或节省物理评价；期刊接收与创新充分性不被保证。

## 4. 标题与方法命名

标题保持“Local Response Stability for Certified Two-Step Rollout in Engineering Optimization”，其中无new或novel。活动正文、补充材料中没有novel/novelty或“new method/algorithm/pruner”等自我评价。旧包络段落的“new pruner”“new exact intervals”和v2程序措辞已改为具体对象名称。历史“new FE calls”“new points”等计数用于区分额外评价，予以保留。

## 5. 图文对应

现有14张图逐张只读渲染检查，并核对原绘图程序的统计量和坐标定义；14份PDF哈希均未变化。各图细节已补入图注或相邻正文。

| 图 | 检查和修订 |
| --- | --- |
| S1 | Stack colors, declaration totals, dimension panels and the meaning of a zero bar. |
| S2 | Selected/pool/top-predicted colors and the horizontal 0.1 reference line. |
| S3 | Signed selected-minus-pool differences and zero line; removed unsupported nearest-zero wording. |
| S4 | T/ST colors, actual checkpoint order, support threshold 20 and plateau patterns. |
| S5 | Full log-relative-error quantity, normalization, aggregation hierarchy and method colors. |
| S6 | Seconds, modeled nonobjective time + Bc, linear/log horizontal sections and logarithmic vertical axis; removed unsupported intersection claim. |
| S7 | Task-specific logarithmic raw-loss scales, median points and interquartile bars; distinguished dispersion from confidence intervals. |
| S8 | Median curves, interquartile shading and internal initialization fractions 0.28/0.44/0.76; corrected description of the DNA timing. |
| S9 | 300 dimensions, 20 runs, logarithmic raw-loss axis and median/interquartile endpoints. |
| S10 | Logarithmic median raw loss, 1,000 paid evaluations and the 62% internal initialization; corrected early CMA-ES versus later TuRBO-1 trajectory attribution. |
| S11 | Interquartile boxes, median lines, 1.5-IQR whiskers, omitted outliers and variant settings. |
| S12 | Budget/D values, dimension panels, hierarchical aggregation and interpretation of connecting segments. |
| S13 | Rows, columns, panel-specific paid-budget fractions and absolute-order prefix comparisons. No initialization reference line is asserted. |
| S14 | Force-position panels, postinitial pilot-step axis, percentage improvement, policy colors and different plateau timings. |

实质性纠错包括：S10早期下降对应CMA-ES，TuRBO-1主要下降发生在较后预算；S3随机池并非每个维度都最接近零；S6没有用于划定成本区间的交点标记；S8的DNA变化应结合其长初始化解释。图S5、S6现有长纵轴标签有截断，完整量纲及单位已写进图注；图形标签的重新导出仍需在最终排版时处理，本轮未改动PDF。

## 6. 官方LaTeX模板

主文使用`\documentclass[]{interact}`，补充材料使用`\documentclass[suppldata]{interact}`，参考文献调用`tfcad`。本地`interact.cls`与`tfcad.bst`的SHA-256均与既有[出版方官方Interact-CAD包](https://files.taylorandfrancis.com/InteractCADLaTeX.zip)记录一致。没有采用第三方仿制模板，也没有修改出版方类文件。

[出版方模板说明](https://authorservices.taylorandfrancis.com/publishing-your-research/writing-your-paper/formatting-and-templates/)要求按具体期刊作者指南确认模板适用性。EO作者指南端点本轮仍返回403，因此“官方出版方模板来源已核验”和“EO当前专属要求已全部核验”分别记录。当前运行环境缺少article.cls，本轮只做源文件与BibTeX检查，没有编译当前论文或宣称最终版式通过。模板二进制文件未上传到仓库。

当前还需提供Zhenyu Meng和Jia Zhao的完整单位、安排实际审稿材料访问，并完成上述最终模板适用性及版式检查。现有209文件公开数值清单与许可证范围不受本轮文字修订影响；私有仓库可见性没有改变。`final_submit_ready`保持false，表示这些明确事项尚未完成。
