# Frozen budget audit: independent validation protocol v1

Technical protocol and author-review record, not a manuscript argument draft.
Freeze and publish this protocol, code, configuration and version manifest before
acquiring any new held-out physics labels. Historical results may motivate the
design but are not an independent validation set. No threshold tuning, seed
replacement, success-only reporting, or automatic recovery of incomplete blocks.

## Target and decision contract

For the same 100-label learned state, compare one selected first action with the
posterior-mean first action, followed by five additional shared-rule actions.
Positive effect is (mean endpoint - alternative endpoint) / initial incumbent.
The primary decision margin is 0.001 (0.1% of initial compliance); descriptive
sensitivities 0.0001 and 0.01. This is an explicitly illustrative numerical decision
margin, NOT a certified engineering tolerance or an industrial requirement.
Equality at the margin is a tie. Targets use the same margin and horizon for all
rules; h0 is only a proxy for h5. A change between horizons is not itself an error.

Exact action/context/state/kernel/continuation/seed equality identifies equivalent
trajectories. Equal utilities alone do not. Response reuse across different states
does not authorize whole-trajectory reuse. Outcomes are conditional on this mesh,
parameterization, fitted kernel, candidate sequence, continuation and horizon.

## Independent source histories

Ten new complete seed blocks 10--19 use master seed 2026101207, distinct from all
released development experiments. Each block has 50 shared Sobol warm labels and
three 50-step EI/PI/LCB source histories. Ten seed blocks are the independent
replication units; the 30 states and named policy contrasts are dependent.

ARD Matern-5/2, normalize_y=True, alpha=1e-6. Fit kernel once at the shared warm
state, bounded L-BFGS-B with maxiter30, no restarts; freeze theta for all source
updates and audit continuations. This deliberately differs from earlier source
GP fitting and is disclosed. Use fresh 1024-point Sobol pools, xi=0.05*training
standard deviation for PI, EI without xi, LCB kappa2; first index breaks ties.
Source histories share external pool seeds within a block. Only branch-own past
observations enter each continuation GP. Probe labels never enter training.

First controls mean/EI/PI/LCB are frozen per learned state before any first-action
or calibration-probe label is read. Two continuations, mean and EI, use the same
external candidate seed at each step; compare rules separately, then describe
continuation sensitivity without treating these two outcomes as independent.

## Budget methods and comparisons

Primary budget: 18 branch-step response requests per state/continuation;
sensitivities12 and24. This conservative budget also charges already-paid response
lookups and exact cross-branch response coincidences. Report distinct response
points, initial-history reuse, and actual physics attempts separately. Oracle
collection shared among replayed methods is charged in the full research ledger;
it is not free deployment evidence or a demonstration of net deployment savings.

* Adaptive: measure h0/h1 for every distinct action, complete the mean branch to
  h5, rank alternatives by abs(h1 difference)/initial + root predictive sd/initial,
  then complete trajectories in that order through stages3 and5. This is an
  allocation heuristic, not a calibrated confidence interval. Partial trajectories
  abstain. All exploration overhead is counted; it can reduce classified coverage.
* Fixed depth: complete mean then EI/PI/LCB action classes in fixed order, under
  the same budget. This is a deliberately strong completion-oriented comparator.
* Fixed breadth: round-robin one additional response per distinct branch under
  the same budget; incomplete target trajectories abstain.
* Immediate: classify h0 as a proxy for the specified h5 target; charge all first
  action response requests. Immediate ties are treated as proxy ties, not certified.
* Calibration gate: eight new uniform Sobol probes, root-GP normalized RMSE<=0.25
  and empirical 90% coverage>=0.8; if accepted, classify the difference of root
  expected improvements as a proxy for h5 effect. Otherwise abstain. This is a
  constructed, explicitly frozen baseline, NOT an implementation of a published
  diagnostic framework. The gate does not imply a future-utility guarantee.
* Full horizon: complete every distinct class; finite-horizon reference requiring
  up to24 requests. It is not budget matched when fewer than24 are available.

Structural aliases report tie with no separate measurement. If all controls are
identical, no response is required. No rule infers later equivalence from a
measured immediate tie. Conservative rules classify only completed contrasts;
their zero observed error can therefore be definitional, and is never presented
without coverage, abstention and cost. Never claim population error is zero.

## Validation and estimands

Collect the full deterministic oracle trajectories, then replay the preregistered
rules through a prefix-only interface. These are prospective independent labels
with sequential offline trace validation, NOT independent live deployment trials.
Each request exposes only its next label. Verify history, seeds, model predictions,
actions, monotone incumbents, all response contexts, and retained hashes.

Report original named contrasts and distinct nonbaseline-action contrasts side by
side. For each rule report classified coverage, abstention, all classification
errors, false promotion (better predicted, target not better), false rejection
(tie/worse predicted, target better), and separate positive opportunities missed
through abstention. Per-control deployment uses the alternative only when better
is reported and otherwise retains mean. Report pairwise-best endpoint regret;
abstentions can incur opportunity loss. State selection among reported better
actions uses the largest reported effect, fixed control order breaks ties; retain
mean if none. Report regret against the full-horizon best distinct action.

Use per-seed-block summaries, paired differences, and full counts. No new
confirmatory p-values; no independence assumption for nested states or policies.
Budget and margin sensitivity are descriptive, not rule-tuning sets. A lower
classification error achieved through abstention is not itself superiority.

## Numerical/engineering checks and accounting

Before any diagnostics, select the first six warm points in seed block10. Repeat
their 100x50 solves and evaluate the same coarse parameterization at200x100 (rmin
scaled from2 to4). Record repeatability, raw compliance, and mesh sensitivity.
This two-resolution check is not mesh-convergence proof. Point-load/discretization
effects may exceed the illustrative decision margin; if so, claims remain about
the fixed discrete optimization problem, not resolved physical improvements.

Maximum4000 new physics attempts, including warm/source history, probes, all
oracle branches, repeats, mesh checks and failures. Stop on failure or cap. Every
PRE and LABEL is fsynced; completed blocks are hash-verified before resumption.
Incomplete blocks require a separately published recovery plan and accounting.
All ten blocks are retained; no extra samples from any replay or verification.

## Authorship and contribution limits

This release evaluates a concrete heuristic and evidence contract. It does not
certify novelty, superiority, convergence, industrial engineering validation or
journal acceptance. Code assistance, experimental suggestions and evidence
generation are recorded for author review. Authors must verify code and results,
independently assess scientific contribution, and prepare the manuscript argument
and accurate AI disclosure under the current publisher policy. Existing manuscript
and PDFs are not silently rewritten by this protocol release.
