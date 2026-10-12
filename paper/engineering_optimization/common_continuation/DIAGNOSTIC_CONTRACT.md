# Diagnostic contract and scope for author review

The diagnostic outputs have different targets. A classification change between
h0 and h5 is not inherently an error: first specify the engineering horizon.
If h5 is the deployment target, h0 alone is an unvalidated proxy for it. These
results are not a blind prospective accuracy test against published diagnostics.

| Evidence input | Identifiable in this experiment | Requires additional evidence |
|---|---|---|
| Frozen-GP RMSE/coverage on source-selected points | Prediction diagnostics of that GP | Which policy action differs and its utility |
| Exact chosen point plus objective context | Immediate response equivalence | Utility-tied points need not be the same action |
| Common-state real response | Immediate paid-action effect | Later benefit under continuation |
| First action plus declared common continuation | Conditional finite-horizon effect | Whole-policy, universal causal or deployment superiority |
| Original whole-policy endpoint/ablation | Overall coupled trajectory outcome | Conditional first-action effect under a fixed continuation |

Decision-equivalence shares responses only for exact context-point equality.
Whole-branch equivalence additionally requires the identical initial training
state, fitted kernel, information boundary, deterministic continuation and seed
stream. Grouping identical initial points within one frozen state satisfies this
contract. Across different states this experiment shares responses, not entire
trajectories. Utility ties alone never authorize either grouping.

The ordinary diagnostic benchmarking paper already analyzes effectiveness,
efficiency, reliability, controllability and runtime dynamics. Its strengths must
be acknowledged. The new evidence object evaluated here is a learned-state
first-action intervention, exact response equivalence and conditional continuation
record; authors must assess whether this specific difference constitutes enough
technical contribution for Engineering Optimization. No absence-of-prior-art,
blind diagnosis accuracy or universal strategy-selection superiority is certified.

## Additional output contract and denominator accounting

The original90 named contrasts remain the original result. Supplementary exact
action accounting identifies34 baseline aliases,56 different-action named
contrasts and46 distinct nonbaseline actions within states. The8 named
classification changes become7 distinct-action changes;7 delayed non-ties become6.
All changes occur in4 states within4 seed blocks. These are alternative reporting
denominators, not additional independent discoveries. See denominator_analysis.json
and distinct_action_contrasts.csv; equivalence uses the frozen action index/point,
never the observed utility or its sign.

Operational outputs distinguish exact structural equivalence, measured target
horizon, proxy prediction, and insufficient evidence. Budget-limited partial
trajectories abstain. A rule's false promotion/rejection is defined only after a
common target horizon, margin and deployment interpretation are fixed. A horizon
classification change alone is not a diagnostic error. The independent budget
audit protocol and all unfavorable comparisons are published separately.
