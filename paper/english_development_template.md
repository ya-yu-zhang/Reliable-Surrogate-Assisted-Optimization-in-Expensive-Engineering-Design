---
title: Decision Effects of Post-Selection Error Monitoring in Surrogate-Assisted Black-Box Optimization
subtitle: Development study and mechanism audit — working manuscript
date: 17 September 2026
---

# Abstract

Surrogate-assisted optimization allocates a small number of objective evaluations using predictions over a changing candidate population. Errors measured over the full population, the evaluated candidates, and candidates declared to improve the incumbent concern different decision objects. We study an empirical one-sided residual monitor and a feedback rule that increases spatial exploration when its historical upper bounds fail, become wide, or accompany stagnation. We first establish that a candidate-independent additive correction preserves the ordering of the predicted means. Under the studied global and temporal rules, the upper-bound improvement mode therefore selects exactly the mean-greedy candidate. The mechanism that can alter the main temporal prototype's trajectory is its exploration probability.

{{ABSTRACT_RESULTS}}

Keywords: expensive black-box optimization; surrogate-assisted evolutionary search; prequential residuals; post-selection error monitoring; model management

# 1 Introduction

An objective evaluation may require a simulation, model training, or a physical experiment. In these settings, a surrogate can help select which candidate merits the next evaluation. The surrogate's usefulness depends on how its predictions affect these decisions, rather than solely on its accuracy over an arbitrary test population. A predictor may be accurate over most proposed candidates while performing differently on candidates favored by its own ranking. Equally, an upper bound may rarely fail while rarely identifying useful opportunities.

We consider deterministic, single-objective optimization over a bounded continuous domain. The objective does not drift within a run. The surrogate, its training population, and the candidate distribution nevertheless change as evaluated points accumulate. Historical residuals can thus differ in both their model of origin and their prediction-time scale. Recording them honestly supports an online empirical monitor; it does not by itself establish exchangeability or a conformal coverage guarantee.

Our original question is whether monitoring the error of the actually evaluated candidates can improve objective-evaluation allocation relative to fixed selection rules. The development protocol permits a transition to mechanism analysis if the feedback prototype does not improve optimization. We follow that branch rather than reinterpret a coverage statistic as evidence of optimization efficiency.

The study separates three experiments. Common-history diagnostics compare residual calibrators at identical frozen models and pools. Common-state experiments compare the immediate utility of alternative decisions without updating the history. Independent closed-loop trajectories evaluate the resulting optimization behavior. Extra labels used by the first two experiments are acquired only on inexpensive analytic benchmarks, stored separately, and never provided to the optimizer.

The contributions retained at this stage are narrowly scoped: an ordering-equivalence result for the specified additive correction and selection rule; an auditable implementation of prediction-before-label residual monitoring; and empirical evidence distinguishing calibration diagnostics, improvement declarations, and optimization utility. We do not claim a new conformal construction, superiority to published methods, or general high-dimensional effectiveness.

# 2 Related work and scope of comparison

Online calibration has already been used in Bayesian optimization. Deshpande, Marx, and Kuleshov [1] study calibrated predictive distributions and online updating. Their approach differs from taking a fixed-weight empirical quantile of historical signed residuals. Its assumptions and guarantees cannot be imported into the present implementation.

LOCBO [2] uses localized online conformal thresholds to calibrate a likelihood, obtains a posterior through denoising, and uses that posterior in optimization. Its guarantees distinguish noisy observations from the latent objective and depend on the construction and stated assumptions. An empirical spatial residual weight and an effective-sample-size threshold are not equivalent substitutes. Moreover, a constant correction to a mean ranking is not a theorem about all distribution-calibrated acquisition functions.

Temporal conformal prediction has also been studied in surrogate-assisted evolutionary optimization [3]. The publisher's abstract reports temporal weighting and optimization evaluation savings. We have verified that abstract, but have not obtained a reliable full implementation. Consequently, the temporal residual monitor here is an internal reference, not a reproduction of that work. The algebraic redundancy identified below concerns our decision rule and must not be attributed to the published method without its algorithm.

