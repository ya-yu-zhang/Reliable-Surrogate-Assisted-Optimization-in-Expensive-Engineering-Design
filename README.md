# Reliable Surrogate-Assisted Optimization in Expensive Engineering Design

This repository contains the manuscript sources, experiment implementation,
configurations, analysis utilities, and tests for the decision-consequence
auditing framework studied in the accompanying paper.

## Current manuscript revision

The active target is **Engineering Optimization**. The revised working sources
are `paper/engineering_optimization_manuscript.md` and
`paper/engineering_optimization_supplementary.md`. See
`docs/ENGINEERING_OPTIMIZATION_REVISION.md` for completed corrections,
evidence boundaries, and remaining work. These are revision drafts, not a
submission-ready package. Author affiliations and additional audit validation
remain unresolved.

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

Raw experiment outputs are about 13.6 GB and are not committed to Git. They can
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

