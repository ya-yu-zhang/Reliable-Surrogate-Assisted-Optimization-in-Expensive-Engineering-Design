# Requirements before the next independent experiment

Technical research planning record. The monotone-only h0 candidate did not pass
the development screen. Increasing the number of same-model seeds or adjusting
the order on the observed outcomes does not repair this missing increment.
Under the current zero-bound certificate, a selected upper bound above
tau*m_init forces every competitor to finish. Completing the selected branch
then restores the full K*(H+1) response-request cost. New seeds cannot remove
that contract; a useful next operation must supply additional valid information
or use a separately declared target.

## Next operation to investigate

A potentially useful operation must obtain a tighter VALID terminal lower bound
before expensive response labels, or change the target to a declared decision
loss with a meaningful reduction in its full cost. Terminal truth, GP standard
deviation and immediate ties are not such bounds.

One concrete feasibility path is a reachable-candidate lower envelope. At a
prefix, define a provable superset of all future candidate actions permitted by
the frozen continuation/seed rule. A cheap bound l(x) must satisfy l(x)<=f(x)
for every point in that set. Then

\[
L_j = \min\{m_j(s),\inf_{x\in R_j(s,H)} l(x)\}
\]

is a terminal lower bound. This is a proposed operation, not implemented or
validated in this release. Unknown training responses make future selected
actions unknown; using only the retrospectively selected path would be invalid.
The fixed external pools can supply a superset, but may be too broad to yield a
useful bound. A new GP-dependent policy needs its own reachable-set argument.

## Feasibility gates

| Gate | Required evidence | Stop condition |
|---|---|---|
| Validity | Derive the bound for the fixed discrete beam model and every reachable candidate; account for numerical error where needed | A heuristic or an empirically calibrated GP interval is substituted for a certificate |
| Sharpness | Test bound quality on complete observed development groups, including ties, without supplying terminal truth to the bound | Bounds remain below C-tau*m_init on the comparisons targeted for early ties |
| Full cost | Charge bound construction, GP work, response requests, paid physical attempts, cache reads, selected completion and failed retries separately | Matched simple certificate-aware methods obtain the same decisions at equal or lower total cost |
| Choice quality | Report certified/uncertified selection, coverage, false adoption/elimination, selection loss and all abstentions | Low error is obtained only by reduced decision coverage or costly completion that erases savings |
| Independence | Freeze rule, hypotheses, budget, target, continuation, margin and whole-seed inclusion before new labels | The proposed validation seeds, selection rule or positive cases have already been examined |

The retrospective sharpness diagnostic in `analysis.json` measures a necessary
condition, not a supplied online bound: for previous-holdout ties the median
required lower bound is 99.9% of the completed baseline endpoint. For the old
1e-6 margin it is 99.9999%. These thresholds belong to the fixed numerical
targets; physical accuracy and an engineering benefit margin remain uncertified.

## Independent-validation specification after a pass

Use a new master seed and disjoint complete seed groups. Inclusion may depend
on frozen state metadata and exact class count, never on future positivity.
The comparison must use the same target, bounds available at the same time,
continuation, budget and all cost categories. Retain strong certificate-aware
fixed orders and the unchanged v1 audit. A published diagnostic comparator can
be named as replicated only after implementing its actual rule and assumptions.

Run mean and EI common continuations under a budget that creates declared
pressure. Report categories and selection certificates separately, all seed
groups, positive/negative/tie composition, false adoption/elimination, abstention
and choice loss. Analyze dependent source states within complete seed groups.
If there are no positive cases, restrict the corresponding diagnostic claim.

For an engineering deployment claim, prospectively choose the benefit margin
and numerical checks. The existing selected-grid checks remain fixed-design
evidence and do not certify physical convergence. Record all GP/physics timing
instead of implying an end-to-end speedup from response-request counts.

## Manuscript consequence now

The current manuscript still has an unresolved novelty risk. This release does
not promote the monotone certificate into a positive optimizer/resource-benefit
claim. The earlier full-depth results, missing positive holdout cases and
numerical limitations remain intact. The candidate and failed screen are
available as development evidence. New manuscript claims require a demonstrated
increment and scientific interpretation; the current PDFs are not recompiled
merely to introduce this unsuccessful development candidate.
