# Prospective GP decision audit

Protocol recorded: 2026-10-10. This is a new diagnostic analysis, not an
amendment to the historical prespecified BBOB/application comparisons.
No new engineering labels or formal results are reported by this revision.

## Question and evidence boundary

At the same archived GP model and candidate pool, do candidate-dependent EI,
PI, and fixed-multiplier LCB select different points from mean-greedy search,
and what immediate improvement do those choices achieve? This examines
decision influence and common-state utility across three acquisition rules.
It is not a comparison of complete optimizers, a calibration theorem, a
delayed-exploration test, or evidence that the audit saves net simulation cost.
Existing matched-initialization endpoints supply closed-loop context only.

LCB is the minimization form of the previously named GP-UCB control.
Parameters match the historical control definitions: PI margin = 0.01 times
observed-label standard deviation, LCB = mean - 2 standard deviations.

## Frozen design

`configs/engineering_optimization_gp_audit.json` prescribes three source
histories (GP-EI, GP-PI, GP-UCB), ten repeats each, and PRE checkpoints
59, 101, 151, and 200. All source optimizers have 58 shared initial labels and
a 200-observation optimizer budget. The four checkpoints produce 120 states.

The reader stops at PRE(t), reconstructs the GP using only labels before t,
restores the recorded Matérn-5/2 kernel parameters without hyperparameter
optimization, and verifies the source action's mean/standard deviation.
Exact source numpy/scipy/scikit-learn versions are required. Failure to
reproduce a source prediction prevents acquisition of any new labels.

Every rule receives the same 4,096-point Sobol pool after duplicate removal,
plus the recorded source action. Candidate rows are deduplicated and sorted
lexicographically; the first index breaks score ties. The audit deliberately
does not repeat acquisition-specific continuous optimization. Its common pool
therefore differs from the source optimizer's complete search pool. No exact
reproduction of the source action's ranking is claimed.

## Information order and calls

1. Check all 60 source files (30 journals and 30 summaries) and the call limit.
2. Freeze and hash all states, candidate predictions, and choices before
   diagnostic labeling. Training labels before t are permitted information.
3. Persist a diagnostic PRE record before accessing any chosen outcome.
4. Label only the union of the four rules' selected points. Reuse a recorded
   source-action outcome only after choices are frozen and only for the exact
   same point and deterministic beam objective. Reuse already-obtained
   diagnostic values by exact point identity.
5. Allow at most 480 new physical finite-element calls. Count failed attempts,
   reused source labels, reused diagnostic labels, and objective seconds
   separately. Never feed diagnostic labels into any optimizer history.

The maximum of 480 corresponds to four distinct choices at each of 120 states;
actual new calls can be lower through identical choices and reused outcomes.
Existing optimizer calls are sunk evidence costs, not newly saved calls.
Source reconstruction time is recorded separately. A failed or partial ledger
requires inspection; automatic reruns are disabled to avoid uncounted calls.

## Outputs and interpretation

Report action-change frequency relative to mean-greedy, normalized one-step
improvement, and paired utility differences within each state. Aggregate
checkpoints within a repeat first, and repeats within each source history
second. Do not treat checkpoints/candidates as independent engineering cases.
The initial release records state-level results without new p-values, post hoc
subgroup selection, or a framework promotion. Any inferential extension must
be separately frozen before inspecting these new outcomes.

A lower one-step gain is not a rejection of exploration. A delayed-value or
held-out closed-loop design is required for that question. Net-savings claims
require a separate audited-versus-unaudited workflow comparison with all
diagnostic and optimization costs included.

## Execution

Use the original frozen application GP environment and restore raw journals
to their original paths; endpoint tables cannot replace them.

```sh
python -m src.engineering_optimization_gp_audit --preflight
python -m src.engineering_optimization_gp_audit --freeze
python -m src.engineering_optimization_gp_audit --evaluate
python -m unittest discover -s tests -p 'test_engineering_optimization_gp_audit.py' -v
```

The checked-in protocol's preflight is currently blocked by absent raw files.
The synthetic test fixtures verify implementation integrity and have no
scientific evidential role. The revision remains a working manuscript.
