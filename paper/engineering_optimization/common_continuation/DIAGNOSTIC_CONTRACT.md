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
