# Reliable Surrogate-Assisted Optimization in Expensive Engineering Design

This repository contains the manuscript sources, experiment implementation,
configurations, analysis utilities, and tests for the decision-consequence
auditing framework studied in the accompanying paper.

## Current manuscript revision


The current private-branch working draft is **Local Response Stability for Certified Two-Step Rollout in Engineering Optimization**. Active sources are `submission_20261014/source/paper/engineering_optimization/EO_manuscript.tex` and `EO_supplementary.tex`. The immediately preceding main is preserved byte for byte under that directory's `archival/EO_action_sets_and_direct_rollout_20261015.tex`.

The current v2 implementation has a complete numerical record: both methods pass on all 43 existing engineering states with matching choices; full projections are 114 versus 25. The local checked stage is slower in the single paired pass (5.469358 s versus 4.933306 s), and paid engineering outcomes remain mixed. No time-saving or policy-superiority claim is made.

Code, protocol and all 43 fixed-input snapshots were saved before execution at `f4f352acdb5ccbc98ead05455d2083ccc72acca3`; all new per-state results were saved at `79f2cfa07082c5cb6b94075d5220175b8fc4e2ab`. See `paper/engineering_optimization/contribution_closure_20261015/CONTRIBUTION_AND_APPLICABILITY_V2.md` and `results/positive_rollout_v2_20261015/RELEASE_MANIFEST.json`. The old positive-scope originals remain missing; v2 is a new implementation and execution, not their recovery.

The scientific baseline remains `58f539c2d0738b20c7d0d4889fe8d808a03a3019`; work is on `research/contribution-closure-20261014-c5d11c`. Canonical status is `paper/engineering_optimization/work_status.json`. V2 charges 43 positive-root and 114 raw-selector fixed-kernel constructions plus 86 method/state runs. Physical evaluations, bound queries, hyperparameter fits and new independent samples are zero. No PDF/ZIP is created or uploaded.

Numerical reproduction uses the released snapshots and `python -m src.reproduce_positive_rollout_v2 --out results/positive_rollout_v2_reproduction`. Historical-journal revalidation for paid outcomes needs the corresponding journals; the checked outcome extracts are included. Current source checks do not certify visual layout. Affiliations b/c, factual submission fields and reviewer access remain pending; `final_submit_ready` remains false.

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


