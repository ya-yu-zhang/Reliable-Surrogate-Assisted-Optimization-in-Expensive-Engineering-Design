# Contribution and evidence assessment for Engineering Optimization

The proposed contribution is an implemented intervention-and-verification
method for surrogate management. It is not a new uncertainty estimate,
acquisition function, universally superior selector, or convergence theorem.
No claim of being the first to log decisions, count diagnostics, use common
initializations, or observe additive ranking invariance is made.

## Concrete technical content

1. Freeze actual learned states and candidate pools; change only acquisition
   policy and record the choice before consulting diagnostic outcomes.
2. Partition policies by exact context-point identity and evaluate one response
   per class. Proposition 1 gives the worst-case exact-utility query requirement
   under an unrestricted deterministic-oracle assumption. Different physical
   conditions are distinct contexts. Equality of one action is not equality of
   later policy trajectories.
3. Connect the immediate intervention to separate finite-horizon policy
   evidence and to an independently seeded, pilot-label-free validation run.
4. Preserve a full cost boundary: algorithm observations, actual FE attempts,
   allowed deterministic reuse, diagnostic calls, solver verification and
   deliberate recovery calls are distinct quantities.

The mathematical observations are elementary; their contribution is the
operational diagnostic design and its application to multiple actionable GP
rules and a residual-monitor controller. The manuscript must not make a
standalone novelty claim for the lower-bound argument or additive invariance.

## Nearest studies and the distinction to establish

| Prior study | Verified focus | Present evidence object |
|---|---|---|
| Hanawa et al., Array 27, 100461 (2025), DOI 10.1016/j.array.2025.100461 | Adjustable pseudo-surrogate accuracy across management strategies | Acquisition intervention on an unchanged, actually learned GP state |
| Zatarain Salazar et al., Engineering Optimization 57(1), 287-308, DOI 10.1080/0305215X.2024.2381818 | Diagnostic benchmarking of MOEAs on real applications | Decision-level equivalence and utility followed by policy-level validation |
| Suprayitno and Yu, Engineering Optimization 51(2), 247-264, DOI 10.1080/0305215X.2018.1446084 | Variance-guided reliable regions and sequential infill | Audit of an existing signal-to-action pathway; no reproduction or superiority claim |
| Kus et al., CP 2024, DOI 10.4230/LIPIcs.CP.2024.38 | Lower-cost acquisition of selection training data | Exact accounting of a particular independent pilot-validation workflow |
| Kostovska et al., PPSN 2022, 46-60, DOI 10.1007/978-3-031-14714-2_4 | Trajectory-based per-run selection with warm-starting | Cold validation used deliberately to test selection transfer, not a competitive new selector |
| Booker et al., Structural Optimization 17, 1-13 (1999), DOI 10.1007/BF01197708 | Surrogate management with convergence analysis | An evidence audit that does not inherit optimizer convergence guarantees |

Sources checked: publisher abstracts, author arXiv versions, the TU Delft
author publication record, and the Dagstuhl proceedings record. Comparisons
are confined to documented study focuses; they do not imply a systematic
proof that no prior work combines any of these techniques.

## Claim-to-evidence map

| Claim | Evidence | Boundary |
|---|---|---|
| A common additive term can be ranking redundant | Lemma 1 and matched implementation records | Explicit tie, arithmetic, candidates and state conditions |
| Diagnostic evaluation can be shared across identical decisions | 480 choices, 261 within-state distinct choices, 138 new calls after permitted reuse | Immediate deterministic responses; not identical later policies |
| Zero first-step gain is insufficient to reject a policy | All eight condition/policy medians have zero first-step gain and positive 20-step median improvement | Diverging pilot histories, not the causal effect of the first action under fixed continuation |
| Short pilot selection does not guarantee final best-policy selection | 20 independent canonical validations; 7 exact portfolio-best matches | A specified selector and two force locations in one beam family |
| A cheaper selection workflow has a cost-performance tradeoff | 280 versus 626 calls, accompanied by 9.014% and 27.217% median selected-policy gaps | Fixed policies cost 200; audit costs 40% more than a fixed policy |
| Endpoint definitions affect apparent engineering value | Separate prespecified selected-policy endpoint and secondary best-of-all-paid endpoint | Secondary descriptive analysis, no retrospective promotion rule |

## Scientific parameter differences to disclose

The immediate audit uses logged ARD Matérn-5/2 parameters without refitting,
4,096 Sobol candidates plus the frozen source action, and EI with zero margin
(PI margin is 0.01 times training standard deviation). Transfer uses isotropic
Matérn-5/2, deterministic bounded L-BFGS-B refitting, 1,024 Sobol candidates,
and a 0.01-scaled margin for both EI and PI. Kappa=2, alpha=1e-6, dimension19
and volume0.35 are common. These are different controlled experiments; the
transfer study does not reproduce the original GP optimizer implementation.

## Readiness boundary

The revised argument is materially stronger because it has an executable
intervention, a query-allocation rule, delayed-policy evidence and a complete
ledger rather than only a failed-feedback case. Innovation sufficiency and
acceptance remain editorial judgments. All new comparisons are descriptive;
there are no added p-values or post hoc optimization-promotion thresholds.
The numerical solver-replay tolerance was revised after the initial check;
its original 42 attempts, revised tolerance and 60 retained checks are disclosed
separately from the unchanged GP prediction-replay tolerance. The framework
has not been validated across distinct physical model families or against a
competitive warm-start selector. Author affiliations, final author approval
and final submission-format PDF verification remain separate pending tasks.
