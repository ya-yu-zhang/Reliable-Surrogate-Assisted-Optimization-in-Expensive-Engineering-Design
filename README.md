# Reliable Surrogate-Assisted Optimization in Expensive Engineering Design

This repository contains the manuscript sources, experiment implementation,
configurations, analysis utilities, and tests for the decision-consequence
auditing framework studied in the accompanying paper.

## Current manuscript revision

The active private-branch draft is **Local Response Stability for Certified Two-Step Rollout in Engineering Optimization**, under `submission_20261014/source/paper/engineering_optimization/`. The final development implements lazy response-region discovery and on-demand conditional posteriors from cleaned training snapshots; it does not read historical action domains, previous posteriors or old integral leaves.

Code, protocol, four passing tests and all 43 clean inputs were committed before execution at `8de86bbe1aeb1568bba754609cf10b8d093094c8`. One paired run accepts all 43 states in both routes with zero complete response projections. Regional bounds reduce cell operations 640 to 585 and conditional posterior constructions 161 to 157, but the checked stage is slower: 12.226469 s versus 10.726626 s. Shared preparation is 2.724387 s. No time advantage or engineering-policy superiority is established.

See `paper/engineering_optimization/contribution_closure_20261015/LAZY_REGIONAL_RESULT_AND_CLOSURE.md`, `configs/lazy_regional_20261015.json` and `results/lazy_regional_20261015/`. Reproduce only in a fresh directory with `python -m src.reproduce_lazy_regional_rollout --out results/lazy_regional_reproduction`. Existing records do not need another run for manuscript preparation.

The numerical guarantee covers positive completions of uncomputed conditional laws and the queried finite posterior marginals; it does not certify a full unqueried covariance, statistical calibration or physical error. CPU costs include 43 training matrices, 114 raw-selector systems and 361 validated positive-posterior construction calls across the paired workflow. Physical evaluations, bound queries, hyperparameter fits and new independent samples are zero. No PDF/ZIP is created or uploaded.

Earlier v2 and regional certificate-transformation records remain separate: sources/inputs were frozen at `f4f352ac`, v2 results at `79f2cfa0`, and the regional theory/transform at `3b3f8a5c`. Their projection, width and timing statistics must not be combined with the final algorithm's results. Missing historical originals and all unfavorable evidence remain disclosed.

The scientific baseline remains `58f539c2d0738b20c7d0d4889fe8d808a03a3019`; the authorized branch is `research/contribution-closure-20261014-c5d11c`. Research is closed at this bounded scope, with no more experiments planned. Required author facts, private reviewer access and current layout remain unfinished; `final_submit_ready` is false. Journal acceptance or sufficient originality is not certified.

The 16 October source integration presents one final algorithm contract and promotes the beam problem, menu sizes, fixed kernel and numerical assumptions into the main text. Start with [the current review entry](submission_20261014/REVIEW_REPRODUCTION.md) and [the final scientific review](submission_20261014/review_20261016/FINAL_SCIENTIFIC_REVIEW.md). The source/hash check writes a new dated review record and preserves all frozen numerical result files. Older manuscript builders restore older presentations; do not run them over this final source. No new algorithm, numerical replay, physical response or experiment is part of this revision.

The current prose revision follows direct, evidence-led academic writing. Proofs precede the historical supplement, the abstract contains 141 words, and all 460 pre-edit numerical table rows and 45 display equations are retained. Current source verification and hashes are in `submission_20261014/finalization_20261016/`.

A selected numerical code/data profile is prepared under `public_release/MANIFEST.json`: 209 files, approximately 3.55 MB, with scoped MIT software and CC-BY-4.0 original research-data terms. See `LICENSE.md` and `public_release/README.md`. The reviewed profile excludes historical PDFs, publisher assets and internal work records and is intended for fresh public repository history. The existing private repository has not been made public.

### Historical 13 October preparation record

The active target is **Engineering Optimization**. Current manuscript sources are
`paper/engineering_optimization/EO_manuscript.tex` and `EO_supplementary.tex` in
that directory, with publisher-template provenance recorded alongside them.
The 2026-10-13 revision supplies the frozen conditional-audit algorithm,
same-target operational comparisons, intact adverse results, and a separate
conditional-results subsection. See `submission_revision_20261013/` within that
paper directory for the core-object comparison, AI-use history audit, response
record and delivery manifest. `work_status.json` records the active boundaries.

The all-author approval task is excluded by the user's explicit instruction;
this is not a claim that approval occurred. Affiliations b/c remain unfilled at
the user's choice. Novelty sufficiency and historical AI-policy applicability
are not certified, and `submission_ready` remains false. No new physics was
acquired for this revision. Its active reproduction entry points are:

```sh
python -m src.compact_budget_audit_records --target .
python -m src.analyze_review_revision
python -m src.analyze_operational_comparison
python -m src.integrate_submission_revision
```

Earlier Markdown and build scripts record prior stages. The active TeX sources
and versioned delivery manifest identify the current manuscript.

