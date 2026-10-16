# Current manuscript and numerical review entry — 16 October 2026

Read the saved evidence before considering reproduction. This revision changes manuscript organization and scientific explanation; it performs no new algorithm run, posterior reconstruction, physical evaluation, bound query, fit, retry, replacement or independent optimization sample. Both witness attempts are exhausted. Do not invoke physical or optimization experiment entry points for this review.

The 16 October prose revision places the current proofs in Supplement A1, retains historical S numbering and all recorded numerical rows, and synchronizes the current 142-word abstract. The six-point prose, figure and template review is recorded in `submission_20261014/style_scope_figures_20261016/REVIEW_AND_CHANGES.md`.

## Read the current paper

| Purpose | Repository path |
|---|---|
| Main paper | `submission_20261014/source/paper/engineering_optimization/EO_manuscript.tex` |
| Final problem, algorithm, propositions and assumptions | `submission_20261014/source/paper/engineering_optimization/integrated_evidence/final_method_20261016.tex` |
| Engineering setting and final paired results | `submission_20261014/source/paper/engineering_optimization/integrated_evidence/lazy_regional_results_20261015.tex` |
| Proofs and separate historical evidence | `submission_20261014/source/paper/engineering_optimization/EO_supplementary.tex` and its inputs |
| Bibliography | `submission_20261014/source/paper/engineering_optimization/EO_references.bib` |
| Scientific assessment and remaining preparation | `submission_20261014/review_20261016/FINAL_SCIENTIFIC_REVIEW.md` |
| Title, abstract, authors and the two missing affiliations | `submission_20261014/PORTAL_FIELDS.json` |

The main method is local response discovery with on-demand conditional posteriors and positive-completion selection. Earlier full-projection methods and saved-certificate transformations are supporting stages, not interchangeable implementations or independent validation. Older manuscript builders can overwrite the final narrative; do not run them to prepare this version.

## Inspect the final numerical record

The immutable scientific baseline is `58f539c2d0738b20c7d0d4889fe8d808a03a3019`. The authorized private branch is `research/contribution-closure-20261014-c5d11c`. Code, protocol, tests and 43 clean snapshots were committed **before execution** at `8de86bbe1aeb1568bba754609cf10b8d093094c8`. The complete final numerical record was saved at `578e00482aff3d65bde4bd422b60c527803e6e22`.

| Purpose | Repository path |
|---|---|
| Core and original runner | `src/lazy_regional_rollout.py`, `src/run_lazy_regional_rollout.py` |
| Pre-execution protocol, limits and hashes | `configs/lazy_regional_20261015.json`, `paper/engineering_optimization/contribution_closure_20261015/LAZY_REGIONAL_PROTOCOL.md` |
| Necessary unit checks and saved execution record | `tests/test_lazy_regional_rollout.py`, `paper/engineering_optimization/contribution_closure_20261015/LAZY_UNIT_CHECK.json` |
| Clean training inputs | `data/lazy_regional_20261015/` — 43 files |
| Actual reconstructed preparation | `results/lazy_regional_20261015/preparation/` — 43 files |
| Local domains, queried marginals, cell certificates and reader results | `results/lazy_regional_20261015/certificates/` — 86 files |
| Summary and decision freeze | `results/lazy_regional_20261015/analysis.json`, `decisions.json`, `decisions_frozen.json` |
| Subsequent consistency and tolerance audit | `results/lazy_regional_20261015/postfreeze_consistency.json`, `src/verify_lazy_regional_records.py` |

Both routes accept 43/43 previously seen states. Regional versus uniform reward uses 585 versus 640 cell operations and 157 versus 161 conditional posterior constructions, taking 12.226469 versus 10.726626 checked seconds. Shared preparation is 2.724387 seconds. Both avoid complete continuation projection. This establishes the finite-menu computation, not a time advantage, improved physical outcomes or independent validation.

The frozen reader shares arithmetic and curvature code with the producer. The separate saved audit checks the input-derived tolerance and regret; ordinary references and parameter overlap are consistency evidence. Queried finite posterior arithmetic is certified under the stated assumptions; unqueried full-joint covariance, kernel-function error, statistical calibration and physical error are outside that certificate.

## Source-only check and optional numerical reproduction

The current preparation check reads sources and saved records, runs BibTeX, verifies references and hashes, and writes only current source-review reports. It does not rebuild a posterior, run the algorithm or build a PDF:

```sh
python -m src.verify_rollout_closure_sources
```

Its record is `submission_20261014/finalization_20261016/SOURCE_VERIFICATION.json`; its current-file manifest is `submission_20261014/finalization_20261016/REVIEW_MANIFEST.json`. Earlier release manifests describe their own commits. Their historical manuscript hashes are not hashes of this revised manuscript. Frozen source/input and numerical-result hashes remain independently checked.

Optional algorithm reproduction is unnecessary for preparing this paper and was **not executed for this revision**. Use Python 3.12, the dependencies in `requirements-positive-rollout-v2.txt`, and MPFR 4.2.1 with a 64-bit ABI. The runner checks source/input hashes, uses one numerical thread and refuses an existing output directory. Run from the repository root with a fresh path below `results/`:

```sh
python -m src.reproduce_lazy_regional_rollout --out results/lazy_regional_reproduction
```

Do not point it at frozen results. Durations and resource-limit outcomes can vary by machine. Reproduction uses clean training data and no physical solver or future responses.

## Availability and submission boundary

The repository is private; its URL is provenance and does not grant reviewer access. Access has not been arranged. The current finite-menu numerical record is self-contained with its declared code dependencies and clean inputs; it does not require the lost old positive-response program or three missing paired-grid raw files. Full historical solver-journal checks still require those journals; paid-outcome extracts do not replace them. The manuscript retains these disclosures.

Publisher class/style files and historical figure assets retain their own availability and rights. A source/BibTeX check is not compilation or visual-layout approval. The selected public numerical profile now has scoped MIT code and CC-BY-4.0 data grants in `LICENSE.md` and `public_release/MANIFEST.json`. No PDF/ZIP, template recovery, repository visibility change or journal submission was performed. Affiliations b/c and current layout remain unfinished. Existing funding/conflict wording is inherited from the supplied manuscript. No all-author approval task is reinstated.

The final closeout record is `submission_20261014/finalization_20261016/PROJECT_CLOSEOUT.md`. The runtime lacks article.cls, so current layout verification remains outstanding.
