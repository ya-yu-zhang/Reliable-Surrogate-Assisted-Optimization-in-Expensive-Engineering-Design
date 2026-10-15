# Scoped review reproduction

The sole current scientific baseline is `58f539c2d0738b20c7d0d4889fe8d808a03a3019`. The data-and-code archive is supplied for review of the GP coefficient-band operator and the existing bounded decision evidence; it is not the full historical project.

Use the environment in `runtime_record.json`. The recorded verification used Python 3.12, NumPy 2.3.5, SciPy 1.17.0, scikit-learn 1.8.0 and Matplotlib. There is no need for the engineering solver for the current verification. From the extracted archive root:

```sh
python3 -m src.prepare_gp_attachment
python3 -m src.verify_project_closure
python3 -m src.check_gp_envelope_downstream
```

The included test record reports 31 scoped tests on the unchanged scientific implementation. Optional rerun:

```sh
python3 -m unittest discover -s tests -v
```

The checked historical timing record is supplied. Optional retiming reads the same frozen bands and creates new machine-dependent stage timings:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python3 -m src.verify_and_benchmark_gp_envelope --out results/gp_envelope_retimed --repeats 3
```

Do not invoke a physical-bound, witness-execution, paired-grid solver or independent optimization entry point for this scoped reproduction. The two witness attempts are already consumed; no retry or replacement is performed.

The private repository's URL is provenance, not reviewer access. The archive preserves the original GP ZIP bytes, its manifest and both witnesses. Selected exact sources resolve through baseline, restored, GP attachment and baseline_more. The 22 recovered paired-grid records and the three historical output tables are included as supporting material, with the three missing final raw files identified by hashes. Those paired-grid tables cannot currently undergo complete independent raw-log reconstruction; no synthetic replacement files are created.

`revision/` retains the earlier closure overlay to reproduce its existing verification. `submission_20261014/source/` is the active journal preparation copy, adding evidence-availability disclosure and front-matter adjustments while preserving numerical rows and the bibliography. To reconstruct those source edits:

```sh
python3 -m src.prepare_submission_20261014
```

The official publisher class and bibliography style are excluded. Obtain the official bundle `https://files.taylorandfrancis.com/InteractCADLaTeX.zip` identified in REPRODUCE_PROJECT_CLOSURE.md and place interact.cls and tfcad.bst beside the active TeX. A working TeX Live can compile:

```sh
cd submission_20261014/source/paper/engineering_optimization
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build/main EO_manuscript.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build/supplement EO_supplementary.tex
```

Funding and conflict statements are inherited author facts, not established by code checks. The affiliations b/c and venue-specific writing-policy applicability remain pending. The packet is not a record of a journal submission or a public data release.

After the preparation builder, apply the final read-only diagnosis and source addition:

```sh
python3 -m src.finalize_contribution_20261014
python3 -m unittest tests.test_h1_bound_bottlenecks -v
```
This reads already recorded bounds only. It adds no physical evaluation and leaves the original efficacy gate false.

## Current 15 October contribution

The current manuscript evaluates the integer filter, independently optimized pairwise control and scalar-certificate router. The earlier full manuscript remains in archival/EO_full_evidence_20261014.tex. Do not run the older preparation builder alone, which restores the earlier presentation.

With the existing GP attachment, the ten new numerical test groups and read-only routing check are:

```sh
python3 -m unittest tests.test_filtered_exact_action_sets tests.test_h1_certificate_routing -v
python3 -m src.verify_h1_certificate_routing
```

Recorded comparison inputs/source hashes, 228 case results and certificate hashes are in results/gp_strong_comparison_20261015/. Optional retiming must use a different directory:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python3 -m src.benchmark_strong_action_sets --out results/gp_strong_retimed --repeats 3
```

This reconstructs fixed binary kernels without hyperparameter fitting, new bound queries, physical evaluations or independent optimization samples. The preserved 15 October record replaces unpreserved earlier timing claims. The router returns only its specified scalar Boolean certificate predicate. H1/H5/independent gates remain unchanged.

Per the user's new instruction the private branch saves source text and derived results. PDFs/ZIPs are kept locally by the user and supplied again when needed. No PDF/ZIP upload is part of this increment.
