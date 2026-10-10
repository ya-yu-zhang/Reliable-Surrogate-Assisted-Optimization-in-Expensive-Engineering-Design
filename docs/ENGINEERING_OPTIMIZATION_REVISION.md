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

All reported Markdown table rows match the previous submission exactly.
The revision audit checks the six history signs and citation completeness.
LaTeX working sources use committed vector figures and a generic article
class; they are not an official journal template. No revised PDF compilation
or visual verification is claimed.

```sh
python -m src.build_engineering_optimization_sources
python -m src.audit_engineering_optimization_revision --output paper/engineering_optimization/revision_audit.json
```

## Stage 2 — additional evidence

Priority is a complete audit of candidate-dependent GP acquisitions, with a
bounded alternative-label budget and separate diagnostic accounting. Restore
the original raw GP journals in their documented `results/` paths. Do not
infer missing frozen states from endpoint tables. A positive endpoint is not
by itself an audit promotion. Detailed implementation and protocol are tracked
in `docs/ENGINEERING_OPTIMIZATION_AUDIT_PROTOCOL.md` when available.

## Stage 3 — engineering transfer and submission

Prespecify an additional physically meaningful beam condition, then compare
the same audited policies with a shared initialization and paid-call ledger.
Do not treat varying a random seed as a new physical engineering condition.
Report objective, model-management, and diagnostic times separately; count
all new diagnostic calls in any claim of net savings. New labels and analyses
must not be added to the old prespecified statistical families.

After the added evidence is reviewed, update the text and figures, acquire the
publisher's current permitted template, compile both documents, and inspect
every rendered page. Affiliations for Zhenyu Meng and Jia Zhao require author
confirmation; they have not been guessed. Submission readiness remains false.

## Sources for venue positioning

- Journal aims and scope: https://www.tandfonline.com/action/journalInformation?journalCode=geno20
- Diagnostic benchmarking: https://doi.org/10.1080/0305215X.2024.2381818
- Reliable regional Kriging: https://doi.org/10.1080/0305215X.2018.1446084
- Editorial emphasis on innovation and engineering applicability:
  https://doi.org/10.1080/0305215X.2025.2450132
