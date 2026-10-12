# Frozen first-action / common-continuation verification

Prospective extension of the released GP intervention, not a new optimizer or a
promised positive result. All first choices and previous diagnostic labels already
exist; the present extension does not claim blind discovery of their immediate
utility. Subsequent five-step outcomes have not been used to select this design.

Thirty learned states at PRE(101): EI, PI and UCB source histories, ten seed blocks
each. States are nested within shared seeds and source histories, not thirty new
independent initializations. Source histories, frozen actions and fitted ARD
Matérn-5/2 kernels retain the original versioned environment. The engineering
problem is the same deterministic Beams2D, 100x50 mesh, 19 design variables,
volume0.35, unchanged default force/material/supports.

First controls: mean, EI, PI, LCB, plus an explicitly constructed common-additive
ranking-invariant control. The last control is an instrumentation check, not an
innovation or independent experiment. Canonical unshifted comparison avoids
finite-precision cancellation. Exactly identical first actions form equivalence
classes and share one deterministic response/continuation history.

After the first action each branch refits the same GP family, with fixed logged
kernel hyperparameters and normalize_y=True, using only its original 100 labels,
its own first label and its own continuation labels. All branches then choose the
minimum posterior mean from fresh common external Sobol pools of 1024 points.
Observed-point filtering is the same declared rule. Seed namespace is shared
within each state/continuation step. No alternative acquisition continues after
the first action. Horizons0/1/3/5 mean additional steps after that first action.
Branch contrasts are conditional on this model, rule, pool sequence and horizon;
they do not prove an unconditional causal effect or global strategy superiority.

The primary scale is fractional initial-incumbent compliance reduction; retain
raw compliance and the old standard-deviation-normalized immediate utility as
secondary evidence. Compare each branch against mean. Fixed relative tie
threshold1e-6, with descriptive sensitivity at1e-5 and1e-4. No post-result tuning,
new inferential p-values or claims of physical improvement beyond discretization
accuracy. Past numerical replay checks remain applicable; no new physical
validation calls are hidden.

Diagnostic comparison is an information/estimand comparison, not a fabricated
accuracy contest against existing published algorithms. A single frozen GP's
error and coverage statistics are shared across these first-action policies.
Describe their inability to distinguish policy actions/outcomes without extra
mechanism information. Report the audit's action classes, measured immediate
utility and common-continuation contrasts. Original whole-policy/ablation
endpoints answer a different question and cannot replace this conditional
contrast. Do not claim conventional diagnostics never analyze mechanisms.

After choices are frozen, ten archived source-selected points101..110 provide
retrospective RMSE and empirical90% interval coverage. These points are biased by
the source optimizer. There is no exchangeability/coverage guarantee; their
labels never enter branch training or promotion. They are already-paid source
observations, not new physical calls and not an independent validation sample.

All first labels reuse the released diagnostic ledger under exact objective/point
equivalence. At most30*4*5=600 new finite-element attempts; failed attempts count
and stop the run. Cache reuse is counted separately. Report total paid historical
first-label provenance, new attempts, GP/FE runtime and archive/recovery overhead
separately. No automatic rerun, replacement seed or favorable-subset selection.
All thirty states and unfavorable results are retained.

Related-work correction: Diagnostic benchmarking of many-objective evolutionary
algorithms for real-world problems (doi10.1080/0305215X.2024.2381818) includes
performance, efficiency, reliability, parameter controllability and runtime
dynamics. Table1a's brief performance-only characterization must be broadened.
A claim of prior-art absence or a complete comparison to all literature is not
supported. The specific extra object here is a frozen first-action intervention,
exact action equivalence, query allocation and conditional common-continuation
record. Authors must independently assess its novelty and integrate scientific
argument. Publisher AI-policy review remains pending; this is a technical
protocol/evidence record, not a drafted manuscript argument section.