JOMI [4] addresses selection-conditional prediction through a reference-set construction. Its theorem requires a selection rule invariant to permutations of the calibration data and a specified conditional exchangeability condition. Our adaptive, cross-model residual history does not have an established justification for those conditions. We diagnose selected-point errors but do not construct JOMI prediction sets or claim its validity.

SADE-SS [5] studies parameter adaptation, search-space tightening, and global/local search management. Boosting Gaussian-process uncertainty [6] and the use of performance, spatial, and temporal evolutionary knowledge [7] provide further context. Full text or reliable executable details remain incomplete for several of these methods. This manuscript therefore reports internal mechanism comparisons and keeps the competitive evidence gap explicit.

# 3 Problem, information, and decision events

The problem is

$$\min_{x\in\Omega}f(x),\qquad\Omega=[l,u]^D,$$

with a budget of $B$ objective calls. Initialization, online startup, repeated calls, and subsequent selected evaluations all count. No constraints, observation noise, multiple fidelities, or multiple objectives are included.

At evaluation $t$, the available labeled history is $\mathcal D_{t-1}=\{(x_i,y_i):i<t\}$. Before obtaining $y_t$, we persist the selected point, its predicted mean $\mu_t(x_t)$, empirical upper bound $H_t(x_t)$, incumbent $b_{t-1}$, prediction-time scale $s_t$, selection mode, and random state. The journal is flushed before the objective is invoked. The signed prequential residual is

$$r_t=\frac{y_t-\mu_t(x_t)}{s_t}.$$

The scale is the population standard deviation of the current training labels, replaced by one when it is zero. Each residual retains the original prediction and scale. We never recalculate it with a later model or use a training residual as if it were an online prediction error.

An upper-bound failure is $e_t=\mathbb I[y_t>H_t(x_t)]$. A monitored improvement declaration requires sufficient support and

$$H_t(x_t)<b_{t-1}-\tau_t,\qquad\tau_t=10^{-6}s_t.$$

It is false if $y_t\ge b_{t-1}-\tau_t$. Every false declaration is an upper-bound failure on that declared point. This elementary event inclusion does not control the declaration denominator, establish a per-declaration success probability, or imply a bound on the false-discovery proportion. A run with no declarations has an undefined FDP, reported as NA.

# 4 Search framework and empirical monitoring

## 4.1 Initialization, model, and candidates

We use a randomized Latin hypercube with $n_0=2D+20$ points in a fixed order. The first $D+10$ points train the initial model. The next $D+10$ points are evaluated sequentially after prediction, forming online startup residuals. Internal variants share this initialization and startup process.

Inputs are scaled to $[0,1]^D$. The regularized Gaussian RBF uses

$$d(x,x')=\|x-x'\|_2/\sqrt D,\qquad k(x,x')=\exp\{-d(x,x')^2/(2\cdot0.25^2)\},$$

and ridge $10^{-6}$. Labels are standardized using the current training subset. At most 256 points are retained: up to 128 best-valued points followed by farthest-point sampling from the remaining archive. Below the cap, all observations are used. This is an implementation choice to limit dense linear-algebra costs, not an RBF complexity advantage.

Each round proposes 256 candidates: 128 reflected DE/current-to-pbest/1 proposals with $F=.5$, $CR=.9$, and $p=.2$, and 128 independently scrambled Sobol points. The parent pool has at most 64 members, combining elite and spatially dispersed historical points. Candidates within $10^{-10}$ of evaluated points or duplicates are removed and replenished from a separate Sobol stream. Ties are resolved by the original index. One candidate is evaluated per round. Random streams are keyed by seed, purpose, and evaluation index; the core search does not use the total budget.

## 4.2 Residual upper bounds and support

For candidate $x$, the empirical bound is

