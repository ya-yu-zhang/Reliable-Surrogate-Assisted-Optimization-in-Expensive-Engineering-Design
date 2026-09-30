# Reproducibility Guide

## Environments

The experiments were executed with Python 3.12. Dependency sets are separated
to avoid changing frozen numerical environments:

- `requirements.txt`: core experiments;
- `requirements-baselines.txt`: GP-EI and TuRBO references;
- `requirements-application.txt`: engineering application;
- `requirements-application-gp.txt`: GP-based application controls;
- `requirements-reporting.txt`: reporting utilities.

Exact environment exports and hardware information are retained in this
directory. Paths in the implementation are repository-relative. External
programs such as Pandoc, Poppler, and a TeX distribution must be available on
`PATH` when document builders are used.

## Reproducing experiments

Create an isolated Python 3.12 environment and install the dependency set for
the target experiment. The principal development and mechanism runs are:

```powershell
python -m src.experiment --config configs/development.json
python -m src.experiment --config configs/mechanism.json
```

Each run records its configuration fingerprint, seed, evaluation sequence,
and completion summary. Existing complete trajectories are skipped. A partial
trajectory is accepted only through the corresponding recovery and integrity
checks implemented in `src/` and `tests/`.

## Results and storage

The complete raw output tree is approximately 13.6 GB and is not stored in the
Git repository. Generated results belong under `results/`, which is ignored by
Git. Manuscript tables and figures are generated from audited summaries rather
than manually entered values.

## External implementations and templates

Third-party author repositories used for comparisons are not vendored. Their
method names, source revisions, and adaptations are documented in the
manuscript and supplementary material. Publisher Word and LaTeX templates must
be downloaded separately from the journal; local copies belong under
`artifacts/`, which is ignored.
