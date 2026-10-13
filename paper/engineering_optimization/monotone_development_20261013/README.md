# Monotone-bound development replay, 2026-10-13

This release executes the P0/P1 feasibility and development step following the
review of commit `c2ce41a0e956621c81f2e3078f31da27edc990dd`. It is separate from
the frozen v1 audit and is not an independent experiment or manuscript draft.

- `METHOD_SPEC.md`: operator, assumptions, certificates, targets and failure conditions.
- `DEVELOPMENT_REPORT.md`: measured results and no-go decision in Chinese.
- `NEXT_OPERATION_REQUIREMENTS.md`: concrete assumptions and gates for a future operation.
- `analysis.json`, `summary.csv`: complete aggregate results and original-margin sensitivity.
- `state_results.csv`, `seed_group_results.csv`: all states/continuations and complete seed groups.
- `certificate_records.jsonl`: primary early category certificates and category-complete but selection-unresolved cases.
- `posthoc_order_envelope.csv`: all-order descriptive envelope; not a deployable comparator.
- `integrity_tests.txt`, `verification.json`: relevant tests and isolated byte-identical replay.

From the repository root, after restoring the existing records:

```sh
python -m src.compact_budget_audit_records --target .
python -m src.compact_common_continuation_records --target .
python -m src.analyze_monotone_development
python -m unittest tests.test_monotone_horizon_audit tests.test_monotone_development -v
```

Analysis and the fifteen new tests require only the Python standard library.
The analysis validates raw input hashes before prefix-only replay. It performs
no GP fit or physical evaluation. All four substantive controls are retained;
the constructed `mean_common_shift` alias is excluded from substantive contrasts.

The broader46-test integrity suite separately includes synthetic GP fixtures;
these are not new experiment fits or physical acquisitions. Generate the scoped
download package and verify isolated output bytes with
`python -m src.package_monotone_development`.

The development records comprise two already observed datasets: 30 archived
states with mean continuation, and30 previous-holdout states with mean/EI
continuations. These are60 stored states and90 state/continuation contexts,
not90 independent cases. Each dataset retains its ten complete seed groups,
GP settings and original primary margin. No pooled inferential result is added.

Costs distinguish audit response requests, selected-branch completion and
distinct statewise points absent training. The latter are not paid-solver counts
because real persistent-cache reuse spans states and runs. Alias-only states
need zero category requests; their six execution requests are included
consistently when the all-state selection-realization total is reported.

The candidate failed the development screen. No new independent labels are
collected and `submission_ready` remains false. Historical PDFs, protocols,
numeric tables and adverse findings remain unchanged.