$$q_t(x)=\max\{0,Q^w_{.9}(r_i:i<t)\},\qquad H_t(x)=\mu_t(x)+s_tq_t(x).$$

The quantile is the smallest observed residual at which cumulative normalized weight first reaches .9, without interpolation. We compare four weight rules over the most recent 100 residuals: global equal weights (G), temporal weights with a half-life of 25 evaluations (T), spatial Gaussian weights (S), and their product (ST). Spatial bandwidth is the twentieth-neighbor distance. The effective sample size is

$$n_{\mathrm{eff}}(x)=\frac{(\sum_iw_i)^2}{\sum_iw_i^2}.$$

Below 20 effective samples, ST falls back to T, S to G, and insufficient T to G. Fewer than 20 total residuals disables bound-based improvement selection. Support, fallback, and weighted distances are recorded. This threshold checks weight concentration and is not a representativeness or coverage guarantee.

## 4.3 Feedback and selection

Over at most the last 30 online predictions, let $\bar e_t$ be the failure fraction and $\bar v_t$ the mean normalized margin, where $v_i=(H_i-\mu_i)/s_i$. Define

$$a_t=\max\left\{\operatorname{clip}\left(\frac{\bar e_t-.1}{.2},0,1\right),\operatorname{clip}\left(\frac{\bar v_t-1}{2},0,1\right)\right\}.$$

Let $h_t$ count evaluations without significant incumbent improvement and $z_t=\min(h_t/20,1)$. The prototype uses

$$p_t=\operatorname{clip}(.1+.4a_t+.3z_t,.1,.8).$$

With fewer than 20 monitoring records, $p_t=.5$ and the improvement mode is disabled. Otherwise, spatial exploration with probability $p_t$ selects the candidate maximizing its minimum distance to the evaluated archive. On the complementary branch, if supported improvement candidates exist and $a_t<.5$, the candidate with the smallest supported empirical bound is selected; otherwise the smallest predicted mean is selected. The coefficients are frozen development choices, not theoretically optimal values. Higher error, width, or stagnation can induce more exploration, but whether those evaluations benefit optimization is an empirical question.

# 5 Structural audit and limitations of event reasoning

**Ordering equivalence.** If support is common across candidates, $q_t(x)=q_t$, and $s_t$ is a common scalar, then $\arg\min_xH_t(x)=\arg\min_x\mu_t(x)$ under the same tie rule. Adding the common constant $s_tq_t$ preserves every pairwise comparison. Checking whether an improvement candidate exists does not change the minimizer in the studied selection rule. Thus G/T upper-bound and mean-greedy modes select the same point on the non-exploration branch.

If the exploration probability and random streams are also unchanged, removing the upper mode produces the same entire trajectory by induction over evaluations. Temporal monitoring with a fixed probability likewise produces the corresponding fixed mean/exploration trajectory. These configurations are retained as implementation audits, not independent mechanism ablations. Spatial bounds can vary across candidates and need not preserve the mean ranking. Candidate-dependent support, other acquisition functions, evaluation-trigger decisions, or altered stopping policies are outside this equivalence statement.

**False declarations.** If $H_t<b_{t-1}-\tau_t$ and $y_t\ge b_{t-1}-\tau_t$, then $y_t>H_t$. No distributional argument is required. Conversely, an overall failure fraction of .1 can coexist with a false-declaration fraction of one if all failures fall in a rare declared subset. The supplied deterministic counterexample distinguishes this event relation from a reliability guarantee; it is not included in benchmark statistics.

# 6 Development protocol and statistical units

We preselected BBOB functions 1, 3, 6, 10, 15, 20, 21, and 24, dimensions 10 and 20, instances 1–3, and three repeats per instance. Each configuration has 144 runs. The budget is $10D$, including initialization. The primary prototype is T; it is not chosen after ranking the spatial variants.

