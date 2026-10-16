# 正文与补充材料六项深查及修订 — 2026-10-16

本轮以私有工作分支提交 `b62366e13d4f71fb30b5b149c090bb717f3ee802` 为编辑起点，科学基线仍为 `58f539c2d0738b20c7d0d4889fe8d808a03a3019`。当前活动正文、补充材料及递归输入共18份TeX文件已检查。没有追加实验、物理评估、bound query、拟合、retry、replacement或独立优化样本；没有生成、打包或上传PDF/ZIP。

## 1. 第一人称与句式

摘要和引言的两处“We develop”已改为被动表述。对展开后的正文、补充材料检查，英语第一人称代词匹配为0。数学指标、单位阵符号和两处I/O缩写保留，不作为第一人称处理。方法与结果改用明确的计算对象和操作描述，避免将所有无生命主语句机械改为被动句。摘要、投稿字段和单独摘要文本同步为150词。

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

[出版方模板说明](https://authorservices.taylorandfrancis.com/publishing-your-research/writing-your-paper/formatting-and-templates/)要求按具体期刊作者指南确认模板适用性。EO作者指南网页端点仍返回403；本轮用户提供的2026-06-19作者指南副本已补齐首次投稿要求，明确允许format-free与LaTeX，不要求EO专属模板。当前运行环境缺少article.cls，尚未编译当前论文或宣称最终版式通过。模板二进制文件未上传到仓库。

当前还需提供Zhenyu Meng和Jia Zhao的完整单位、指南明确要求的机构联系方式，安排实际材料访问，套用官方投稿信模板并准备最终提交文件。现有209文件公开数值清单与许可证范围不受本轮文字修订影响；私有仓库可见性没有改变。`final_submit_ready`保持false，表示这些明确事项尚未完成。

## 按用户提供的完整scope复核

2026年10月16日再次读取[EO官网](https://www.tandfonline.com/journals/geno20/about-this-journal)，检索全文与用户提供的scope一致。期刊明确覆盖数值优化、决策支持、统计决策理论和理论研究；scope没有将耗时加速或工程终值优越性列为每篇论文的必备结果。因此，本项目的范围匹配围绕具体的数值优化决策贡献判断，耗时与物理终值按实际证据报告。

当前核心技术贡献表述为：在同一个模型值遗憾停止准则下，联合安排局部动作身份认证、条件后验查询和收益积分，以未计算区域的剩余收益界完成有限首动作菜单的选择。正响应补全下的选择保证与跨策略切换的分段误差分析支撑这一算法。MBB梁的定体积参数化、柔度目标和下一次可行设计评价明确了工程决策对象；43个已有状态的清理输入及冻结配对计算提供实现证据。

投稿信已据此重写算法贡献与期刊范围的连接。贡献评估中将“scope匹配”“技术命题及实现证据成立”和“相对已有工作的创新强度判断”分别记录，不再把缺少耗时或物理效果优势直接等同于scope不符。全文、数值结果及优先权结论没有因期刊scope而加强；没有新增实验。官方scope已核对不等于作者指南、LaTeX专属要求或最终版式已经核验。

## 用户提供的作者指南：实际需要修改的项目

附件为2026年6月19日更新的EO作者指南。它补齐了网页403时未能读取的具体要求，不能继续把这些内容整体标作未知。

| 要求 | 当前处理 |
| --- | --- |
| 官方投稿信模板及三项必填内容 | 已按机构联系信息、scope关联、贡献声明三类准备草稿；官方Google文档模板的正文无法通过网页读取，未冒称已完成原模板套用。 |
| 每位作者的机构邮箱和机构主页 | Chu的机构邮箱已填；其余3个机构邮箱、4个机构主页URL待补，Meng/Zhao两位作者的单位仍缺。未猜测身份或联系方式。 |
| 贡献声明不超过100词 | 独立声明已写入CONTRIBUTION_STATEMENT.txt并嵌入投稿信，共78词，集中说明算法机制、选择保证和工程应用。 |
| 非结构式150词摘要、3至5个关键词 | 摘要由142词修订为150词，补入已有定体积约束事实；5个关键词保留，投稿字段同步。 |
| 标出篇幅，通常不超过7000词（含表、参考文献、图注） | LaTeX展开后通过Pandoc/citeproc作源文本估算，正文含表及所引参考文献3352词，含摘要/题名等元数据共3517词；题名页标注约3520词，数学记号未计入。这不是PDF版面计数。 |
| 首次投稿format-free | 指南明确允许LaTeX及一致的参考文献格式，文内放表图亦可。保留官方出版方Interact-CAD；不再将EO专属模板核验列为首次投稿阻碍。 |
| 生成式AI使用声明、利益冲突声明 | 已为现有真实AI协助披露使用独立节标题；利益冲突节改为Disclosure Statement，事实内容不变。 |
| 数据声明和按合理请求共享 | 已在数据声明补充通讯作者的访问请求联系方式；该政策不要求直接公开整个私有Git历史。已准备的209文件公开数值清单保持不变。 |
| 图像与可访问性 | 14图的图文细节已核对；作者自供alt text为可选项，不增加无必要任务。S5/S6图内轴标签截断仍需最终图形输出时修正。 |
| LaTeX实际提交文件 | 指南要求生成的稿件PDF及源文件ZIP。按用户本轮约束未生成、打包或上传；这些是实际提交时所需文件，不能标为已完成。 |

主贡献继续围绕可认证首动作优化算法展开，不因本次合规检查新增实验或加强结果。当前需要作者补充的事实为机构联系信息及两位作者单位；官方投稿信模板最终套用和实际提交文件准备仍未执行。论文并未因format-free而免除必要材料要求。无需加入视频摘要、图文摘要或新的敏感性实验。
