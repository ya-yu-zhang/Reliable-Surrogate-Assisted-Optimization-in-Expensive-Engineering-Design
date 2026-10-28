# Decision-consequence auditing for surrogate-assisted optimization in expensive engineering design

The repository keeps its original name; the paper title was narrowed on 20 October 2026.

This repository contains the manuscript sources, experiment implementation,
configurations, analysis utilities, and tests for the decision-consequence
auditing framework studied in the accompanying paper.

## Current manuscript revision

The active target is **Engineering Optimization**. The paper title is
*Decision-consequence auditing for surrogate-assisted optimization in expensive
engineering design* (repositioned on 2026-10-19 from the earlier "Reliable ..." title;
see `paper/engineering_optimization/CONTRIBUTION_POSITIONING_20261019.md`). The
submission source of record is the Markdown/Word track:

- `paper/engineering_optimization_manuscript.md` and
  `paper/engineering_optimization_supplementary.md`
- built artifacts `paper/eo_submission/EO_submission_manuscript.docx`,
  `EO_supplementary_materials.docx` and `EO_cover_letter.docx`
  (`python src/build_eo_docx.py`, `python src/build_eo_submission_extras.py`)

That track carries seven numbered main tables, 33 supplementary tables and a
23/27-page render. `paper/engineering_optimization/EO_manuscript.tex` and
`EO_supplementary.tex` are a frozen author-review artifact, not the submission
source: they retain the later evidence tables (budget audit, thermal record,
paired grid, common continuation) that the submission track does not report. Do not
regenerate the LaTeX source from the Markdown without porting the reference and
evidence fixes listed in `source_build_check.json`.

The 2026-10-13 revision supplies the frozen conditional-audit algorithm,
same-target operational comparisons, intact adverse results, and a separate
conditional-results subsection. See `submission_revision_20261013/` within the
paper directory for the core-object comparison, response record and delivery
manifest. `work_status.json` records the active boundaries.

All authors have approved the manuscript (recorded 2026-10-19). Novelty sufficiency is not certified, and
`submission_ready` remains false pending the scientific decisions. The AI-use record is
copyediting and language refinement only; earlier notes asserting draft assistance were
incorrect. No new physics was acquired for this revision. Its active reproduction entry
points are:

```sh
python -m src.compact_budget_audit_records --target .
python -m src.analyze_review_revision
python -m src.analyze_operational_comparison
python -m src.integrate_submission_revision
```

Earlier Markdown and build scripts record prior stages.

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

The `cmc_*` sources and compiled PDFs keep an earlier manuscript formatting.
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


