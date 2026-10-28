# Decision-consequence auditing for surrogate-assisted optimization in expensive engineering design

**ARTICLE**

**Shu-Chuan Chu**$^{1,2}$, **Ya-Yu Zhang**$^1$, **Zhenyu Meng**$^3$, **Jia Zhao**$^4$ and **Jeng-Shyang Pan**$^{1,2,*}$

1 School of Computer Science, Nanjing University of Information Science and Technology, Nanjing 210044, Jiangsu, China  
2 School of Artificial Intelligence/School of Future Technology, Nanjing University of Information Science and Technology, Nanjing 210044, Jiangsu, China  
3 School of Computer Science and Mathematics, Fujian University of Technology, Fuzhou 350118, China  
4 School of Information Engineering, Jiangxi University of Water Resources and Electric Power, Nanchang 330099, China  
* Corresponding Author: Jeng-Shyang Pan. Email: 100112@nuist.edu.cn  
Shu-Chuan Chu. Email: 100130@nuist.edu.cn  
Ya-Yu Zhang. Email: 202412492223@nuist.edu.cn  
Zhenyu Meng. Email: zy.meng@fjut.edu.cn  
Jia Zhao. Email: zhaojia@juwp.edu.cn  
Jeng-Shyang Pan. Email: 100112@nuist.edu.cn  
ORCID: Shu-Chuan Chu, 0000-0003-2117-0618; Ya-Yu Zhang, 0009-0001-2272-4654; Zhenyu Meng, 0000-0002-1466-8082; Jia Zhao, 0000-0002-3652-1903; Jeng-Shyang Pan, 0000-0002-3128-9025

## Abstract

Surrogate-assisted optimization spends its budget on which engineering simulation is evaluated next. Error diagnostics often look fine while search actions stay redundant or harmful, so paid solves yield little design gain. The process increment is a decision-consequence audit that asks whether an evaluation is justified before release. Calibration, selected-design change and immediate utility, and closed-loop improvement are scored apart. Exact decision equivalence gives the smallest extra simulation count: a frozen 120-state beam intervention is reported from 138 finite-element solves instead of 480. A post-hoc rule returns one promotion, one stop, and one held-for-revision verdict; thresholds are illustrative. PEM-T is the adversarial case: a near-calibrated temporal residual monitor that fails the optimization-benefit gate, yet the audit can block that decision-useless signal before it burns finite-element budget. In a 200-evaluation beam study, GP-PI, DRSO, and TuRBO-1 reduce median compliance by 51.7%, 74.7%, and 75.1%, whereas GP-EI and fixed-multiplier GP-UCB do not.

**Keywords:** expensive engineering optimization; surrogate model management; decision auditing; evaluation allocation; finite-element design

Word count: 9291 words, inclusive of tables, references and figure captions.

## 1 Introduction

Many engineering optimization problems hang on simulations, model training, or experiments. Those evaluations often dominate the computational or physical budget. Surrogate-assisted evolutionary algorithms and Bayesian optimization cut the load by fitting a cheap predictor and choosing which candidate gets the next exact evaluation (Jin 2011; Jin et al. 2019; Jones, Schonlau, and Welch 1998; Li, Zhan, and Zhang 2022; Liang et al. 2025). Model management turns prediction into an acquisition or management decision, spends a paid evaluation, and folds the label into the optimization state. Only then does a reliable predictor improve budget use.

Simulation-based engineering design makes the gap tangible. A monitoring signal can redirect finite-element analyses and still leave structural performance flat, even when aggregate error looks satisfactory. Predictive accuracy and optimization utility can diverge. On expensive workflows that split is an operational risk: teams may pour simulation budget into candidates from a well-calibrated yet decision-redundant surrogate system. Reliable regional Kriging search has tied uncertainty to restricted regions and infill decisions (Suprayitno and Yu 2019). Diagnostic benchmarking has shown standard-test and real-application algorithm behavior can differ (Zatarain Salazar et al. 2025). Both push inspection of the path from surrogate information to paid engineering evaluations. The beam study here stays inside a constrained design family. Materials, manufacturing, robotics, and neural architecture search remain motivation, not validated applications.

Uncertainty, ensembles, local models, temporal signals, and adaptive infill all appear in methods that trade exploitation against exploration (H. Liu et al. 2025; Q. Liu et al. 2021; Ma et al. 2025; L. Yu et al. 2026; Zhou et al. 2025; Zou et al. 2025). Online and conformal calibration ask whether predictive bounds keep intended reliability under sequential selection (Deshpande, Marx, and Kuleshov 2024; Jin and Ren 2025; Kim et al. 2025; Nardone et al. 2026). Passing a calibration check is not enough. It does not prove that a signal reorders candidates, picks a better design at a fixed state, or improves a closed-loop trajectory after the surrogate adapts. Those decision-pathway claims need separate tests.

PEM-T, the prediction-error-monitoring prototype, is an adversarial controller for the audit. Its residual monitor hits a near-target calibration signal. Yet an algebraically redundant exploitation term sits in the decision pathway and steers spatial exploration the wrong way. The failure is useful, not ornamental. At a common-state layer the audit can catch that pattern before a large closed-loop finite-element budget is spent. Nothing in the procedure depends on PEM-T alone. Any surrogate, candidate generator, monitoring signal, and acquisition or model-management rule can be inspected if its path to paid evaluations is recorded.

What follows is a decision-support audit with records. It states the evidence—and its cost—needed before a surrogate-management claim counts as an engineering improvement. Four elements follow.

1. An allocation rule for exact decision reporting: policies that select the same exact point in the same deterministic objective context share one response, and Proposition 1 gives the worst-case minimum query count. The implementation collapses 480 GP control-state choices through 261 within-state distinct choices to 138 additional finite-element calls, so the same report costs 138 paid solves instead of 480, and no exact procedure uses fewer queries.
2. An executable audit separates structural decision influence, frozen-state intervention effects, finite-horizon policy performance, and complete physical-call cost. Each stage returns an explicit evidence object and an unsupported-claim boundary, so prediction quality is never substituted for optimization value.
3. A recorded-verdict layer applies one declared promotion rule to three frozen acquisition rules, returning one promotion, one stop and one held-for-revision verdict. Written after those records existed, its thresholds are illustrative and separate from the prespecified optimization-benefit gate (failed by the residual monitor). Prediction-before-label records, fixed information boundaries and the paid-call ledger keep every verdict auditable; the elementary additive-ranking invariant is a screening case, not the mathematical contribution.
4. Beyond the residual-monitor case, a frozen 120-state GP acquisition intervention and twenty transfer cases under two previously untested beam load positions test actionable rules and longer horizons. They distinguish zero first-step gain from later policy improvement and quantify the performance loss and extra cost hidden by an unqualified claim of cheaper strategy selection.

Algorithm 1 lays out the audit steps and required evidence. What is contributed is an implemented intervention-and-verification method for surrogate-management mechanisms; no acquisition function or universally superior strategy selector is introduced. Section 2.3 situates the evidence objects; Sections 6.3-6.5 add the GP evidence. Each stage returns a costed verdict, so teams that must justify simulation spend before releasing a batch of solves have an explicit promote, revise, or stop point.

Reliability, as used here, means credibility and utility of surrogate-management decisions. It does not mean reliability-based design optimization with structural failure probabilities or probabilistic safety constraints.

Bounds on the claims are strict. The empirical residual quantile is not a conformal coverage theorem, false-discovery guarantee, regret bound, or universally effective high-dimensional method. Findings concern a deterministic single-objective setting, the stated surrogate and candidate process, and the tested budgets. This is a structured test procedure. It does not imply that candidate-dependent uncertainty, expected improvement, confidence bounds, restarts, stopping rules, or uncertainty-aware optimization in general are ineffective.

## 2 Related Work

### 2.1 Surrogate-assisted optimization and model management

