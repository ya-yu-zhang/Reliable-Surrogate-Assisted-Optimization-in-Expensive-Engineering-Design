# Engineering Optimization revision

Revision opened: 2026-10-10. Baseline: `4161c59f65771e889699c4596dd89b7b8496dc26`.

## Stage 1 — completed source revision

The active sources are `paper/engineering_optimization_manuscript.md` and
`paper/engineering_optimization_supplementary.md`. The CMC sources, compiled
PDFs, original experiment implementations, and their historical hashes remain
the prior submission record. They are not the current revision.

- Corrected Figure 3 and Figure S3 direction prose. The definition is
  **selected-point failure minus candidate-pool failure**. Fixed03 is positive
  and greedy is negative in all three validation dimensions. For D=10,
  0.1215 - 0.0479 = +0.0736 and 0.0903 - 0.1018 = -0.0115.
- Replaced CMC-specific venue positioning with engineering model-management
  and diagnostic-benchmarking context. Added relevant Engineering Optimization
  references 34–35; retained scientific references regardless of venue.
- Distinguished decision reliability from probabilistic structural reliability.
- Clarified that immediate improvement cannot universally reject exploration.
  Calibration testing applies to mechanisms making a calibration claim.
- Added an inconclusive outcome and explicit diagnostic-cost accounting.
  The conceptual revision does not change the historical prespecified gate,
  frozen optimizer settings, measured endpoints, or statistical comparisons.
- Removed unsupported implications of demonstrated audit savings. Existing
  positive controls establish optimizer context, not full framework validation.
- Updated availability to reflect public sources/configurations and excluded
  raw outputs; no new data release or license is claimed.

All historical numerical Markdown table rows match the previous submission exactly.
The revision audit checks the six history signs and citation completeness.
LaTeX working sources use committed vector figures and a generic article
class; they are not an official journal template. No revised PDF compilation
or visual verification is claimed.

```sh
python -m src.build_engineering_optimization_sources
python -m src.audit_engineering_optimization_revision --output paper/engineering_optimization/revision_audit.json
```

## Stage 2 — completed frozen-state evidence

The supplied 30 GP histories and 30 summaries are now verified and released in a
byte-preserving text bundle. Input hashes and 120 intervention choices were
committed at `f1c9bbdebc35071bd935d0b11c92857f5e07201e` before acquiring
new diagnostic labels. The source release repair is commit
`71e074945262e1dbfc223726c7216e5415385ddc`; it replaces an incomplete binary
transfer, preserves every original file byte, and does not alter scientific inputs.

The 480 policy-state choices contain 261 within-state distinct actions. After
120 permitted source-response reuses and three diagnostic-cache reuses, 138
new FE calls determine all prespecified immediate utilities. GP prediction
replay passes the unchanged 1e-8 tolerance in all 120 states. The separate solver
check costs 102 attempts: 42 initial checks and 60 retained checks. The retained
comparisons pass a disclosed 1e-6 relative solver tolerance, with maximum
relative difference 4.929e-8. The first-pass solver time was not retained and
is not invented. No diagnostic label enters an optimizer history.

## Stage 3 — completed delayed and engineering-condition evidence

The protocol and code were frozen at
`7555d58b145a2c44b73bab5ec47d0f643a57dde1`. Force positions 0.25 and 0.75
have ten fresh repeats each. They are two conditions of the same beam model,
not validation across independent engineering domains. The isotropic refitted
GP, 1,024-point pool and EI margin differ from the immediate frozen-ARD audit;
these differences are disclosed in the manuscript and Table S27.

Every condition/policy has zero median first-step pilot gain and positive
20-step median gain. The independently seeded, pilot-label-free selected-policy
workflow costs 280 physical calls; a fixed policy costs 200, and the actually
executed full four-policy portfolio costs 626. Selected-policy paired median
final-compliance gaps are 9.014% and 27.217%, with 7/20 exact portfolio-best
matches. Thus a lower call count does not imply equivalent performance. A
secondary best-of-all-paid-design analysis has gaps of 9.014% and 2.116%; it
is identified separately and does not replace the prespecified endpoint.

The retained transfer batch costs 18,120 FE attempts. Loss of access to earlier
complete local journals required unchanged-protocol recovery, recorded before
re-execution at `62560a245a8b804dcff3ce00aa45aae0af9f3884`. The previous
18,120 attempts are also counted. With the 240 immediate/solver attempts, total
additional revision cost is 36,480. All 20 retained endpoints exactly match the
preserved previous endpoint record; original lost journal bytes cannot be
verified and no such claim is made. The compact release at
`ce8e71e62dfef52c25c3754fed161dc8a3402fd7` restores the retained journals
byte-for-byte under the pinned runtime, without new FE calls.

## Stage 4 — contribution and integrated sources

Section 2.3 and Table 1a compare the actual evidence objects with regional
Kriging, diagnostic benchmarking, adjustable-accuracy surrogate studies, frugal
selection, warm-start selection and surrogate-management convergence analysis.
Section 3.5 supplies exact context-point equivalence and an elementary
worst-case query argument. Neither the argument alone nor the failed residual
controller is asserted to be a sufficient stand-alone innovation.

Sections 6.3–6.4, Tables 5–6 and Figure 6 integrate the new experiments. Sections
S9–S10, Tables S26–S32 and Figure S14 disclose all repeats, parameter differences,
fixed-policy comparisons, pilot horizons, retained timings and recovery cost.
Original numerical table rows and statistical families remain unchanged.
The implementation has ten passing integrity tests; the manuscript audit checks
historical values, six direction statements, references and claim boundaries.
Both scientific figures were visually inspected. The source builder regenerates
working LaTeX, but no current submission-format PDF compilation or page-layout
verification is claimed.

The contribution is an executable intervention-and-verification method,
query-allocation rule and engineering cost-performance evidence. It is not a new
acquisition, a universally superior selector, a convergence guarantee, or a
claim of performance-preserving net savings. See
`docs/ENGINEERING_OPTIMIZATION_CONTRIBUTION_EVIDENCE.md` for the claim map.

## Remaining submission work

- Confirm affiliations 2 and 3 and obtain final approval of the revised text.
- Apply the publisher's currently permitted submission format, compile both
  documents and inspect all rendered pages.
- Finalize the release citation and submission declarations.

Novelty sufficiency and acceptance remain editorial decisions. No retrospective
performance threshold, additional p-value, or cross-domain validation claim has
been added to make the findings appear stronger.

## Sources for venue positioning

- https://www.tandfonline.com/action/journalInformation?journalCode=geno20
- https://doi.org/10.1080/0305215X.2024.2381818
- https://doi.org/10.1080/0305215X.2018.1446084
- https://doi.org/10.1080/0305215X.2025.2450132
