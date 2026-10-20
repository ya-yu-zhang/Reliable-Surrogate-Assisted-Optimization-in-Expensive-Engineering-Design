# Independent budget-audit measured evidence

Technical data record for author verification; not a manuscript argument draft.

Protocol frozen and published before new physics labels at460657e8c6507fcf41d67a1b8ce9463cfa7622bf. Ten complete independent seed blocks,30 dependent source states,23 different training histories,55 exact first-action classes. Seventeen states have different actions;13 states have only structural aliases. Each continuation has90 named comparisons and25 distinct nonbaseline-action comparisons.

Primary target: five additional shared-rule actions, relative margin0.001, response-request budget18. All classifications in the table exclude structural aliases.

| Continuation | Method | Classified /25 | Errors | False promotions | Abstained | Requests across30 states | Mean state selection regret (%) |
|---|---|---:|---:|---:|---:|---:|---:|
| mean | calibration | 6/25 | 6 | 5 | 19 | 240 | 0.000000 |
| mean | immediate | 25/25 | 0 | 0 | 0 | 42 | 0.000000 |
| mean | fixed_depth | 25/25 | 0 | 0 | 0 | 252 | 0.000000 |
| mean | fixed_breadth | 25/25 | 0 | 0 | 0 | 252 | 0.000000 |
| mean | adaptive | 25/25 | 0 | 0 | 0 | 252 | 0.000000 |
| mean | full | 25/25 | 0 | 0 | 0 | 252 | 0.000000 |
| ei | calibration | 6/25 | 6 | 5 | 19 | 240 | 0.298265 |
| ei | immediate | 25/25 | 1 | 0 | 0 | 42 | 0.000000 |
| ei | fixed_depth | 25/25 | 0 | 0 | 0 | 252 | 0.000000 |
| ei | fixed_breadth | 25/25 | 0 | 0 | 0 | 252 | 0.000000 |
| ei | adaptive | 25/25 | 0 | 0 | 0 | 252 | 0.000000 |
| ei | full | 25/25 | 0 | 0 | 0 | 252 | 0.000000 |

Budget12 sensitivity at the same margin: fixed-depth17/25 classified, adaptive9/25, fixed-breadth9/25. Each requests204 labels across30 states for either continuation. Completed-horizon methods have zero observed errors by direct target measurement; report coverage and cost alongside this fact. At budget18, every state has at mostthree exact action classes, so the budget already permits full completion. This dataset does not establish an adaptive-allocation advantage.

Immediate proxy errors: mean0/25; EI1/25. Pairwise and state-selection regret are zero for the immediate rule in these cases: its one classification error is not evidence of a wrong deployment choice. The calibration rule is a constructed root-EI proxy gate, not a published diagnostic benchmark; it classifies6/25 with6 errors, including5 false promotions. Its empirical calibration threshold does not certify future utility.

All30 states and10 seed blocks are retained. Seed-block_results.csv is the replication-level record. Budget/margin sensitivity is descriptive, not a tuning set or a new inferential family. Offline prefix replay is not independent live deployment.

## Numerical and cost record

New paid physics attempts: 2134; ordered response requests2912; exact cache reuses778. Breakdown: warm500, source1047, calibration240, oracle335, repeatability6, finer mesh6. No failed/recovery attempts or replacement seeds. Cumulative attempts through this stage are 54784; the project ledger total is 55305 before the two auxiliary physical-bound reference solves and 55307 after them. See `../COST_LEDGER_DEFINITIONS.md` for the three definitions. FE timings and continuation GP timings are retained; warm-kernel/source/calibration GP times were not separately recorded, so no complete original end-to-end runtime or speedup claim is made.

Six repeated solves have maximum relative difference 0. Maximum two-resolution difference is 24.6298%. This exceeds the illustrative0.1% decision margin. Reproducibility of the fixed discretization does not establish physical accuracy; two meshes do not prove mesh convergence.

Raw compliance, exact design points and full histories are retained in the lossless data archive. The margin is not an engineering-certified tolerance. No advantage, global zero-error guarantee, net deployment savings or acceptance claim is supported by this technical record.

## Reproduction

```bash
python -m src.compact_budget_audit_records --target /path/to/clean-checkout
python -m src.analyze_budget_audit
```

Use the exact numpy/scipy/scikit-learn/EngiBench/cvxopt versions in the frozen manifest. The analyzer rebuilds all source and diagnostic decisions using only their own recorded past labels. Physical collection is a separate opt-in command and will not overwrite or automatically replay an incomplete experiment.