Surrogate-assisted evolutionary algorithms (SAEAs) and Bayesian optimization reduce the evaluation burden of expensive black-box simulations (Jin 2011; Jin et al. 2019; Jones, Schonlau, and Welch 1998; Li, Zhan, and Zhang 2022; Liang et al. 2025). Model management converts predictions into sampling or selection decisions. Early work combined approximate fitness with generation-based control (Jones, Schonlau, and Welch 1998; Ong, Nair, and Keane 2003). Committee-based active learning (H. Wang, Jin, and Doherty 2017) and cooperative swarm SAEAs for high-dimensional problems (Sun et al. 2017) extended that line. Later designs introduced boosting Gaussian-process uncertainty (Zou et al. 2025), large-scale lower-confidence-bound models with diversity search (Ma et al. 2025), and relation models that retain unevaluated population information (DRSO) (Hao, Zhang, and Zhou 2024), consistent with evidence that unevaluated solutions can remain valuable under expensive budgets (Hao, Zhang, and Zhou 2025). Hierarchical surrogate evaluation appears in adjacent settings such as neural architecture search (X. Liu, Bao, and Leng 2025). Grouping multilayer-perceptron with sparse Gaussian-process SAEAs targets expensive multiobjective problems (Pan, Peng, et al. 2026). Parallel comparisons of Bayesian, evolutionary, and hybrid solvers under wall-clock limits show that model-management choices interact with time-constrained workflows (Gobert et al. 2024). The same paradigms already appear in multi-objective robotic linkage design (Ibrayev et al. 2024), laser-welding parameter selection (Z. Wang et al. 2025), and multi-UAV path planning (R.-Y. Wang et al. 2026). Hanawa, Harada, and Miura (2025) showed that prediction accuracy affects preselection, individual-based, and generation-based management unevenly. Surrogate information therefore needs a check at the decision layer: it is valuable only when it guides paid physical evaluations.

### 2.2 Reliability quantification and operational benchmarking

Bayesian optimization has incorporated online calibration through updated predictive distributions (Deshpande, Marx, and Kuleshov 2024), localized online conformal thresholds (Kim et al. 2025), and selection-conditional coverage under explicit exchangeability conditions (Jin and Ren 2025). Temporal conformal prediction has also been considered in surrogate-assisted evolutionary optimization (Nardone et al. 2026). Table 1 summarizes the scope: these approaches primarily guarantee marginal or localized coverage. Meeting a coverage guarantee does not by itself imply optimization utility or trajectory improvement after the surrogate adapts. Diagnostic benchmarking (Zatarain Salazar et al. 2025) evaluates cross-application runtime dynamics. Two-step lookahead optimizes short model-based horizons (Wu and Frazier 2019). Neither isolates counterfactual choices at a fixed learned state. The costed validation protocol used here makes the decision pathway falsifiable before expensive solvers are released.

**Table 1. Scope of representative reliability and model-management approaches.**

| Approach | Primary quantity assessed | Direct decision question | Closed-loop consequence required |
|---|---|---|---|
| Gaussian-process uncertainty | Predictive confidence | Does uncertainty modify an acquisition value? | Usually evaluated by optimizer performance |
| Conformal prediction | Marginal or localized coverage | Does a calibrated set or bound satisfy its stated guarantee? | Not implied by coverage alone |
| Adaptive infill | Evaluation selection | Which candidate receives the next expensive label? | Evaluated through search performance |
| Candidate-dependent SAEA management | Ranking, region, or population update | Does surrogate information change the search action? | Method-specific |
| Relation-model DRSO | Pairwise fitness/category relations and unevaluated population | Does evolutionary surrogate management preserve promising search information? | Evaluated by paid-budget endpoint |
| Decision-consequence audit | Calibration, decision influence, utility, and final outcome | Does the signal change a paid decision and make it more useful? | Required as the final audit level |

### 2.3 Operational distinction from existing model management and selection

Reliable regional Kriging supplies variance-guided regions and adaptive infill (Suprayitno and Yu 2019). Other surrogate-management frameworks can provide convergence guarantees under their assumptions (Booker et al. 1999). The method here does not replace those rules or inherit their guarantees. It evaluates the route from an existing rule to a paid action and the evidence needed to justify that route. Hanawa, Harada, and Miura (2025) vary pseudo-surrogate accuracy across management strategies; the intervention below holds a learned GP state fixed and varies only the acquisition rule. Algorithm selection and trajectory warm-starting address a complementary problem (Kostovska et al. 2022; Kuş et al. 2024). The reusable technical object is the frozen decision record together with its equivalence classes, response ledger, and subsequent validation record. What is claimed is a diagnostic procedure, not an optimizer: outputs are verdicts with stated evidence and cost, and the only performance claims are the measured ones reported below.

**Table 2. Relation to representative prior work and the evidence object added here.**

| Representative work | Reported focus | Operational evidence in the present implementation |
|---|---|---|
| Reliable regional Kriging (Suprayitno and Yu 2019) | Variance-guided reliable regions and sequential infill | Exact chosen-action equivalence and separate intervention labels at a frozen state |
| Surrogate management (Booker et al. 1999) | Managing approximation models with convergence analysis | An evidence audit without inheriting an optimizer's convergence guarantee |
| Adjustable-accuracy management study (Hanawa, Harada, and Miura 2025) | Search response to controlled pseudo-surrogate accuracy | Fixed learned posterior, identical candidate pool, and acquisition-only intervention |
| Diagnostic benchmarking (Zatarain Salazar et al. 2025) | Effectiveness, efficiency, reliability, and runtime dynamics across real applications | Mechanism-level decision effects connected to separate closed-loop outcomes |
| Two-step lookahead (Wu and Frazier 2019) | Model-based expected future improvement for choosing evaluations | Recorded first actions followed by actual responses under a declared common continuation |
| Frugal selection (Kuş et al. 2024) and trajectory warm-starting (Kostovska et al. 2022) | Selection data cost and reuse of search information | Independent pilot-to-validation transfer, exact paid ledger, and explicit endpoint/cost boundaries |

## 3 Decision-Consequence Auditing Framework for Surrogate-Assisted Model Management

### 3.1 Optimization system and information boundary

A deterministic objective f(x) is minimized over a bounded continuous domain under budget B. At evaluation t, the labeled history contains only observations acquired before t. A surrogate fitted to that history supplies predictions for a candidate set, while a monitoring signal and model-management rule determine which candidate, region, evaluation gate, restart, or stopping action is used. The audit treats the full chain from surrogate output to paid evaluation as its object of analysis.

Before the objective is called, a prediction-before-label journal stores the candidate set or its reproducible identifier, selected point, surrogate outputs, monitoring signal, incumbent, decision mode, support indicators, and random-state identifiers. The record is flushed before the label is obtained. Labels acquired solely for frozen-state diagnostics remain separate and never return to the optimizer. This boundary prevents outcome information from leaking into the decision being audited.

The role of the framework in a surrogate-assisted optimization loop is shown in Figure 1.

![Decision-consequence auditing framework for surrogate-assisted optimization.](../results/framework_audit_v1/decision_consequence_framework.png)

Figure 1 arranges the loop as six stages read from left to right: expensive engineering problem, surrogate model, monitoring or uncertainty signal, model-management decision, expensive evaluation and optimization outcome, with a return arrow that carries the updated archive and search state back to the surrogate model. Three annotation arrows connect the audit band beneath the chain to the stage each level interrogates, calibration to the monitoring signal, decision influence and utility to the model-management decision, and closed-loop consequence to the optimization outcome. Calibration therefore assesses the signal the optimizer encounters; decision analysis tests whether that signal changes a choice and improves common-state utility; closed-loop validation measures the final consequence after histories diverge.

### 3.2 Decision pathways and ranking invariance

A monitoring mechanism can affect optimization through candidate-specific ranking, an evaluation gate, a restart or stopping rule, a change of search region or population, or a stochastic exploration controller. The first audit step identifies at least one such path before additional expensive experiments are authorized.

**Lemma 1 (ranking invariance under a candidate-independent additive correction).** At evaluation t, suppose two rules receive an identical indexed candidate set, use deterministic and identical tie-breaking, and are evaluated in exact arithmetic. If every supported candidate shares the same additive correction $c_t$, then minimizing $H_t(x)=\mu_t(x)+c_t$ returns the same minimizer index as minimizing $\mu_t(x)$.

**Proof.** For any indexed candidates $x_i$ and $x_j$, $H_t(x_i)-H_t(x_j)=\mu_t(x_i)-\mu_t(x_j)$. Every strict comparison and exact tie is therefore preserved under the stated tie-breaking rule. The same indexed minimizer follows. ∎

**Corollary 1.** If two configurations also share initialization, candidate generation, exploration decisions, all random streams and stochastic operators, numerical precision, and optimizer-state updates, and differ only by replacing the common-correction minimizer with the mean minimizer, their trajectories are identical by induction over evaluations. Finite-precision agreement is an implementation property and is checked separately in the experiment audit.

This result identifies a structural limitation of candidate-independent corrections; it does not invalidate uncertainty-aware surrogate management in general. Candidate-dependent posterior uncertainty, expected improvement, lower-confidence bounds, support-dependent rules, evaluation gates, restarts, and stopping policies may create decision paths that Lemma 1 does not remove.

### 3.3 Three audit levels and promotion gate

