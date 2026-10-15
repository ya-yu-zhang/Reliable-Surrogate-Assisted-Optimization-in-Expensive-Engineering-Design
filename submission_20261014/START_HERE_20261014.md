**最近方法/工程诊断已完成（2026-10-15）：**当前稿定位为认证数值实现与验证研究。经典包络核心已明确归因；228 个案例的 band 与 nominal 索引全部相同，未观察到额外动作挽救。不能据计算加速宣称已达到新优化方法的原创性门槛。最终解释见 `paper/engineering_optimization/contribution_closure_20261015/RESULT_AND_CONTRIBUTION.md`，逐案例与预定例子见 `results/nominal_band_diagnostic_20261015/`。旧输入包需与当前分支更新配合；本轮不生成或上传 PDF/ZIP。

# 10月14日投稿准备包

**2026-10-15 当前版本：**方法与正文已更新，优先阅读
`paper/engineering_optimization/contribution_closure_20261015/RESULT_AND_CONTRIBUTION.md`。
新的强对照结果是过滤约 2.71 倍、三项计算合计约 1.36 倍；标量路由在
142 个非基线分支/域请求上保持判断且动作集回调 0 次。旧 PDF/ZIP 和下面
旧计时描述不代表本次新稿。本轮只保存源码、正文文本和派生结果，不上传 PDF/ZIP。

目标沿用Engineering Optimization。今天已完成稿件与附件准备，未操作期刊门户、未上传至期刊、未取得稿件编号。单位b/c按用户本次选择继续待补，不能将本包标为已具备最终提交的全部条件。

## 本包文件与使用顺序

1. `pdf/Manuscript_for_submission_20261014.pdf`：有署名主稿；贡献聚焦精确系数带包络、闭区间动作集与可复核排除证据。数据可用性声明已修正。
2. `pdf/Supplement_for_submission_20261014.pdf`：补充结果、证明、费用与完整不利结果，新增配对网格保存缺口说明。
3. `pdf/Cover_letter_preparation_20261014.pdf`与`COVER_LETTER.txt`：一页未签署投稿信准备稿。填写事实声明后再使用；未伪造未发表／未投他刊确认。
4. `pdf/Author_information_20261014.pdf`：现有四位作者顺序与通讯作者；b/c明确待补。
5. `pdf/Editorial_evidence_note_20261014.pdf`：给编辑的贡献范围、复核附件和原始证据缺口说明。
6. `Data_and_Code_for_Review_20261014.zip`：供审稿的有限数据与代码包，包含当前GP贡献的完整输入、证书、原执行附件、固定来源与复核程序；包含已恢复的22份配对网格记录及历史分析输出，明确缺少另外3份。
7. `source/paper/engineering_optimization/`：当前投稿准备版TeX、40项文献、图和内联数值表；官方模板资产不在分发包中，按复现说明取得。
8. `ABSTRACT_AND_KEYWORDS.txt`与`PORTAL_FIELDS.json`：可复制的标题、纯文本摘要、五个关键词及现有元数据。空值表示尚未取得事实，不能用占位符冒充真实信息。

## 今天进入系统的实际顺序

从官方期刊页进入“Go to submission site”，核对刊名后开始Research Article草稿；具体门户网址和下拉选项以官方页面为准。该刊官网确认采用单盲审稿，本包保留署名。

填写标题、摘要、关键词和作者；上传主稿、补充、必要图／表及审稿复核包；若门户对ZIP或单文件大小有限制，应使用其允许的补充材料／审稿文件入口。不能把私人GitHub链接当作审稿访问权限。作者单位b/c和必要事实字段未补齐时，先保存系统草稿。

预览系统生成PDF，确认作者顺序、图表、公式和引用；核对实际投稿要求及事实声明后才进入最终提交。这份文件不表示上述门户操作已经发生。

## 当前需要完成的事实与适用性事项

- **作者单位b/c**：用户选择继续待补。Zhenyu Meng和Jia Zhao的实际机构、城市、国家仍需真实信息。
- **事实声明**：资助、利益冲突和CRediT沿用原稿记录，未被本次独立证实；是否已有发表、是否投其他期刊尚未提供。未发起被用户排除的全作者批准任务。
- **AI政策适用性**：现行T&F官网不允许AI生成稿件／章节首稿或创建、完成文章论证。本项目已披露论证撰写等辅助；这里没有将其改写成仅语言润色，也不认证合规。研究和材料制作已按用户要求继续完成，实际目标刊投稿的适用性问题仍需解决。
- **配对网格原始证据**：当前22/25份已哈希核对；缺少最终恢复作业的events.jsonl、responses.json、run_status.json。三个历史输出可审查，但完整原始日志重放暂不可完成。稿件与给编辑的说明已披露，不能承诺缺失文件可以按需提供。
- **刊物细则**：已核实范围、创新要求与单盲审稿；完整作者须知网页访问受限，字数／页数上限及附件限制尚未获得可靠正文。不能把未核实项目记为已通过。

## 审稿人角度的验收结论

贡献有可执行对象和实测增量：同一冻结系数带、同一228个动作集与独立证据复查下，构造阶段约3.19倍、含另行证明复查约2.62倍改善。经典包络几何并非新发现，未比较所有优化库；H1没有新增判断、H5与完整部署节省均未实现。这些范围已经写入论文，录用或充分原创性由期刊同行评议决定。

历史表格、失败门槛、55,309次物理尝试账本和既有种子组均保留。本轮新增物理评估0次，不重试／替换witness，不新增独立优化样本。唯一当前科研基线仍是58f539c2d0738b20c7d0d4889fe8d808a03a3019。已保存的早前Paper_project_closure_20261014.zip不被覆盖，本包是其投稿准备增量。

官方来源（2026-10-14核对）：

- 期刊范围、单盲审稿及官方入口：https://www.tandfonline.com/journals/geno20
- 作者须知入口：https://www.tandfonline.com/action/authorSubmission?show=instructions&journalCode=geno20
- AI规则：https://authorservices.taylorandfrancis.com/editorial-policies/using-ai-in-your-research-and-manuscript-preparations/
- 一页投稿信与事实声明：https://authorservices.taylorandfrancis.com/publishing-your-research/making-your-submission/writing-a-journal-article-cover-letter/
- 投稿文件检查：https://authorservices.taylorandfrancis.com/publishing-your-research/making-your-submission/article-submission-checklist/
