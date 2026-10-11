# Prospective engineering transfer and paid-workflow experiment

This protocol, configuration and implementation must be committed before
acquiring any new labels. It is separate from the original statistical
families and from the 120-state immediate diagnostic. No acceptance threshold
or optimizer coefficient will be tuned using its outcomes.

The physical changes are downward-force positions at 0.25 and 0.75 of the
100-element top edge, compared with the original top-left position 0.0.
Each condition uses ten fresh repeats, common Sobol initializations of 58
points, the original 19-variable volume-preserving parameterization, volume
fraction 0.35, the original material and supports, and EngiBench Beams2D v1.
A fresh problem object is configured per condition; a cached FE state must
never be reused across different force positions.

All four acquisition policies use the same isotropic Matérn-5/2 GP, normalized
targets, alpha=1e-6, constant bounds [0.05,20], length-scale bounds
[0.005,2], one deterministic L-BFGS-B fit with at most 100 iterations, and
no restarts. This bounded model and a 1,024-point Sobol pool deliberately
define a new controlled transfer experiment; they are not a replay of the
original ARD GP and continuous-refinement optimizer. Mean, EI, PI and LCB
use xi=0.01 times the training standard deviation and kappa=2. Exact
score ties use the lowest candidate index; selection ties use PI, mean, EI,
LCB. Candidate points already in the active training archive are excluded.
Convergence warnings are logged, not used to trigger additional fits.

For each condition/repeat, actually execute both workflows:

1. Audited selection: pay for 58 initial labels; fork four independent
   20-step pilots (80 paid labels); select the lowest pilot-end compliance;
   write the selection before validation; discard pilot labels from training;
   run only that selected policy from the 58-point archive to budget 200
   (142 more paid labels). Total 280 physical calls.
2. Full portfolio: pay separately for the same 58 initial points; fork all
   four policies to budget 200 (568 additional calls). Total 626 calls.

The full portfolio is an explicitly defined alternative selection workflow,
not a generic unaudited single optimizer. Audited selection costs 80 more
calls than a fixed single policy (200). Any portfolio cost reduction must
be accompanied by the observed endpoint loss relative to its best member,
and by comparisons to each fixed policy. No universal savings claim follows
from these prescribed counts. Pilot policies develop different histories;
their 20-step outcomes assess delayed policy value, not a fixed-continuation
counterfactual effect of the first action alone. The 200-step validation uses
a distinct candidate-seed namespace and no pilot labels.

Both workflows use identical canonical candidate seeds, so the selected
canonical trajectory can be checked against its independently paid portfolio
counterpart. Initial seeds are fresh and independent of the old development
histories. No physical-call cache is used, even for repeated designs between
workflows. Initial labels are shared only among forks inside each workflow.
Every attempt writes PRE before evaluation, increments a paid counter before
the call, and writes LABEL or FAILURE. A failure stops that case and makes the
experiment incomplete; no automatic scientific reruns are allowed. At most
906 calls per case and 18,120 across all twenty cases are authorized by this
configuration. Earlier 240 revision attempts remain separately accounted.

Report condition-specific repeat-first endpoints, relative improvement from
the initial incumbent, first-step and twenty-step pilot outcomes, selected
policy frequencies, paired losses, full learning curves, all paid calls,
FE seconds, GP fit/selection seconds, and observed wall seconds. Concurrent
timings are implementation observations, not exclusive resource measurements
or evidence of production wall-time savings. Do not add new p-values to the
old inferential families. Report negative and inconclusive findings fully.

Run in the pinned GP/EngiBench environment:

```sh
python -m src.engineering_optimization_transfer
python -m src.analyze_engineering_optimization_transfer
```
