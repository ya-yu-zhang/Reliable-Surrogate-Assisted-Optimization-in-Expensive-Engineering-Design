# Contribution--evidence matrix for independent author assessment

Status: technical assessment and manuscript-edit checklist. Author confirmation
and novelty sufficiency are pending. This is not a drafted article argument.
Baseline release: 062c1b62a773f80cc4383d51a4d6655e9cc3f083.

| Candidate contribution | Existing research already does | Specific implemented object to assess | Evidence | Unsupported extension / author decision |
|---|---|---|---|---|
| Frozen learned-state intervention | Model-management studies and diagnostic benchmarking investigate decisions, dynamics, sensitivity and performance; endpoint-only characterization is inaccurate | Hold training information, fitted kernel and candidate pool fixed; change one first-action rule; record predictions before responses |120 historical GP states;480 named choices,261 within-state distinct choices;138 new FE labels after permitted reuse | No absence-of-prior-art claim. Authors must establish the increment beyond matched-state ablation and existing mechanism diagnostics |
| Exact response / trajectory equivalence | Deterministic memoization and common-random-number comparisons are established tools | Separate exact objective-context/point response equality from the stronger state/kernel/history/continuation/seed equality needed to share a trajectory | Common-continuation76 first-action classes; independent budget validation55 classes; raw hashes and information-boundary replay | Elementary query-count proposition supports a reporting contract, not a convergence/regret theorem or principal mathematical innovation |
| Conditional delayed consequence | Whole-policy runs already measure longer-term optimizer performance | Alter the first action at the same learned state, then use the declared identical continuation; distinguish this target from each policy's own evolving trajectory | Original90 comparisons become46 distinct nonbaseline-action comparisons;7 distinct h0/h5 changes,6 delayed non-ties, concentrated in4 states/4 seed blocks | Neither8 independent discoveries nor universal median advantage; conditional on horizon, kernel, pools and continuation |
| Budget / abstention contract | Adaptive resource allocation and early stopping predate this project, including Hyperband | Complete the declared target before certification; budget-incomplete branches abstain; report coverage, missed opportunities, response requests and physical attempts together | Ten new seed blocks,30 dependent states, mean/EI continuation; budget18 is nonbinding; at12 fixed-depth17/25 vs adaptive9/25 completed | Adaptive allocation was not superior. Completed-oracle zero errors are definitional, not predictive accuracy or population-zero-error proof |
| Engineering applicability boundary | Reliable-region Kriging connects uncertainty to concrete search management; engineering optimization papers assess practical consequences | Measure discrete compliance/thermal objectives and audit the meaning of mesh/context changes | Two extra beam load positions;20 small thermal cases; gate differs twice with tie/loss; selected 14 paired-grid classifications are stable (8 different endpoints, 6 same-endpoint ties); one coarse source-agreement flag remains | One beam family plus a small authored thermal model is not industrial or broad cross-domain validation;0.1% margin lacks physical accuracy certification |
| Reproducible evidence and full paid-call ledger | Benchmark software, seed protocols and reproducibility are established contributions | Lossless record restoration, prefix-only replay, separate training/diagnostic/recovery contexts and independent seed-block accounting |24 relevant local tests; earlier 49 remote file hashes and 7 identical budget-analysis outputs; 25 mesh-release files restored and 3 mesh-analysis outputs identical; 55305 cumulative paid physics attempts | Strong supporting practice, not a substitute for optimization novelty. Source/calibration GP timing was not separately recorded; no end-to-end speedup claim |

## Primary prior-art anchors and retrieval boundary

* Diagnostic benchmarking of many-objective evolutionary algorithms for real-world
  problems, doi10.1080/0305215X.2024.2381818. Its metrics include effectiveness,
  efficiency, reliability, controllability and runtime dynamics. Verified publisher
  text and accessible author-repository article support this description.
* Evolutionary reliable regional Kriging surrogate for expensive optimization,
  doi10.1080/0305215X.2018.1446084. The repository's existing ref35 supplies the
  model-management comparison; no complete algorithm-level replication is claimed.
* Hyperband, JMLR18(185),2018, https://jmlr.org/papers/v18/16-558.html.
  The verified primary abstract explicitly covers adaptive resource allocation and
  early stopping. No new allocator novelty follows merely from staging budgets.
* Engineering Optimization50th-anniversary editorial,
  doi10.1080/0305215X.2025.2450132, emphasizes formal optimization advances and
  practical applicability. Directional scope fit does not certify sufficient novelty.

The table states implemented distinctions for review, not the conclusion of a
complete literature review. Authors should identify the closest matched-state
intervention/diagnostic comparator and assess each claimed technical increment.

## Author decision gates

1. Identify an executable diagnostic question this method answers that the chosen
   existing workflow cannot answer with the same information/cost boundary.
2. Verify the boundary between response reuse and full-trajectory reuse.
3. Keep the original named denominators plus de-duplicated action denominators;
   use complete seed blocks for replication statements.
4. Assess whether a diagnostic-method contribution with adverse allocator/selector
   results meets the target journal's innovation standard. Do not promote the tested
   allocator or change thresholds to make results positive.
5. Confirm the eventual article argument, disclosures and all author approvals.
   No author decision is presumed by this record.