Common-history calibration fits the same frozen model and candidate pool, then evaluates monitoring losses and failures without updating the search. Common-state decision analysis compares the action with and without the mechanism at the same state; when actions differ, separate diagnostic labels measure true one-step utility. Independent closed-loop experiments then allow each policy to update its own history and evaluate final optimization behavior. One-step improvement diagnoses immediate exploitation value but is not a necessary condition for useful exploration. A lower immediate gain therefore identifies a need for delayed-value assessment rather than, by itself, grounds for stopping an exploration mechanism. The following procedure clarifies the interpretation of audit stages; it does not retrospectively alter any frozen experimental protocol or statistical comparison.

**Algorithm 1. Decision-consequence audit for a surrogate-assisted model-management mechanism.**

**Step 1 — Specify.** Freeze the surrogate, candidate generator, monitoring signal, management or acquisition rule, expensive objective, budget, and deterministic replay information. Output: protocol and information boundary.

**Step 2 — Trace.** Follow the signal through ranking, evaluation, region, population, restart, stopping, or stochastic-exploration decisions. Gate: at least one candidate-dependent or otherwise actionable path.

**Step 3 — Record and calibrate.** Persist every decision before its label. If the mechanism makes a calibrated-error claim, assess that claim on appropriately separated diagnostic data. Gate: an intact information boundary and evidence supporting the stated claim. Mechanisms that make no calibration claim are not required to pass a coverage test.

**Step 4 — Test common-state utility.** Freeze optimization states and candidate pools, compare baseline and mechanism actions, and label only the prespecified diagnostic alternatives. Report decision-change frequency and immediate utility. For exploration, region, restart, or stopping mechanisms, prespecify a delayed-value assessment where needed. Gate: an identifiable decision consequence and sufficient evidence to justify the next diagnostic expenditure; lower one-step improvement alone does not reject exploration.

**Step 5 — Validate the closed loop.** Run independent optimization on held-out instances or engineering conditions under matched optimizer budgets, including when exploration requires a delayed-value test. Record diagnostic calls separately and include them in any deployment-cost comparison. Output: final objective consequence and total cost boundary.

**Step 6 — Decide.** Promote, revise, stop, or retain an inconclusive decision using prespecified outcome tolerances and cost limits. Report the first unsupported claim and the evidence needed to resolve it. Promotion requires closed-loop evidence for the intended engineering use. Output: stage-wise audit record.

The framework can return a positive result, and does so on recorded data. Classical GP acquisition is a candidate-dependent positive control because both its predicted improvement and its uncertainty vary across candidates, so it can change ranking and passes the structural decision-influence check; passing that first check does not guarantee superior endpoints, it authorizes empirical utility and closed-loop evaluation. Section 6.4 applies a promotion rule written after the records existed and reports one promotion, one stop and one held-for-revision verdict. That reading is retrospective. The prespecified optimization-benefit gate for the residual monitor remains unmet.

### 3.4 Diagnostic cost and scope of deployment claims

The optimization budget and the audit budget are different quantities. The total physical-call cost includes additional optimizer evaluations, diagnostic evaluations, and recovery or verification calls; previously paid deterministic labels reused from an archive are identified separately. A comparison of optimizer endpoints at equal budgets does not establish that the audit itself saves evaluations.

The independent internal validation uses 907,200 optimization evaluations and 1,990,656 additional diagnostic labels. Those full-pool diagnostics support mechanism analysis on inexpensive benchmark functions, but are not proposed as the default screening cost for expensive engineering simulations. A bounded engineering audit should prespecify states, label the union of selected alternatives where possible, and stop or report inconclusive when its diagnostic limit is reached. Any claim of net savings must compare the audited workflow with a prespecified unaudited workflow, including diagnostic overhead. Section 6.5 reports a complete paid-workflow comparison with endpoint losses; it does not establish performance-preserving net savings.

### 3.5 Decision equivalence and the minimum immediate diagnostic budget

For a frozen state $s$, let $a_j(s)$ be the exact point selected by policy j and let $c$ identify the deterministic objective context: simulator, physical condition, parameterization, and numerical configuration. Policies are immediately decision-equivalent when they select the same bitwise point under the same $c$. This is a local relation. Equivalent first actions do not make later policies equivalent, and labels must not be reused across changed physical conditions or noisy objectives without an additional justification.

Let $X$ be the union of distinct context-point pairs selected by all prespecified states and policies, and let $A$ contain the exact responses that the auditor is permitted to reuse after decisions have been frozen. For incumbent $m_s$ and fixed positive scale $v_s$, the reported immediate utility is $u_j(s)=\max(0,m_s-f_c(a_j(s)))/v_s$. The additional deterministic query requirement is

**Diagnostic query requirement:** *N*diag = |*X* − *A*|.

**Proposition 1 (minimum worst-case immediate diagnostic queries).** Suppose the objective is an unrestricted deterministic oracle, all selected points and incumbents are frozen, and each unqueried response can independently lie on either side of at least one associated incumbent while all other responses remain fixed. Querying each member of $X$ outside $A$ once suffices to report every immediate utility. In the worst case, fewer queries cannot determine all utilities exactly.

**Proof.** Sufficiency follows by assigning the same exact response to every context-point equivalence class and reusing only permitted responses. For necessity, consider an unqueried member *x* in a class with incumbent *m*. Two objectives can agree on all available and queried responses while taking values *m* − δ and *m* + δ at *x* for δ > 0 (δ < *m* for a positive objective); the resulting utilities differ. No procedure using only those shared observations can distinguish them. For a finite set of distinct points, disjoint smooth local interpolants can realize these assignments, so smoothness alone does not remove the ambiguity. Querying each undetermined member resolves it. A certified response bound or a restricted physical objective class may reduce this worst-case requirement; no such additional exact inference is used here. ∎

The proposition is an allocation rule for a specified exact diagnostic report, not a lower bound on all possible optimization audits. It does not prove that the queries improve search. Section 6.3 illustrates both the within-state equivalence reduction and the additional reduction from permitted source-response and diagnostic-cache reuse. The source label at a frozen original action is consulted only after the intervention choices are fixed; it never enters the predecision GP fit. All thresholds for a deployment decision must still be fixed for the intended engineering use before its validation outcomes are observed. The added transfer study supplies descriptive evidence, not a retrospectively chosen promotion threshold.

## 4 Experimental Design

### 4.1 Audited monitor prototype and internal optimizer

A temporal residual monitor serves as the representative audited mechanism. For a selected candidate $x_t$, the monitor records the standardized prediction residual $r_t$. It then constructs a temporal upper value bound $H_t(x)=\mu_t(x)+s_t q_t(x)$, where $q_t(x)$ is the nonnegative weighted 0.9 quantile of recent historical residuals. The prediction-error-monitoring prototype with temporal weighting (PEM-T) converts these tracking signals and evaluation-stagnation flags into a dynamic exploration probability in $[0.1, 0.8]$. When exploring, PEM-T selects the candidate with the largest minimum distance to the archive; otherwise it uses the common-correction upper value $H_t(x)$ when an improvement declaration is available and the monitor is not alarmed, and the predicted mean $\mu_t(x)$ in the remaining cases. By Lemma 1, the exploitation rankings of the upper-value and mean modes are algebraically identical under a candidate-independent correction. A fixed-exploration control retains the same model and candidate process with exploration probability 0.1.

The internal search engine uses a regularized Gaussian radial-basis-function (RBF) surrogate. Initialization size and the candidate-generation protocol follow Section S0.2; differential-evolution crossover families are surveyed by Pan, Chen, et al. (2026).

### 4.2 Independent validation suites and reference baselines

The empirical gate evaluation is split into a development phase and an independent validation phase to enforce strict information boundaries. Development uses eight Black-Box Optimization Benchmarking (BBOB) functions ($D\in\{10,20\}$) across three instances to screen internal configurations against a fixed-exploration control. The budget is $10D$. Failure of the required gate prevents any optimization-superiority claim.

Following the development gate, the unchanged configurations are frozen and evaluated on a separated validation suite comprising all 24 noiseless BBOB functions in dimensions 10, 20, and 40. This independent batch generates 3,888 runs and 907,200 post-initialization evaluations. Trajectory performance is quantified using the base-10 logarithm of final error relative to common initialization error, with numerical flooring at $10^{-12}$. Matched random streams, nine prespecified Holm-adjusted contrasts, and paired hierarchical bootstrap intervals are detailed in Section S2.

