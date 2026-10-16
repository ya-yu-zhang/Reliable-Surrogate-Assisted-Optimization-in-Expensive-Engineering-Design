# Certified finite-menu rollout: code and numerical data

This profile contains the final lazy response-stability algorithm, its clean engineering training inputs and its complete saved numerical execution record. It is a file allowlist with hashes, prepared without generating an archive or changing repository visibility. Paths below are relative to the repository root.

## Method and evidence

The algorithm selects a first design from a supplied finite menu under an affine raw-response mean continuation. Local response-stability proofs identify continuations; positive terminal-reward bounds enclose uncomputed contributions. A checked inequality accepts a first action to model-value tolerance `m0/1000000`, or the computation returns unresolved.

Code, protocol, tests and 43 clean inputs were committed before execution at `8de86bbe1aeb1568bba754609cf10b8d093094c8`; numerical records were saved at `578e00482aff3d65bde4bd422b60c527803e6e22`. The scientific baseline remains `58f539c2d0738b20c7d0d4889fe8d808a03a3019`. The paper's prose revision is recorded at `a7f94484d5858e0730b86275c48c559d99fde8e0`.

| Quantity | Uniform reward | Regional reward |
|---|---:|---:|
| Accepted states | 43/43 | 43/43 |
| Complete response projections | 0 | 0 |
| Cell operations | 640 | 585 |
| Conditional posterior constructions | 161 | 157 |
| Checked seconds | 10.726626 | 12.226469 |

Shared preparation takes 2.724387 seconds. These results concern certified model-value computation on previously observed beam states. Regional bounds reduce requests and take longer in the recorded pass. The corresponding paid engineering outcomes remain mixed.

## Inspect and verify

- Configuration and source/input hashes: `configs/lazy_regional_20261015.json`.
- Clean inputs: `data/lazy_regional_20261015/`.
- Preparation, conditional marginals, cell certificates and frozen decisions: `results/lazy_regional_20261015/`.
- Protocol and pre-execution unit record: `paper/engineering_optimization/contribution_closure_20261015/LAZY_REGIONAL_PROTOCOL.md` and `LAZY_UNIT_CHECK.json`.
- Exact release paths, hashes and license scope: `public_release/MANIFEST.json`.

Verify the selected file bytes and the local import closure without running an optimizer:

```sh
python -m src.verify_public_numerical_manifest
```

Optional numerical reproduction uses Python 3.12, `requirements-positive-rollout-v2.txt`, and a separately installed 64-bit MPFR 4.2.1 shared library. Run only into a fresh directory:

```sh
python -m src.reproduce_lazy_regional_rollout --out results/lazy_regional_reproduction
```

The runner verifies frozen source/input hashes. Reproduction uses no physical solver, bound query or future response. Machine-dependent durations and resource-cap outcomes can differ. The saved post-freeze consistency audit is included; repeating its comparisons to earlier v2 references requires the separately preserved earlier v2 record.

## Licenses and publication

Original selected implementation files are MIT-licensed. Selected original numerical data, protocol and release documentation are CC-BY-4.0. The manifest specifies each file's license; `LICENSE.md`, `DATA_LICENSE.md` and `THIRD_PARTY_NOTICES.md` give the boundaries. Installed packages retain their upstream terms.

This profile excludes manuscript PDFs, publisher assets, render caches, internal work status and large historical archives. Publish the selected file set with a fresh repository history when a public code repository is needed. Preserve the listed source paths and `public_release/MANIFEST.json`, and copy this README to the new repository root as the documented README alias. A branch in the existing private repository does not isolate the repository's other branches or history. This preparation performs no public visibility change, upload, archive packaging or journal submission.
