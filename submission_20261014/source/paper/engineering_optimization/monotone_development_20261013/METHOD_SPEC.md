# Monotone horizon-category certificate: development specification

This is a technical research record, not manuscript or section draft text. The
new operation is separate from the frozen v1 experiment and is not claimed as a
new optimization theorem. Its status is development-only.

## Target and assumptions

Fix a learned state, first-action classes, continuation, external candidate-seed
rule, horizon H=5, and the original dataset-specific relative margin tau. Step 0
is the first intervention; reaching H requires six responses per branch.
Minimization incumbent m_j(s) is nonincreasing. Every reachable objective must
satisfy a known lower bound ell. The beam development replay uses ell=0 because
deterministic compliance is nonnegative. This assumption does not certify the
accuracy of the FE response or the engineering meaning of the margin.

Only an exactly identical state/action/continuation context is a structural
alias. Matching observed objective values never justify merging branches.

## Terminal bounds and category certificate

For an unfinished branch, set [L_j,U_j]=[ell,m_j(s)] (U_j is the initial
incumbent before any response). For a completed branch set both ends to m_j(H).
Let branch 0 be the baseline and m_init be the positive initial incumbent. Then

\[
\frac{L_0-U_j}{m_{init}} \le
d_j=\frac{m_0(H)-m_j(H)}{m_{init}}
\le \frac{U_0-L_j}{m_{init}}.
\]

The assertion follows by subtracting the terminal intervals and dividing by a
positive number. The implementation rounds partial interval arithmetic outward.
If both branches complete, it uses the recorded-float v1 classifier unchanged.

Return `better` if the lower end exceeds tau; `worse` if the upper end is below
-tau; `tie` only if the entire interval is inside [-tau,tau]. Otherwise abstain.
Each partial certificate carries its interval. Its terminal effect is `None`,
since a category certificate is not a measured effect size.

For example, a completed alternative with incumbent 100 and a baseline prefix
incumbent 70 certify that the alternative is worse at H, for initial=100 and
tau=0.001. The baseline can only improve further. This can require seven rather
than twelve pairwise requests, but the baseline still needs five continuation
responses to realize its H outcome.

## Selection certificate and separate target

Choose the smallest upper bound with a deterministic baseline-first tie-break.
Branch j is certified tau-optimal if

\[
U_j \le L_i+\tau m_{init}\quad\text{for every other branch }i.
\]

Its eventual endpoint cannot be worse than its own upper bound; competing
endpoints cannot beat their lower bounds. This is a guarantee conditional on
finishing the selected branch and the validity of the supplied bounds. It is
not an exact ranking or a measured outcome. Arithmetic in this check is also
conservative at a boundary.

Two explicit targets are replayed:

- `categories`: stop when all nonbaseline categories are certified.
- `categories_and_selection`: also require the selection certificate; otherwise
  continue reading within the same budget.

If selection remains unresolved, the report records abstention from selection
certification and scores a separately disclosed baseline fallback. It does not
call that fallback certified. The cost ledger adds every unread prefix response
needed to finish whichever branch is selected for outcome scoring.

## Executable comparators

All schedules receive the same classes, bounds, horizon, target and budget. They
can read only the next response on each branch.

| Schedule | Deterministic order |
|---|---|
| Frozen v1 fixed depth | Baseline to H, then alternatives; no partial category certificate |
| Certificate baseline depth | Baseline first, then alternatives; check bounds after every read |
| Certificate alternative depth | Original-order alternatives first, then baseline; same certificates |
| Certificate fixed breadth | Baseline-first branch order at each depth; same certificates |
| Development h0 largest upper | Read all step-0 responses, finish the largest observed incumbent branch, then baseline-first remaining order |

Already certified alternatives can be skipped for the category target. For the
joint target this skip also requires selection to be certified. The h0 order
uses only exposed responses and is a heuristic. All branch-order permutations
are separately enumerated as a response-informed descriptive envelope; that
envelope is not an executable or preregistered comparator.

## Failure conditions and scope

For this particular certificate with ell=0, a selected upper bound above
tau*m_init requires every competing branch to be complete: any unfinished
competitor has L_i=0 and violates the selection inequality. Finishing the
selected branch then brings the total to K*(H+1) branch-step requests. This
elementary contract explains why request savings disappear on certified
selection realization, regardless of branch order. It is not a bound on paid
physics, other certificates, nonzero lower bounds or general auditing methods.

With ell=0 and ordinary positive incumbents, two unfinished branches generally
have an effect interval crossing both signs. A step-0 tie cannot certify a later
tie. If baseline H is C and the alternative is incomplete, a tie certificate
requires U_j <= C+tau*m_init AND L_j >= C-tau*m_init. A zero lower bound cannot
meet the second requirement when C>tau*m_init. This elementary information
boundary explains the limited coverage gains; it is not a claim about the
unobserved physics or future GP acquisition predictions.

Several alternatives can all be better than baseline while their mutual ranking
remains unresolved. Stopping after their categories are known is insufficient
for certified selection. Joint-target replay retains this unfavorable outcome
instead of inserting a partial interval endpoint as a measured effect.

The bounds are elementary interval/pruning practice. The official
[SCIP FAQ](https://www.scipopt.org/doc/html/FAQ.php) documents primal/dual bounds
and gap-based reasoning; SCIP solves a different target and is not an algorithm
replication here. [Wu and Frazier (2019)](https://papers.neurips.cc/paper_files/paper/2019/hash/2e6d9c6052e99fcdfa61d9b9da273ca2-Abstract.html)
already formulate multistep evaluation value. Our certificate supplies a bound
on recorded conditional terminal categories; it does not replace their
lookahead acquisition algorithm or establish an advance over it. These sources
do not establish the novelty of this audit application.

## Execution and termination

Original margins are 1e-6 for archived common-mean continuation and 0.001 for
the previous independent budget validation. All complete original seed groups
are included; no future response is used to choose inclusion or schedule.
Those observed records are now development data for this new rule.

The development screen checks errors, coverage, selection loss and cost after
selected completion against certificate-aware simple schedules. Its 5% gain
threshold is an internal spending screen, not an editorial requirement or a
preregistration. Failure terminates this candidate's independent-validation
path; it does not imply that all possible auditing improvements are impossible.