Standard Sobol sampling, CMA-ES, classical Gaussian-process expected improvement (GP-EI), and trust-region Bayesian optimization (TuRBO-1) provide budget-matched descriptive references (Eriksson et al. 2019). For the finite-element beam application (Section 6), the baseline family is augmented by the relation-model-assisted SAEA (DRSO) (Hao, Zhang, and Zhou 2024), GP probability of improvement (GP-PI), and GP upper confidence bound (GP-UCB) operating on identical initial archives to isolate selection-level causal effects. Three LassoBench tasks provide application transfer under fixed data and splits (Sehic et al. 2022). The BBOB implementation and reporting follow the Comparing Continuous Optimizers (COCO) framework (Hansen et al. 2021). Complete tables, the 300-dimensional extension, resource measurements, sensitivity studies, and file-level audits appear in the Supplementary Materials.

## 5 Mechanism Results

### 5.1 Development gate and implementation invariants

All 1,872 development optimization runs and 432 common-history runs complete without exceptions. PEM-T and the configuration that removes its upper-value mode have identical trajectories in all 144 matched pairs. Temporal monitoring with fixed 0.3 management likewise matches fixed 0.3 mixing in all 144 pairs. These are implementation confirmations of Lemma 1 and Corollary 1, rather than independent effective components.

The development-selected control is fixed 0.1. PEM-T is worse on all eight development functions in both dimensions. Its function-weighted log-relative endpoint difference is +0.2831 in D=10 and +0.1810 in D=20, where positive values favor fixed 0.1. The required optimization-benefit gate is therefore unmet before the independent validation begins.

### 5.2 Independent endpoint and immediate decision effects

Table 3 reports the nine prespecified validation comparisons. PEM-T increases final relative error in all three dimensions. The base-10 differences correspond to geometric error ratios of 1.468, 1.258, and 1.159 for dimensions 10, 20, and 40. The effect decreases with dimension but remains in the unfavorable direction for 60 of 72 function-level comparisons. Common-state feedback decisions also have lower true immediate improvement than mean-greedy decisions in every dimension.

**Table 3. Prespecified independent validation contrasts. Endpoint values above zero favor fixed 0.1; immediate values below zero favor mean-greedy selection. History-interaction values are selected-point minus pool failure differences, so positive values mean the policy's selected points fail more often than its own candidate pool. Direction counts give positive and negative repeat-level outcomes; the denominator is 24 for the endpoint and history-interaction rows and 19, 21 and 21 for the immediate-improvement rows, where exact ties are excluded.**

| Dimension | Contrast | Estimate | 95% bootstrap interval | Direction count | Holm p |
|---:|---|---:|---:|---:|---:|
| 10 | PEM-T minus fixed 0.1 endpoint | 0.1668 | [0.0749, 0.2391] | 22 positive, 2 negative | 5.36e-6 |
| 20 | PEM-T minus fixed 0.1 endpoint | 0.0998 | [0.0467, 0.1905] | 19 positive, 5 negative | 0.00170 |
| 40 | PEM-T minus fixed 0.1 endpoint | 0.0639 | [0.0130, 0.1123] | 19 positive, 5 negative | 0.00170 |
| 10 | History interaction (selected minus pool failure) | 0.0851 | [0.0311, 0.1234] | 20 positive, 4 negative | 0.00149 |
| 20 | History interaction (selected minus pool failure) | 0.1225 | [0.0696, 0.1948] | 21 positive, 3 negative | 0.00065 |
| 40 | History interaction (selected minus pool failure) | 0.1449 | [0.0941, 0.2244] | 17 positive, 7 negative | 0.00170 |
| 10 | Feedback minus mean immediate improvement | -0.0170 | [-0.0431, -0.0067] | 1 positive, 18 negative | 0.00078 |
| 20 | Feedback minus mean immediate improvement | -0.0158 | [-0.0352, -0.0079] | 0 positive, 21 negative | 0.00048 |
| 40 | Feedback minus mean immediate improvement | -0.0344 | [-0.0630, -0.0100] | 1 positive, 20 negative | 0.00048 |

The nine contrasts and the 72 function-level contrasts they aggregate are released with the retained validation records (see Data availability). The function-level distribution underlying the aggregate endpoint contrasts is shown in Figure 2.

![Function-level endpoint effects in the independent BBOB validation. Positive values indicate larger PEM-T errors.](../results/mechanism_validation_report_v1/endpoint_function_effects.png)

Figure 2 displays all 24 function-level effects separately for each dimension rather than only the suite average. Each panel covers functions 1 to 24 on the horizontal axis against the difference in base-10 log-relative error on the vertical axis; bars above the zero line are drawn in orange and the few below it in blue. Most bars lie above the zero line: 22 of 24 in dimension 10 and 19 of 24 in both dimensions 20 and 40. The few negative bars show that the result is not pointwise uniform, while the shrinking bar heights across panels agree with the smaller aggregate effect at higher dimension. The conclusion is therefore based on a broad directional pattern with disclosed exceptions, not on one dominant benchmark function.

### 5.3 Calibration does not identify optimization utility

PEM-T explores 39.7%, 36.4%, and 34.4% of post-initialization evaluations in dimensions 10, 20, and 40, compared with approximately 10% for fixed 0.1. Its observed selected-point upper-bound failure fractions are 0.1008, 0.0942, and 0.0964, close to the nominal monitoring level. Nevertheless, its endpoints and common-state decisions are worse. A near-target aggregate failure fraction therefore does not imply efficient budget allocation. This empirical divergence validates the core thesis of the audit: standard validation metrics are insufficient to license deployment, and common-state decision auditing is required to safeguard expensive engineering pipelines against well-calibrated but counterproductive search heuristics.

Improvement declarations provide a second example. PEM-T makes 31, 34, and 155 declarations across the three dimensions; 20, 27, and 30 are false. The corresponding pooled false-declaration fractions are 0.645, 0.794, and 0.194. A one-sided failure rate near 0.1 cannot control the conditional error among the small subset declared to improve the incumbent.

History also changes the object being monitored. Under fixed 0.3 mixing, selected-point failures exceed pool failures, whereas under greedy histories the relationship reverses. The prespecified interaction is positive in all three dimensions (0.0851, 0.1225 and 0.1449) and passes Holm adjustment (p=0.00149, 0.00065 and 0.00170; Table 3). Selection-induced differences should therefore be attributed to the coupled history and policy, not treated as a universal direction of undercoverage.

The reversal of selected-point and pool failure differences across frozen history policies is shown in Figure 3.

![Selected-point minus pool failure differences under frozen history policies.](../results/mechanism_validation_report_v1/history_object_differences.png)

Figure 3 makes the history dependence visible. Each panel, one per dimension, plots the selected-point minus pool failure fraction on the vertical axis for the three frozen history policies on the horizontal axis, and the zero line marks identical failure fractions for the two monitored objects. Fixed 0.3 histories place the selected-point failure fraction above the pool value in all three dimensions, whereas greedy histories place it below the pool value. Random-pool histories remain closer to zero and are negative in each panel. Because the sign changes with the policy that generated the frozen state, a single universal “selection penalty” would misrepresent the monitored process.

Spatial-temporal weighting lowers selected-point quantile loss in the prespecified diagnostic comparisons, yet its closed-loop endpoint remains worse than fixed 0.1 in each dimension. This is the central empirical separation: a better residual estimate can still direct evaluations toward candidates with low optimization value.


To isolate the evidential role of each audit stage, a stage-omission ablation is constructed from the frozen records. Unlike an optimizer-component ablation, omitting an audit stage does not alter the evaluated trajectory; it removes the corresponding basis for inference. Table 4 states the strongest conclusion still supported at each stopping point and the evidence that would be lost.

**Table 4. Stage-omission ablation and the resulting loss of evidence.**

| Available audit evidence | Apparent conclusion for the representative monitor | Information lost if the audit stops here |
|---|---|---|
| Calibration only | Selected-point failure is close to 0.1 and may appear satisfactory. | No evidence that exploitation ranking changes or that selected actions are useful. |
| Calibration plus ordering analysis | The temporal additive correction is exploitation-redundant; feedback can act through exploration. | The utility of the changed exploration decisions remains unknown. |
| Ordering plus common-state utility | Feedback changes actions, but those actions have lower immediate improvement than mean-greedy choices. | Delayed effects after histories diverge remain untested. |
| Full audit including closed loop | The controller does not pass the held-out optimization-benefit gate under the tested budgets. | No omitted audit stage is used to claim deployment value. |

This evidence ablation uses the same frozen results rather than rerunning a modified optimizer because the ablated objects are inferential stages rather than search operators. It shows why a calibration-only assessment would have produced an incomplete reliability conclusion, why algebraic pathway analysis can identify redundancy without additional objective calls, and why common-state and closed-loop evidence answer distinct questions.

