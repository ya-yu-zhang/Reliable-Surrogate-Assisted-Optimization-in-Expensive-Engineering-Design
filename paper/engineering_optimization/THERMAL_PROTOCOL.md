# Prospective decision-usefulness verification protocol

Status: protocol frozen before thermal optimization labels. No thresholds will be tuned after observing results. This is a bounded verification study, not a promised positive result or a new universally superior optimizer.

## Journal criterion and study purpose

Engineering Optimization's official scope requires innovation in optimization and strong engineering applicability, including decision-support methods. Its 50th-anniversary editorial likewise calls for clear advances in formal optimization with practical applicability. Neither source prescribes a number of benchmark domains or requires every contribution to be a new optimizer.

Sources checked 2026-10-11:
- https://www.tandfonline.com/action/journalInformation?journalCode=geno20
- https://www.tandfonline.com/doi/full/10.1080/0305215X.2025.2450132

The existing audit has clear evidence objects and cost allocation, but its incremental value over ordinary diagnostics and strategy ranking remains uncertain. This study tests a concrete, prespecified promotion gate against ordinary pilot-endpoint selection and fixed policies at equal deployment budgets. Positive engineering benefit is an empirical question. A second physical model establishes limited structural-to-thermal breadth, not industrial qualification or universal transfer.

## Physical problem

Authored dimensionless steady conduction model, not a published benchmark or EngiBench problem: unit square; temperature zero on all four boundary sides; unit integrated heat input. Source is a Gaussian of width 0.08 centered at (0.5,0.5) or (0.75,0.25), normalized on each mesh. Twelve equal-area zones in a 3-by-4 partition have densities obtained by logistic projection to exactly 0.35 mean material fraction. Conductivity is k=1+19*rho^3. All variables lie in [0,1]. Minimize source-weighted temperature (thermal compliance). No safety, peak-temperature, experimental validation, manufacturing, or real execution-expense claim is made.

The 24-by-24 finite-volume grid uses harmonic interior face conductance and half-cell boundary distances. Manufactured-solution convergence, symmetric positive definiteness, heat conservation, nonnegative temperatures and material-volume checks precede optimization. Mesh checks compare prespecified uniform and two fixed material designs at 24/48/96 for both sources; they are verification calls, outside deployment budgets and fully counted. Model selection and algorithm settings will not be changed in response to these labels; a failed verification stops the experiment.

## Search protocol and information boundary

Twenty independent cases: ten scrambled-Sobol initializations for each source condition. Each workflow pays 96 physical evaluations. Fixed-policy comparators are posterior mean, EI and LCB. The common surrogate is normalized GP, isotropic Matérn 5/2, fixed length scale 0.4, alpha=1e-6; hyperparameters are not fitted. EI uses xi=0.01 times training standard deviation; LCB uses kappa=2. A fresh 256-point Sobol pool is generated each step. These settings differ from the beam studies and are held identical across thermal workflows. They limit any comparative optimizer claim.

Both selectors pay 24 common initial observations plus 8 steps for each of the three arms (24 pilot calls). Simple selection picks the lowest pilot incumbent with priority mean/EI/LCB. The audit gate promotes that winning arm only if its incumbent is at least 2% lower than mean at all pilot checkpoints 4, 6 and 8; otherwise it retains mean. The gate implements temporal corroboration; it is an illustrative, prespecified operational rule, not a claim that this threshold is optimal or theoretically certified. Two selectors receive exactly the same pilot information. The comparison isolates this gate rather than all stages of the original auditing framework.

Selection and all checkpoint evidence are persisted before validation labels. Each selector warm-starts from its selected arm's 32 paid observations, then performs 48 further evaluations in a new pool namespace. Other arms' paid designs remain eligible for the final best-paid objective but are not put in the selected GP. Fixed policies receive 24 initial observations and 72 further evaluations. Validation candidate streams use the same deterministic seed rules across workflows. Future labels are never used for selection. Pilot reuse is explicitly warm-start search, not training on external withheld diagnostic labels.

## Complete cost and reporting

Actual execution per case: 24 common initial + 24 common pilot + 2*48 selector continuations + 3*72 fixed-policy continuations = 360 calls. Sharing deterministic initial/pilot solves across experimental comparators saves duplicate execution; it does not reduce their individual 96-call deployment cost. Global optimization cap: 7200 solves. Failures count as attempts and stop the affected experiment; no automatic rerun or replacement seed. Verification calls and any recovery calls are separately recorded.

Primary endpoint is the lowest objective among every physically evaluated design available to each workflow, including all selector pilots. Report paired audit-versus-simple and audit-versus-each-fixed relative differences (audit/comparator-1)*100, condition-wise medians and full per-case rows, wins/ties/losses with relative tolerance 1e-10, and realized policy choices. Negative differences favor audit. Report initial-to-final improvement, gate disagreement frequency and whether disagreements help or harm under independent continuation. No new confirmatory p-values, retrospective threshold tuning, or best-of-fixed oracle presented as a deployable baseline. Timing is descriptive runtime on this implementation, not measured industrial expense. All 20 cases, raw pre/label journals, environment and hashes are released.

Results will be supplied as an evidence addendum for author scientific review. AI must not draft manuscript sections or formulate the authors' scientific argument under the publisher's current policy. Authors must independently assess the method, claims and prior AI-use history. No numerical AI-detector target is part of this protocol.
