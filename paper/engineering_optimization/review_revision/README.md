# Post-review factual revision and zero-solver sensitivity

This release addresses the simulated review at cfc2b94. It preserves all frozen
v1 physical records, code and primary comparisons. It adds descriptive replay,
an implementation contract and measured manuscript tables. It does not certify
novelty, general efficacy, adaptive advantage or submission readiness.

## Reproduce the new analysis

From a checkout with the original independent budget archive restored:

```bash
python -m src.compact_budget_audit_records --target .
python -m src.analyze_review_revision
python -m src.integrate_review_revision
```

The new replay uses Python's standard library and the frozen audit module. It
verifies the frozen file hashes and all ten complete blocks; it does not refit
GPs or call a physical solver. Seven analysis outputs are generated. The original
source-action/GP verification remains in the preceding release. The new analysis
reproduces all 36 fixed-depth/adaptive budget/margin cells before adding reversed
orders. Candidate enumeration uses every alternative-class permutation and keeps
the original control tie-break for state selection.

The new classification composition and ordering results are retrospective. The
always-tie calculation is explicitly a post hoc sanity check, not a registered
baseline. Positive synthetic unit-test fixtures validate implementation behavior,
not independently observed engineering gains.

## Files

* analysis.json: existing-label provenance, class topology, primary truth counts,
  original/reversed budget cells and interpretation boundaries.
* truth_composition.csv and seed_block_results.csv: all ten complete seed groups,
  retaining their three dependent source states and zero-contrast blocks.
* completion_capacity.csv and order_sensitivity.csv: request capacity, unfinished
  prefix cost, exhaustive alternative orders and missed-target ranges.
* budget_comparison.csv: all existing budget/margin cells and reversed order,
  keeping requests, statewise new points and selection loss separate.
* paired_grid_ranges.csv: all14 selected checks, with eight different endpoints
  separated from six identical-endpoint ties.
* IMPLEMENTATION_CONTRACT.md and TECHNICAL_INCREMENT_CHECKLIST.md: verified
  implementation objects and remaining author novelty decisions.
* factual_edit_audit.json and table_inputs.json: exact changes to existing text
  and hashes behind the generated tables.

New .tex inputs are data/implementation tables in integrated_evidence/. Existing
method, cost, result and conclusion paragraphs received factual clarification;
there are no new scientific argument sections. Author review of the final
scientific argument and publisher-policy compliance remains necessary.

Existing numerical rows and original named comparison denominators are retained.
New grid checks, permutations or margin cells are not independent samples and do
not expand the original confirmatory statistical families. Public raw/PDF upload
blockers from the preceding release remain unresolved; no alternate indirect
upload is attempted. Sources and small text/CSV outputs can be published normally.
