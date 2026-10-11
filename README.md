# Reliable Surrogate-Assisted Optimization in Expensive Engineering Design

This repository contains the manuscript sources, experiment implementation,
configurations, analysis utilities, and tests for the decision-consequence
auditing framework studied in the accompanying paper.

## Current manuscript revision

The active target is **Engineering Optimization**. The revised working sources
are `paper/engineering_optimization_manuscript.md` and
`paper/engineering_optimization_supplementary.md`. See
`docs/ENGINEERING_OPTIMIZATION_REVISION.md` for completed corrections,
evidence boundaries, and remaining work. The contribution comparison is in
`docs/ENGINEERING_OPTIMIZATION_CONTRIBUTION_EVIDENCE.md`. The working sources now
integrate frozen-state GP interventions, delayed policy outcomes, two new beam
force conditions, all-repeat endpoints and recovery-aware evaluation costs.
Final author review, affiliations and submission-format PDF verification remain
pending; the working sources do not guarantee journal acceptance.

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
python -m src.integrate_engineering_optimization_evidence
python -m src.build_engineering_optimization_sources
python -m src.audit_engineering_optimization_revision
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

## Citation

The final bibliographic record will be added after publication. Until then,
please cite the manuscript title and this repository revision.

## License

No open-source license has yet been assigned. Copyright remains with the
authors. Public visibility does not grant permission to reuse third-party
assets or redistribute publisher templates.