The subsequent P0/P1 development release is
`paper/engineering_optimization/monotone_development_20261013/`. It implements
prefix-only monotone terminal-category bounds and a separate selection
certificate. The h0-directed candidate did not improve on certificate-aware
simple orders; selected-branch completion erased its previous-holdout request
savings. No new independent experiment was started. Reproduce this development
screen with `python -m src.analyze_monotone_development` after restoring the
existing budget and common-continuation records. The candidate is not added to
the manuscript as an established optimization contribution.

The next reviewer-driven development screen is
`paper/engineering_optimization/physical_bound_screen_20261013/`. Its protocol
was published before two reference-displacement solves. Classical scalar and
two-dimensional trial bounds were screened on1720 candidates across all old
seed groups; all43 nontrivial states failed root-tie sharpness for the declared
full-pool operator. No independent optimizer experiment was started. Reanalyze
with `python -m src.physical_bound_screen --analyze`; the original manuscript,
statistics and adverse findings remain intact.

The prospective GP audit is specified in
`docs/ENGINEERING_OPTIMIZATION_AUDIT_PROTOCOL.md` and implemented in
`src/engineering_optimization_gp_audit.py`. It freezes 120 common states and
limits new diagnostic finite-element calls to 480. The completed experiment uses
138 new diagnostic calls after permitted deterministic reuse. A separately
frozen transfer protocol is in `docs/ENGINEERING_OPTIMIZATION_TRANSFER_PROTOCOL.md`.
Its 20 complete retained cases cost 18,120 FE attempts; an earlier complete batch
had to be recovered without changing the protocol and is also charged. Including
102 solver checks, total additional revision cost is 36,480 FE attempts.
The execution boundary is recorded in `paper/engineering_optimization/work_status.json`.

The curated release contains all 60 author-supplied GP files in a byte-preserving
text bundle and all 20 transfer journals in a lossless compact record format.
Restore and validate these records without acquiring new FE labels:

```sh
python -m pip install -r requirements-engineering-gp-audit.txt
python -m src.restore_engineering_gp_records
python -m src.analyze_engineering_optimization_gp_audit --released
python -m src.compact_engineering_transfer_records
python -m src.analyze_engineering_optimization_transfer
python -m src.plot_engineering_optimization_transfer
```

The plotting command uses Matplotlib (installed through the engineering reporting
dependencies) and regenerates both PNG and SVG figures. The PNGs are required
by the working LaTeX sources; SVGs are committed for direct manuscript viewing.
The compact GP check validates chosen vectors, source hashes, label order and
immediate utilities. It does not independently replay the full candidate pools
or posterior; the original full-snapshot check and preparation implementation
remain available separately. Neither restoration command reruns a simulator.

The `cmc_*` sources and compiled PDFs preserve the previous submission state.
They contain the documented Figure 3/S3 direction-text error and are not the
current working manuscript. The new sources correct that error without changing
reported experimental values. Historical hashes and frozen experiment code
are retained.

## Repository layout

- `src/`: optimization, auditing, analysis, and manuscript-build code.
- `configs/`: frozen experiment configurations.
- `tests/`: integrity, accounting, recovery, and reporting checks.
- `paper/`: manuscript sources, figures, and compiled research drafts.
- `docs/REPRODUCIBILITY.md`: environment and reproduction guidance.
- `requirements*.txt`: dependency sets for the core, application, baseline,
  and reporting environments.

## Scope of the public release

Historical raw experiment outputs are about 13.6 GB and are not committed to Git.
The curated revision inputs, intervention ledger and compact transfer journals
are explicit exceptions, with per-file and segment checksums. Historical outputs can
be regenerated from the frozen configurations and seeds. Local virtual
environments, interrupted-run archives, machine-specific logs, publisher
templates, and third-party author repositories are also excluded.

The CMC submission builders expect the official journal templates to be
obtained from the publisher and placed in the local `artifacts/` directory.
That directory is intentionally ignored because this repository does not grant
redistribution rights for publisher assets.

## Quick start

Python 3.12 is recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q tests
```

Representative experiment entry points are:

```powershell
.\.venv\Scripts\python.exe -m src.experiment --config configs/development.json
.\.venv\Scripts\python.exe -m src.experiment --config configs/mechanism.json
```

The complete workflow, environment separation, output accounting, and
large-result handling are described in `docs/REPRODUCIBILITY.md`.

## Independent budget-audit validation

The frozen protocol, code and configuration were published at commit
`460657e8c6507fcf41d67a1b8ce9463cfa7622bf` before collecting new labels. Ten new
seed blocks provide30 dependent source states and two common continuation rules.
The full2134 new physics attempts, unfavorable allocation comparisons, uncertainty
and numerical limitations are retained. Primary adaptive allocation did not improve
over fixed allocation; at budget12 it classified fewer contrasts than fixed depth.

See `paper/engineering_optimization/budget_audit/README.md` for restoration and
verification, and `EVIDENCE.md` in the same directory for measured results.
This is an author-review evidence extension. It does not certify novelty, optimizer
superiority, physical accuracy of the illustrative margin, or submission readiness.

## Citation

The final bibliographic record will be added after publication. Until then,
please cite the manuscript title and this repository revision.

## License

No open-source license has yet been assigned. Copyright remains with the
authors. Public visibility does not grant permission to reuse third-party
assets or redistribute publisher templates.