## 6 Engineering Application: Surrogate-Assisted Structural Optimization

### 6.1 Problem and parameterization

EngiBench Beams2D v1 supplies a density-based finite-element model of the right half of a symmetric Messerschmitt-Bolkow-Blohm beam (Felten et al. 2025). Surrogate-assisted evolutionary optimization has previously been developed for expensive structural design (M. Yu, Li, and Liang 2020), and uncertainty-guided reliable-region search has been studied for expensive engineering optimization (Suprayitno and Yu 2019). Here, the beam provides engineering application validation of the audit framework within an expensive structural optimization workflow. The domain uses 100 by 50 bilinear elements. Horizontal degrees of freedom along the left symmetry boundary are fixed, the lower-right vertical degree of freedom is supported, and a unit downward load is applied at the top-left of the modeled half-beam. The material interpolation uses minimum stiffness 10^-9, unit maximum stiffness, penalization power 3, and Poisson ratio 0.3. The objective is structural compliance; lower values are better.

Direct optimization of all 5,000 element densities is outside the studied surrogate's budget and initialization regime. A constrained engineering family is defined in which 19 effective logits plus one fixed anchor form a 4 by 5 coarse field. Cubic interpolation expands the field to 50 by 100 elements. A scalar logistic shift is solved by bisection so that every design has mean density 0.35. The study therefore evaluates model management within this smooth 19-dimensional design family rather than claiming general topology-optimization performance.

### 6.2 Application protocol and audit results

Before formal labels, five methods, ten repeats, and 200 evaluations per run are frozen. The first batch keeps the native 38-point initialization of GP-EI and TuRBO-1 while Greedy, fixed 0.1, and PEM-T share a 58-point initialization. A prespecified sensitivity batch then reruns GP-EI and TuRBO-1 from exactly the same 58 points and deterministic labels as the internal methods. Two acquisition controls, GP-PI and GP-UCB, and the author-code DRSO SAEA are subsequently run from the same archive. Their subsequent searches retain their stated acquisition, trust-region, relation-model, evolutionary, and candidate-generation rules. The original 50 trajectories contain 10,000 paid finite-element evaluations. The five shared-initialization external controls add 10,000 algorithm-budget observations, reuse 2,900 initial labels, and make 7,100 additional finite-element calls. All 100 trajectories finish without failure or exact duplicate points. Independent endpoint diagnostics reproduce the original GP-EI and TuRBO-1 sensitivity endpoints within a maximum relative difference of 6.23e-12; event-level audits accept every GP-PI, GP-UCB, and DRSO trajectory.

The first and third quartiles are denoted by Q1 and Q3, respectively, in Table 5.

**Table 5. Finite-element endpoint compliance over ten optimization repeats.**

| Method | Median | Q1 | Q3 | Median improvement after shared initialization |
|---|---:|---:|---:|---:|
| Greedy | 1445.1 | 1300.8 | 1694.9 | 0.362 |
| fixed 0.1 | 1435.6 | 1354.2 | 1580.7 | 0.383 |
| PEM-T | 1972.8 | 1759.3 | 2168.9 | 0.251 |
| GP-EI | 2308.5 | 1989.4 | 2464.5 | 0.000 |
| GP-PI | 1233.1 | 921.2 | 1399.7 | 0.517 |
| GP-UCB | 2308.7 | 2223.8 | 2827.3 | 0.000 |
| DRSO | 647.4 | 580.4 | 780.0 | 0.747 |
| TuRBO-1 | 574.0 | 534.7 | 665.3 | 0.751 |

PEM-T minus fixed 0.1 has median paired compliance difference +488.7, with interquartile range +134.7 to +814.7; PEM-T is better in two repeats and worse in eight. These and the differences below are medians of the ten repeat-matched endpoint differences, not differences between the medians in Table 5; the repeat-level endpoints and all seven contrasts are released with the other measured records (see Data availability). The corresponding comparison with greedy has median difference +575.2 and the same direction count. Under matched initialization, GP-EI minus PEM-T has median difference +242.8; GP-EI is better once, tied three times, and worse six times (paired Wilcoxon Holm-adjusted p=0.0469). Within the three added-control family, GP-PI minus PEM-T has median difference -876.1 and nine wins (Holm-adjusted p=0.0117), GP-UCB has median difference +574.6 with two wins, two ties, and six losses (p=0.0391), and DRSO has median difference -1334.6 with nine wins and one loss (p=0.0117). TuRBO-1 minus PEM-T has median difference -1372.3 and is better in all ten repeats (Holm-adjusted p=0.00391 in the original sensitivity family). Changing from native to shared initialization produces no supported endpoint shift for GP-EI (Holm-adjusted p=0.320) or TuRBO-1 (p=0.695). The application therefore distinguishes a weak acquisition setting from successful Bayesian, evolutionary-surrogate, and trust-region controls under the same starting evidence.

The shared-initialization finite-element trajectories and their between-repeat dispersion are shown in Figure 4.

![Median and interquartile best-so-far finite-element compliance under a shared 58-point initialization; the dashed line marks the end of initialization.](../results/engineering_beam_drso_shared_init_v1/complete_shared_initialization_convergence.png)

Figure 4 separates the common initialization from method-specific search. Best compliance so far is plotted on a logarithmic vertical axis spanning 10^3 to 10^5, the horizontal axis counts finite-element evaluations up to 200, and the dashed vertical line marks the end of the 58-point initialization. One curve and one shaded interquartile band are drawn for each of the eight methods; the control is labelled Fixed-0.1 in the legend. All curves share the same values up to the dashed boundary. TuRBO-1 and DRSO then improve rapidly and reach the lowest endpoint group. GP-PI also produces sustained improvement and finishes below the three internal methods, whereas GP-EI and GP-UCB show little median improvement after initialization. Greedy and fixed 0.1 improve more gradually and remain below PEM-T near the endpoint. The shaded interquartile bands preserve between-repeat variability and show that the endpoint ordering is not produced by a single trajectory.

Representative endpoint density fields for all eight shared-initialization methods are shown on the common material-density scale in Figure 5.

![Representative median-run density fields for all eight methods under the shared-initialization comparison.](../results/engineering_beam_drso_shared_init_v1/complete_representative_designs.png)

Figure 5 shows the median-endpoint design from every method on the common density scale. Each panel is one method, labelled with the representative repeat and that repeat's endpoint compliance, and the grey scale on the right maps element density from 0 in white to 1 in black. Because every field satisfies the same mean-density constraint, the contrast concerns material placement rather than material quantity. TuRBO-1 and DRSO form concentrated high-density load paths and reach the lowest compliance group. GP-PI produces a stronger structural path than GP-EI or GP-UCB, whose diffuse fields remain close to their initial designs. The visual differences are consistent with the convergence pathways and endpoint ordering in Table 5.

### 6.3 Frozen-state intervention on GP acquisition policies

To test the audit beyond the residual controller, thirty archived Gaussian-process expected-improvement (GP-EI), GP probability-of-improvement (GP-PI), and GP upper-confidence-bound (GP-UCB) histories supply ten repeats per source policy. The states immediately before evaluations 59, 101, 151 and 200 are frozen, giving 120 interventions. Every fit uses only earlier labels. Logged automatic-relevance-determination (ARD) Matérn-5/2 parameters are replayed without refitting; all source-action means and standard deviations agree within the prespecified absolute and relative tolerance of 1e-8. Mean prediction, expected improvement (EI), probability of improvement (PI), and lower confidence bound (LCB) act on a shared 4,096-point Sobol pool augmented by the frozen source action. Here EI has zero improvement margin, PI uses 0.01 times training standard deviation, and LCB uses kappa=2. No intervention response is fed back into a source optimizer.

The 480 policy-state choices contain 261 distinct within-state actions. After choices have been frozen, 120 original action responses are legitimately reused; three further responses come from identical context-point pairs already evaluated in the diagnostic ledger. The audit therefore acquires 138 additional finite-element (FE) labels. A separate solver-compatibility check incurs 102 attempts, including an initial 42-call check whose numerical tolerance was found too strict. The final 60 retained comparisons pass the disclosed 1e-6 solver-relative tolerance, with maximum relative difference 4.929e-8. The 1e-8 GP replay tolerance is unchanged. Input hashes and choices were committed before additional diagnostic acquisition; see S9 for the archive transfer and verification boundary.