The closed-loop experiment compares 13 configurations: mean greedy, fixed exploration probabilities .1/.3/.5/.8, temporal monitoring with fixed .3 management, PEM-G/T/S/ST feedback, removal of the upper mode, failure-only feedback, and stagnation-only feedback. The failure-only variant removes both width feedback and stagnation, so it cannot identify those two terms' separate causal contributions. Mean-greedy and fixed strategies still compute T bounds for their monitoring journals, but the bounds do not affect their decisions.

Common histories use mean greedy, fixed .3 mixing, and uniform selection from the current 256-candidate pool. Pool-random is not global independent uniform sampling, and maximum-distance exploration is not a random history. At four frozen evaluation indices we compare G/T/S/ST and alternative single-step choices using independently acquired pool labels. The first checkpoint is moved beyond startup when needed: 41/50/75/100 in 10 dimensions and 61/100/150/200 in 20 dimensions. These corrected first checkpoints are not described as 25% budget.

Let $E_B=\max(f_{\mathrm{best},B}-f^*,0)$ and let $E_{n_0}$ be the common initial error, floored at $10^{-12}$. The endpoint is $\log_{10}\max(E_B/E_{n_0},10^{-12})$. For each function/instance, we take the median over three runs, then average the three instances; functions receive equal weight within each dimension. The paired difference is prototype minus control, with negative values favoring the prototype. Its base-10 exponent is a geometric summary of relative errors, not a ratio that every run shares.

The fixed probability is selected only on development data, by equal-weight endpoint scores over dimensions and functions. Eight function-level paired contrasts per dimension enter Wilcoxon tests. Twenty comparisons are jointly Holm-adjusted. Four thousand paired hierarchical bootstrap resamples draw functions, instances, and common run indices; each method's run median is recomputed before subtraction. Bootstrap intervals are not multiplicity-adjusted and do not remove uncertainty introduced by selecting the fixed control on this dataset. No development comparison is represented as independent confirmation.

Diagnostics report pool, predicted top 10% (26 candidates), actual selected point, strategy-selected point, and the declared subset separately. Failure fractions are first averaged by state, while sparse declarations additionally disclose nonempty states, candidate counts, and pooled failures. Candidate labels within a pool are correlated and are not treated as independent statistical problems.

# 7 Audited development results

{{RESULTS}}

# 8 Discussion

The retained evidence has two distinct meanings. Ordering redundancy is a deterministic property of the stated rule, supported by trajectory audits. Increased exploration without the required development benefit is an empirical finding about this feedback design, model, candidate mechanism, and budget. It does not imply that all uncertainty feedback or conformal optimization is ineffective.

Differences between pool and selected-point failures depend on history. Fixed mixing can select either a mean-greedy candidate or a spatially distant candidate. Labeling every such difference as greedy selection bias obscures the exploration policy's role. Local residual weighting may improve a diagnostic loss without establishing that the region contains valuable optimization opportunities or that paying to evaluate it improves future decisions.

The upper-bound margin, failure rate, declaration frequency, and final objective must be read together. A low failure rate can be achieved by wide bounds or nearly absent declarations. In this study, the main prototype approximately attains its target observed failure fraction while making very few declarations and producing worse development endpoints. This separates empirical monitoring quality from useful budget management.

The recorded implementation costs include fitting, candidate generation, bound computation, selection, objective calls, and journaling. Shared-process elapsed times are not exclusive wall-clock comparisons. The analytic benchmark is extremely cheap and cannot establish application acceleration. Greedy/fixed variants' recorded costs include T monitoring that does not affect selection. Dense RBF fitting, training truncation, and candidate generation should be evaluated separately, alongside peak process memory, before practical time claims.

The present residual quantile provides no pointwise 90% success probability, selection-conditional coverage theorem, FDP/FDR guarantee, regret bound, or global convergence theorem. Cross-model scale migration and sparse short-budget feedback remain limitations. Development dimensions 10 and 20 do not establish general high-dimensional capability.

