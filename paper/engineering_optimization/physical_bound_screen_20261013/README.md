# Physical-bound development screen

The protocol and source plan were pushed at
`fab39284d1c7e0fc4bbeb359ba5e7b384117bb14` before acquiring either reference
response. This is an extension of the development work at `c7fa9a2`, not a new
independent optimization experiment or manuscript draft.

- `REVIEW_AND_EXECUTION_PLAN.md`: reviewer-oriented current-state analysis and execution priorities.
- `PROTOCOL.md`: frozen operation, two-reference cost cap, pool inclusion and fail/go rule.
- `RESULT_AND_REVIEW_DECISION.md`: measured unfavorable result and submission judgment.
- `NEXT_RESEARCH_GATE.md`: concrete next information object and stopping criteria.
- `analysis.json`, `summary.csv`, `state_sharpness.csv`: all original groups and contexts.
- `verification.json`, `integrity_tests.txt`: numerical replay and55 relevant tests.

Raw readable records are in
`results/engineering_optimization_physical_bound_screen_v1/`: plan, two solved
trial-displacement vectors, element Gram data, candidate bounds, durable event
ledger and the original run status. The package records engine source hashes;
the local copied EngiBench package had no distribution metadata, recorded as
null rather than an invented version. Physical reference responses and residual
checks are fully retained.

Reanalyze already acquired data without simulations:

```sh
python -m src.physical_bound_screen --analyze
python -m unittest tests.test_reduced_compliance_bounds tests.test_physical_bound_screen -v
```

For an explicit numerical check from the stored trial vectors:

```sh
python -m src.verify_physical_bound_screen
```

That check uses the original engineering Python dependencies and does not solve
a physical system. It recomputes1720 bound designs, charged separately as
verification work. The `--run` acquisition command refuses an existing journal;
do not use it to reproduce reports or silently incur new physical attempts.

All60 stored states and both datasets' ten whole groups remain in the report.
Seventeen alias-only states skip bound work;43 nontrivial states use1720 design
queries. Mean/EI contexts are dependent and share this same physical information.
The sampled minimum is an upper cap on the specified full-pool lower envelope,
never a valid terminal lower bound or an early classifier.

The screen did not pass. No independent optimizer study was started. Scientific
claims, original physics records and v1/statistical families remain unchanged.
The existing manuscript/supplement availability paragraphs now identify the
private repository; the main GP cross-reference includes6.5. Both PDFs were
recompiled and checked. After earlier source regeneration, use
`python -m src.correct_repository_availability --verified-visibility private --include-acquired-physical-bound-cost`
only after verifying current visibility. `submission_ready=false`.