**Table 6. Acquisition-only intervention at frozen GP states. Results are means over ten repeat-level summaries, each averaging four checkpoints. U=max(0,training incumbent minus diagnostic compliance)/training standard deviation. Utility and paired differences are displayed in units of 1e-6; action-change percentages are relative to mean selection.**

| Frozen source | Control | Changed (%) | Mean U (1e-6) | Delta U vs mean (1e-6) |
| --- | --- | --- | --- | --- |
| EI history | EI | 30.0 | 0.899669 | +0.000000 |
| EI history | PI | 25.0 | 0.899669 | +0.000000 |
| EI history | LCB | 52.5 | 0.000000 | -0.899669 |
| PI history | EI | 95.0 | 0.000000 | -0.347088 |
| PI history | PI | 7.5 | 0.347088 | +0.000000 |
| PI history | LCB | 97.5 | 0.000000 | -0.347088 |
| UCB history | EI | 30.0 | 0.887232 | +0.009475 |
| UCB history | PI | 35.0 | 1.178882 | +0.301124 |
| UCB history | LCB | 75.0 | 0.511893 | -0.365864 |

LCB often changes the selected point yet has negative mean immediate-utility differences in all three source-history groups. EI and PI effects depend on the state-generating history; a different choice does not automatically provide immediate gain. The small normalized effects must not be described as a large engineering improvement: training standard deviations range from 7.332e5 to 9.122e8, reflecting high-compliance designs. This is a bounded immediate diagnostic, not evidence for rejecting uncertainty-based exploration. The next experiment explicitly assesses longer horizons under different physical loads.

### 6.4 Recorded verdict for the acquisition rules

The frozen-state records also carry the material for a promotion verdict, so the audit does not end at a critique of the residual controller. The rule applied here is illustrative and is written after the records existed: a control is promoted when it changes the selected point by at least 20% of states in two or more source histories, its mean immediate utility never falls below the mean-selection control, and its held-out endpoint under the shared initialization lies below that control at the same budget; a control whose utility falls below mean selection in every history is stopped; any other outcome is held for revision.

GP-PI satisfies all three conditions. It changes 25.0% and 35.0% of selected points in the EI and UCB histories, its mean immediate utility is 0.900e-6, 0.347e-6 and 1.179e-6 in the three histories, the corresponding differences from mean selection are 0.000, 0.000 and +0.301e-6, and its closed-loop endpoint is 1233.1 against 1445.1 for the mean-selection rule. GP-UCB fails the second and third conditions: its utility difference is negative in all three histories (-0.900e-6, -0.347e-6 and -0.366e-6) and its endpoint is 2308.7, so it is stopped. GP-EI is held for revision: its utility difference is negative in the PI history (-0.347e-6) and its endpoint is 2308.5.

The per-history utility and the three criteria are released with the other measured records (see Data availability). This is the positive case the framework requires, with its scope stated: a candidate-dependent acquisition rule receives an affirmative verdict from recorded evidence and a plausible alternative is rejected, without an additional physical solve. The verdict is retrospective on frozen records, it is not a pre-registered promotion test, the thresholds are illustrative, and no policy was selected for the paper's comparisons by applying it. It also remains limited to the frozen states, the four-checkpoint utility metric and one design family.

### 6.5 Longer-horizon policies, load-position transfer and total cost

A separately frozen protocol moves the top-edge downward force from position 0.0 to the previously untested positions 0.25 and 0.75 within the same beam family. Each condition uses ten fresh, paired Sobol initializations of 58 designs; material, supports, mesh, dimension, and volume fraction are unchanged. All four transfer policies share one isotropic Matérn-5/2 GP specification and the same candidate seeds at a given phase and step. Environment pins, optimizer bounds, candidate-pool settings, and the difference from the frozen ARD intervention in Section 6.3 are recorded in S10.

Every condition/policy has zero median improvement at its first pilot action, whereas 20-step median improvement is positive. For LCB the 20-step medians are 2.514% and 3.649% in the two conditions; four of ten repeats in each condition improve after a zero-gain first action. Delayed policy assessment is therefore kept separate from immediate screening.

The audited-selection workflow pays for 58 initial responses, four 20-step pilots, and 142 further evaluations of the pilot-selected policy (280 calls). The comparison portfolio separately pays for the same initial designs and all four 142-step continuations (626 calls). Selection is written before validation; pilot labels are excluded from validation training.

**Table 7. Independent selected-policy validation and complete-portfolio comparison. Compliance is lower-is-better. Each compliance column is a median across ten repeats; the gap is the median of paired percent ratios, not a ratio of medians. Selected-policy validation uses 200 algorithm observations but 280 paid workflow calls including pilots; the portfolio pays 626.**

| Force position | Initial compliance | Selected-policy compliance | Portfolio-best compliance | Paired gap (%) | Exact best matches |
| --- | --- | --- | --- | --- | --- |
| 0.25 | 1608.5 | 1172.5 | 943.2 | 9.014 | 4/10 |
| 0.75 | 700.7 | 406.4 | 320.6 | 27.217 | 3/10 |

The selected policy matches the independently executed portfolio-best endpoint in seven of twenty repeats. Its paired median gaps are 9.014% and 27.217%. Against the explicitly executed full portfolio it makes 55.272% fewer calls, accompanied by the disclosed endpoint losses. A secondary all-paid analysis that retains every design paid for by the audited workflow narrows the paired median portfolio gaps to 9.014% and 2.116%; both endpoints are disclosed in S10, and the secondary result does not replace the selected-policy test. These counts do not establish universal savings, equivalence, or a performance-preserving deployment gate. Full per-repeat endpoints, fixed-policy comparisons, pilot-horizon tables, and the paid-call ledger (including the 18,120 / 2,320 / 1,600 / 14,200 recovery accounting) are reported in S10.

![Cost and performance of the independently executed beam transfer workflows.](engineering_optimization/figures/transfer_cost_performance.png)

Figure 6 reports median initial-incumbent improvement and interquartile ranges together with the actual per-repeat call requirement. Each panel is one force position; the six horizontal positions are the four fixed policies at 200 calls, the pilot-selected policy at 280 calls, and the executed four-policy portfolio at 626 calls.

## 7 Discussion and Design Guidance

The deterministic and empirical findings answer different questions. Ordering redundancy follows from the stated decision rule whenever the correction is common across supported candidates. The observed performance loss is specific to the tested feedback controller, surrogate, candidates, and budgets. That loss does not imply that candidate-dependent uncertainty, conformal Bayesian optimization, or all adaptive exploration is ineffective.

A staged design procedure follows for surrogate model management. Identify the exact route from the monitoring statistic to the decision. If the signal adds a common constant before an argmin, ranking cannot change. Freeze common states next and compare the true utility of the alternative choices; an unhelpful exploration response then appears before histories diverge. Closed-loop validation should use instances that did not select controls or coefficients. Calibration statistics remain useful diagnostics, but they are not substitutes for decision utility or final objective value.

The residual-monitor prototype shows why the sequence is required. Its failure fraction is close to 0.1, which could be read as successful monitoring. The same controller increases exploration from about 0.1 to 0.34-0.40, selects candidates with lower immediate improvement, and ends with larger errors. A near-nominal residual diagnostic would have licensed continued spending; the audit stops that spending at the decision layer. Localized weighting improves some quantile-loss diagnostics without producing better trajectories. The missing link is not error measurement but a rule that connects error information to valuable evaluations.

For engineering users the implication is concrete: evaluate the acquisition pathway before paying for large simulation batches. A useful monitor should produce candidate-specific or management-level distinctions whose value can be tested, including delayed value for exploration, search-region changes, restarts, or stopping decisions. Monitoring width or error only to increase exploration can spend the same number of expensive evaluations in less productive regions. In a finite-element design workflow the procedure identifies, before a large batch is released, which mechanism deserves the solves and which evidence would justify promotion to deployment.

The GP intervention tests the audit on actionable acquisition rules. The two force-position conditions test finite-horizon policy and selection outcomes within the same beam family. The strongest reusable result is the evidence procedure itself: identify exact decision classes, pay only for undetermined immediate responses, preserve a label-free intervention boundary, and disclose both closed-loop endpoints and total cost. The transfer selector marks a failure boundary rather than a competitive-optimizer contribution. Its pilot ties, endpoint losses and extra cost relative to fixed policies delimit engineering deployment. Validation on distinct physical model families and competitive warm-start selectors remains outside the evidence.

Several limits remain. Residuals originate from changing surrogate models and scales; no exchangeability argument establishes pointwise coverage. Sparse declarations limit conditional reliability statements. The RBF surrogate truncates training data, and the candidate process is one implementation among many. The broad BBOB external-reference batches retain their native initialization, although the finite-element sensitivity analysis removes this difference. The beam study uses a smooth 19-dimensional design family, not unrestricted 5,000-variable topology optimization. Full sensitivity, 300-dimensional, application, resource, and recovery evidence is supplied separately so that these limits stay auditable without dominating the main paper.