An independently frozen mechanism validation on all 24 BBOB functions, dimensions 10/20/40, and instances 11–13 is in progress. Its labels and comparisons are not included here. Original instances 6–10 remain reserved. Sobol/CMA-ES background runs have been completed separately; GP-EI and author TuRBO adapters are under resource precheck. Full competitive SAEA reproduction, CEC verification, and application evidence remain incomplete. These gaps limit the manuscript's readiness for submission.

# 9 Conclusion

We implement a prequential one-sided error monitor and examine its decision consequences through isolated diagnostics and closed-loop development runs. Candidate-independent additive corrections preserve the predicted-mean ordering under the specified rule. Diagnostics also show that differences among monitoring objects depend on the history policy. The main feedback prototype does not meet the predeclared development optimization-benefit gate, so we retain a mechanism and failure analysis rather than an optimization-improvement claim. Independent validation and complete competitive/application evidence are still required; this is a working development manuscript.

# References

[1] S. Deshpande, C. Marx, V. Kuleshov. Online Calibrated and Conformal Prediction Improves Bayesian Optimization. AISTATS, PMLR 238, 1450–1458, 2024. <https://proceedings.mlr.press/v238/deshpande24a.html>.

[2] D. Kim, M. Zecchin, S. Park, J. Kang, O. Simeone. Robust Bayesian Optimization via Localized Online Conformal Prediction. arXiv:2411.17387v2, 2025. <https://arxiv.org/html/2411.17387v2>.

[3] E. Nardone, C. De Stefano, A. Scotto di Freca, F. Fontanella, T. D'Alessandro. Toward Reliable Uncertainty Quantification in Surrogate-Assisted Evolutionary Algorithms via Temporal Conformal Prediction. EvoApplications, LNCS 16524, 384–401, 2026. DOI:10.1007/978-3-032-23604-3_24.

[4] Y. Jin, Z. Ren. Confidence on the Focal: Conformal Prediction with Selection-Conditional Coverage. arXiv:2403.03868v3. <https://arxiv.org/html/2403.03868v3>.

[5] R. Zhou, C. Ren, Z. Meng, H. Zhu. Surrogate-Assisted Differential Evolution With Search Space Tightening for High-Dimensional Expensive Optimization Problems. IEEE Transactions on Systems, Man, and Cybernetics: Systems 55(10), 7356–7368, 2025. DOI:10.1109/TSMC.2025.3582897.

[6] H. Zou, S. Zeng, C. Li, R. Jiao, F. Zhao. Uncertainty estimation by boosting with Gaussian process for expensive optimization problems. Applied Soft Computing 180, 113320, 2025. DOI:10.1016/j.asoc.2025.113320.

[7] L. Yu, Y. Guo, L. Feng, Z. Zhu, Z. Wei, Y. Hou. A multi-source surrogate-assisted evolutionary algorithm for expensive optimization: An optinformatics perspective. Swarm and Evolutionary Computation 107, 102491, 2026. DOI:10.1016/j.swevo.2026.102491.

[8] COCO. BBOB test suite documentation. <https://numbbo.github.io/coco/testsuites/bbob>. Accessed 17 September 2026.

[9] IOHprofiler. IOHexperimenter documentation and implementation. <https://github.com/IOHprofiler/IOHexperimenter/blob/master/ioh/README.md>. Experimental version 0.3.22.

# Reproducibility and completion status

The repository contains frozen core code and configuration fingerprints, environment locks, seeds, raw PRE/LABEL journals, candidate-pool snapshots, independent diagnostic labels, statistics, and failure records. Supplementary material discloses the information path, declaration counts, and a explicitly post-hoc trace illustration. No diagnostic label is an optimizer input. Repeated trajectory executions used to capture pools do not increase the optimization statistical sample. Author-code budget counterexamples are labeled control-flow tests rather than performance experiments. The original research goal remains active pending the remaining evidence and manuscript checks.
