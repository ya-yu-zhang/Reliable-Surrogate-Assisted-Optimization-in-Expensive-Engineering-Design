# Independent budget-audit release

Read EVIDENCE.md, analysis.json, seed_block_results.csv and cost_accounting.json.
Keep unfavorable primary results and sensitivity comparisons. AUTHOR_REVIEW.md
lists integration boundaries; this is a technical evidence package, not a newly
drafted manuscript section. The later factual integration adds these measured records to the main and
supplement; the release-validation JSON below remains a historical record of
the earlier budget-only publication. Scientific author review remains pending.

## Restore and verify without new simulations

From a clean checkout, in Python3.12 with requirements-budget-audit.txt installed:

```bash
python -m src.compact_budget_audit_records --target .
python -m src.analyze_budget_audit
python -m unittest discover -s tests -v
```

The archive contains82 raw files and one derived primary trace file; all exact
bytes have SHA256 checks. Seven analysis outputs reconstruct identically from
the raw records. Restoration and analysis do not call the physical solver.
The large primary_traces.json is reconstructed/restored rather than stored as a
second uncompressed Git blob. No historical raw-data release is needed for this
independent experiment.

## Code interface and budget interpretation

src.budgeted_decision_audit.audit takes exact same-state action classes, a baseline
class, initial compliance, root predictive standard deviations, and a sequential
observe(branch, step) callback returning Observation(incumbent, exact_point_key).
The callback exposes the next prefix response only. Completed target trajectories
classify better/tie/worse; incomplete comparisons abstain. Utilities do not group
actions. Live callbacks must enforce the same history/kernel/continuation/context
and separately journal paid responses, failures and cache reuse.

The tested modes are adaptive, fixed_depth, fixed_breadth, immediate and full.
The post-validation configuration recommends fixed_depth within this tested
discrete-problem audit; it does not promote adaptive as a new superior optimizer.
The frozen primary response-request budget conservatively charges cache lookups.
Distinct points, training-cache reuse and actual physical attempts are separate
columns/counters. Research oracle collection is fully charged and cannot be
presented as net deployment savings.

## Physical collection guard

The frozen runner only runs with a supplied published protocol commit. It refuses
to overwrite scientific blocks. Existing complete blocks are hash-checked before
resumption; an incomplete block stops and requires a separately accounted recovery
plan. The supplied ten-block release is already complete: do not rerun it merely
to reproduce the tables. New experiments need a new version, seed namespace,
configuration and prospectively published protocol.