## 8 Conclusion

Recorded evidence supports a decision-consequence audit for surrogate-assisted optimization. The path from surrogate information to a model-management action is stated explicitly. Calibration, decision influence, common-state utility, and closed-loop optimization each require their own evidence. Ranking invariance and the prediction-before-label protocol flag structurally redundant mechanisms and information leakage before large experimental budgets are committed.

The temporal residual monitor is an illustration, not the scope of the audit. Aggregate failure stays close to the nominal level, yet the candidate-independent correction cannot form a distinct exploitation ranking. Feedback choices have lower immediate utility, and held-out BBOB and finite-element trajectories fail the optimization-benefit gate. Shared-initialization controls give context: GP-PI, author-code DRSO, and trust-region Bayesian optimization (TuRBO-1) improve strongly, whereas GP-EI and fixed-multiplier GP-UCB leave the median initial incumbent unchanged. The frozen-state intervention then supplies mechanism-level evidence for the GP acquisition rules. A full decision-level audit of DRSO and TuRBO-1 is not claimed.

Predeployment assessment in expensive engineering optimization is the intended use. On the tested prototype, calibration statistics are not treated as demonstrated optimization value; the unsupported decision pathway is recorded instead. Beyond the residual controller, the GP intervention and force-position study show further distinctions: decisions can differ without immediate gain; later policy value can appear after a zero-gain first action; cheaper selection can lose final performance. The contribution is that reproducible audit, with its query-allocation and cost records—not a guarantee of optimization superiority or net savings.

## Declaration of Generative Artificial Intelligence Use

DeepSeek V4.1 Flash (version 1017) was used only for copyediting and language refinement to improve spelling, grammar, clarity and flow. It did not draft the manuscript or any section of it, form or conclude the argument, or generate the analysis code or the tables. The authors confirm the originality and accuracy of the content. The authors have checked the terms of use of the tool and confirm that this use is suitable for publication. The authors take full responsibility for the integrity of the whole content, including the accuracy of the references.

## Funding Statement

The authors received no specific funding for this study.

## Author Contributions

The authors confirm contribution to the paper as follows: conceptualization, Ya-Yu Zhang, Shu-Chuan Chu, and Jeng-Shyang Pan; methodology, Ya-Yu Zhang, Shu-Chuan Chu, and Zhenyu Meng; software, Ya-Yu Zhang; validation, Ya-Yu Zhang, Zhenyu Meng, and Jia Zhao; formal analysis, Ya-Yu Zhang and Zhenyu Meng; investigation, Ya-Yu Zhang and Jia Zhao; resources, Jeng-Shyang Pan; data curation, Ya-Yu Zhang; visualization, Ya-Yu Zhang and Jia Zhao; writing-original draft preparation, Ya-Yu Zhang; writing-review and editing, Ya-Yu Zhang, Shu-Chuan Chu, Zhenyu Meng, Jia Zhao, and Jeng-Shyang Pan; supervision, Shu-Chuan Chu and Jeng-Shyang Pan; project administration, Shu-Chuan Chu. All authors reviewed the results and approved the final version of the manuscript.

## Availability of Data and Materials

The manuscript sources, the implementation, the frozen configurations, the dependency records, and the released records supporting the added results will be made publicly available in the project repository https://github.com/ya-yu-zhang/Reliable-Surrogate-Assisted-Optimization-in-Expensive-Engineering-Design upon acceptance. Those records comprise the nine validation contrasts and their function-level components (data/engineering_optimization_bbob_validation_v1), the beam repeat-level endpoints and paired contrasts (data/engineering_optimization_beam_endpoints_v1), and the per-history utility record behind the acquisition verdicts (data/engineering_optimization_gp_verdicts_v1). The same materials are available to reviewers during peer review on request. Original GP input hashes and the required archive checksum are documented. Approximately 13.6 GB of historical raw outputs and full execution archives remain outside the repository; the reported experiments can be regenerated using the documented environments and configurations, and archived raw data are available from the corresponding author upon reasonable request. Public release does not grant an open-source license; third-party implementations and publisher templates retain their own terms.

## Ethics Approval

Not applicable. This study did not involve human participants or animals.

## Acknowledgments

During the preparation of this manuscript, DeepSeek V4.1 Flash was used only for language revision (copyediting) to improve spelling, grammar, clarity and flow. The research questions, experimental protocols, acceptance criteria, and scientific interpretations were determined by the authors. All source code, numerical outputs, statistical summaries, citations, and AI-assisted wording were reviewed and verified by the authors, who revised the manuscript and accept full responsibility for the published content.

## Disclosure Statement

The authors report there are no competing interests to declare.

## Supplementary Materials

The supplementary document contains the historical function-level, LassoBench, dimensional, sensitivity and resource evidence, plus the added GP intervention, force-position transfer, per-repeat endpoints, fixed-policy comparisons, horizon diagnostics and complete recovery-aware cost ledger.

## References

Booker, A. J., J. E. Dennis Jr., P. D. Frank, D. B. Serafini, V. Torczon, and M. W. Trosset. 1999. "A Rigorous Framework for Optimization of Expensive Functions by Surrogates." *Structural Optimization* 17: 1–13. https://doi.org/10.1007/BF01197708.

Deshpande, S., C. Marx, and V. Kuleshov. 2024. "Online Calibrated and Conformal Prediction Improves Bayesian Optimization." *Proceedings of AISTATS* 238: 1450–1458. PMLR.

Eriksson, D., M. Pearce, J. A. Gardner, R. Turner, and M. Poloczek. 2019. "Scalable Global Optimization via Local Bayesian Optimization." *Advances in Neural Information Processing Systems* 32. arXiv:1910.01739.

Felten, F., G. Apaza, G. Bräunlich, C. Diniz, X. Dong, A. Drake, M. Habibi, N. J. Hoffman, M. Keeler, S. Massoudi, F. G. VanGessel, and M. Fuge. 2025. "EngiBench: A Framework for Data-Driven Engineering Design Research." *Advances in Neural Information Processing Systems*. https://doi.org/10.52202/085713-0003.

Gobert, M., G. Briffoteaux, J. Gmys, N. Melab, and D. Tuyttens. 2024. "Observations in Applying Bayesian versus Evolutionary Approaches and Their Hybrids in Parallel Time-Constrained Optimization." *Engineering Applications of Artificial Intelligence* 137, article 109075. https://doi.org/10.1016/j.engappai.2024.109075.

Hanawa, Y., T. Harada, and Y. Miura. 2025. "Impact of Surrogate Model Accuracy on Performance and Model Management Strategy in Surrogate-Assisted Evolutionary Algorithms." *Array* 27, article 100461. https://doi.org/10.1016/j.array.2025.100461.

Hansen, N., A. Auger, R. Ros, O. Mersmann, T. Tušar, and D. Brockhoff. 2021. "COCO: A Platform for Comparing Continuous Optimizers in a Black-Box Setting." *Optimization Methods and Software* 36 (1): 114–144. https://doi.org/10.1080/10556788.2020.1808977.

Hao, H., X. Q. Zhang, and A. M. Zhou. 2024. "Enhancing SAEAs with Unevaluated Solutions: A Case Study of Relation Model for Expensive Optimization." *Science China Information Sciences* 67 (2), article 120103. https://doi.org/10.1007/s11432-023-3909-x.

Hao, H., X. Zhang, and A. Zhou. 2025. "Un-Evaluated Solutions May Be Valuable in Expensive Optimization." *Swarm and Evolutionary Computation* 94, article 101905. https://doi.org/10.1016/j.swevo.2025.101905.

Ibrayev, S., B. Omarov, A. Ibrayeva, and Z. Momynkulov. 2024. "DeepSurNet-NSGA II: Deep Surrogate Model-Assisted Multi-Objective Evolutionary Algorithm for Enhancing Leg Linkage in Walking Robots." *Computers, Materials & Continua* 81 (1): 229–249. https://doi.org/10.32604/cmc.2024.053075.

Jin, Y. 2011. "Surrogate-Assisted Evolutionary Computation: Recent Advances and Future Challenges." *Swarm and Evolutionary Computation* 1 (2): 61–70. https://doi.org/10.1016/j.swevo.2011.05.001.

Jin, Y., and Z. Ren. 2025. "Confidence on the Focal: Conformal Prediction with Selection-Conditional Coverage." *Journal of the Royal Statistical Society Series B* 87: 1239–1259. https://doi.org/10.1093/jrsssb/qkaf016.

Jin, Y., H. Wang, T. Chugh, D. Guo, and K. Miettinen. 2019. "Data-Driven Evolutionary Optimization: An Overview and Case Studies." *IEEE Transactions on Evolutionary Computation* 23 (3): 442–458. https://doi.org/10.1109/TEVC.2018.2869001.

Jones, D. R., M. Schonlau, and W. J. Welch. 1998. "Efficient Global Optimization of Expensive Black-Box Functions." *Journal of Global Optimization* 13: 455–492. https://doi.org/10.1023/A:1008306431147.

Kim, D., M. Zecchin, S. Park, J. Kang, and O. Simeone. 2025. "Robust Bayesian Optimization via Localized Online Conformal Prediction." *IEEE Transactions on Signal Processing* 73: 2039–2052. https://doi.org/10.1109/TSP.2025.3559568.

Kostovska, A., A. Jankovic, D. Vermetten, J. de Nobel, H. Wang, T. Eftimov, and C. Doerr. 2022. "Per-Run Algorithm Selection with Warm-Starting Using Trajectory-Based Features." *Parallel Problem Solving from Nature – PPSN XVII*: 46–60. LNCS 13398. https://doi.org/10.1007/978-3-031-14714-2_4.

Kuş, E., Ö. Akgün, N. Dang, and I. Miguel. 2024. "Frugal Algorithm Selection (Short Paper)." *Proceedings of CP 2024* 307. LIPIcs. https://doi.org/10.4230/LIPIcs.CP.2024.38.

Li, J.-Y., Z.-H. Zhan, and J. Zhang. 2022. "Evolutionary Computation for Expensive Optimization: A Survey." *Machine Intelligence Research* 19 (1): 3–23. https://doi.org/10.1007/s11633-022-1317-4.

Liang, J., Y. Lou, M. Yu, Y. Bi, and K. Yu. 2025. "A Survey of Surrogate-Assisted Evolutionary Algorithms for Expensive Optimization." *Journal of Membrane Computing* 7: 108–127. https://doi.org/10.1007/s41965-024-00165-w.

Liu, H., Z. Ren, C. He, and W. Du. 2025. "A Surrogate-Assisted Differential Evolution Algorithm with a Dual-Space-Driven Selection Strategy for Expensive Optimization Problems." *Complex & Intelligent Systems* 11, article 230. https://doi.org/10.1007/s40747-025-01812-0.

Liu, Q., X. Wu, Q. Lin, J. Ji, and K.-C. Wong. 2021. "A Novel Surrogate-Assisted Evolutionary Algorithm with an Uncertainty Grouping Based Infill Criterion." *Swarm and Evolutionary Computation* 60, article 100787. https://doi.org/10.1016/j.swevo.2020.100787.

Liu, X., Y. Bao, and F. Leng. 2025. "Neural Architecture Search via Hierarchical Evaluation of Surrogate Models." *Computers, Materials & Continua* 84 (2): 3503–3517. https://doi.org/10.32604/cmc.2025.064544.

Ma, X., Y. Li, Y. Zhuang, Y. Li, J. Fan, L. Wang, Y. Qi, and J. Xiong. 2025. "A Surrogate-Assisted Evolutionary Algorithm with Gaussian Process Regression and Diversity Search for Large-Scale Expensive Optimization." *Applied Soft Computing* 182, article 113440. https://doi.org/10.1016/j.asoc.2025.113440.

Nardone, E., C. De Stefano, A. Scotto di Freca, F. Fontanella, and T. D'Alessandro. 2026. "Toward Reliable Uncertainty Quantification in Surrogate-Assisted Evolutionary Algorithms via Temporal Conformal Prediction." *Applications of Evolutionary Computation*: 384–401. LNCS 16524. https://doi.org/10.1007/978-3-032-23604-3_24.

Ong, Y. S., P. B. Nair, and A. J. Keane. 2003. "Evolutionary Optimization of Computationally Expensive Problems via Surrogate Modeling." *AIAA Journal* 41 (4): 687–696. https://doi.org/10.2514/2.1999.

Pan, J.-S., J. Chen, J. Li, and Z. Meng. 2026. "Differential Evolution with Exponential Crossover: A Survey." *Computer Science Review* 62, article 100990. https://doi.org/10.1016/j.cosrev.2026.100990.

Pan, J.-S., Y. Peng, J. Li, J. Zhao, L. Kong, and S.-C. Chu. 2026. "Multilayer Perceptron Grouping and Sparse Gaussian Process-Based Surrogate-Assisted Evolutionary Algorithm for Expensive Multiobjective Optimization." *IEEE Transactions on Cybernetics* 56 (4): 2148–2161. https://doi.org/10.1109/TCYB.2025.3634364.

Sehic, K., A. Gramfort, J. Salmon, and L. Nardi. 2022. "LassoBench: A High-Dimensional Hyperparameter Optimization Benchmark Suite for Lasso." *Proceedings of the 1st International Conference on Automated Machine Learning* 188: 2/1–2/24. PMLR. https://proceedings.mlr.press/v188/sehic22a.html.

Sun, C., Y. Jin, R. Cheng, J. Ding, and J. Zeng. 2017. "Surrogate-Assisted Cooperative Swarm Optimization of High-Dimensional Expensive Problems." *IEEE Transactions on Evolutionary Computation* 21 (4): 644–660. https://doi.org/10.1109/TEVC.2017.2675628.

Suprayitno and J.-C. Yu. 2019. "Evolutionary Reliable Regional Kriging Surrogate for Expensive Optimization." *Engineering Optimization* 51 (2): 247–264. https://doi.org/10.1080/0305215X.2018.1446084.

Wang, H., Y. Jin, and J. Doherty. 2017. "Committee-Based Active Learning for Surrogate-Assisted Particle Swarm Optimization of Expensive Problems." *IEEE Transactions on Cybernetics* 47 (9): 2664–2677. https://doi.org/10.1109/TCYB.2017.2710978.

Wang, R.-Y., J.-S. Pan, S.-C. Chu, V. Snášel, J. Zhao, and H.-M. Yang. 2026. "A Bimodal Surrogate-Assisted PSO Algorithm with Wide Coverage and Dynamic Space Refinement for Expensive Multi-UAV Path Planning." *Expert Systems with Applications* 331, article 133075. https://doi.org/10.1016/j.eswa.2026.133075.

Wang, Z., L. Duan, L. Kuang, H. Zhou, and J. Duan. 2025. "Physics-Informed Gaussian Process Regression with Bayesian Optimization for Laser Welding Quality Control in Coaxial Laser Diodes." *Computers, Materials & Continua* 84 (2): 2587–2604. https://doi.org/10.32604/cmc.2025.065648.

Wu, J., and P. I. Frazier. 2019. "Practical Two-Step Lookahead Bayesian Optimization." *Advances in Neural Information Processing Systems* 32.

Yu, L., Y. Guo, L. Feng, Z. Zhu, Z. Wei, and Y. Hou. 2026. "A Multi-Source Surrogate-Assisted Evolutionary Algorithm for Expensive Optimization: An Optinformatics Perspective." *Swarm and Evolutionary Computation* 107, article 102491. https://doi.org/10.1016/j.swevo.2026.102491.

Yu, M., X. Li, and J. Liang. 2020. "A Dynamic Surrogate-Assisted Evolutionary Algorithm Framework for Expensive Structural Optimization." *Structural and Multidisciplinary Optimization* 61 (2): 711–729. https://doi.org/10.1007/s00158-019-02391-8.

Zatarain Salazar, J., D. Hadka, P. Reed, H. Seada, and K. Deb. 2025. "Diagnostic Benchmarking of Many-Objective Evolutionary Algorithms for Real-World Problems." *Engineering Optimization* 57 (1): 287–308. https://doi.org/10.1080/0305215X.2024.2381818.

Zhou, R., C. Ren, Z. Meng, and H. Zhu. 2025. "Surrogate-Assisted Differential Evolution with Search Space Tightening for High-Dimensional Expensive Optimization Problems." *IEEE Transactions on Systems, Man, and Cybernetics: Systems* 55 (10): 7356–7368. https://doi.org/10.1109/TSMC.2025.3582897.

Zou, H., S. Zeng, C. Li, R. Jiao, and F. Zhao. 2025. "Uncertainty Estimation by Boosting with Gaussian Process for Expensive Optimization Problems." *Applied Soft Computing* 180, article 113320. https://doi.org/10.1016/j.asoc.2025.113320.
