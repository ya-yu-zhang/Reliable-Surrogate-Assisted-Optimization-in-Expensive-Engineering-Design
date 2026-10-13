# Fixed-discrete physical-bound feasibility screen

This is a development protocol and technical record, not a new manuscript
section or an independent validation protocol. It is to be published before
the two reference-displacement solves. Source states/trajectories were already
observed and remain development materials. All unfavorable outcomes are retained.

## Research object and closest simple operations

The proposed information is a lower bound on future compliance, beyond the
zero bound used in the previous monotone audit. For the fixed discrete SPD
stiffness K(rho), any Dirichlet-admissible trial displacement v satisfies

\[
\ell_v(\rho) = \frac{(f^T v)^2}{v^T K(\rho)v}
\le f^T K(\rho)^{-1} f.
\]

This follows by maximizing the quadratic energy over scalar multiples of v.
It is classical variational reasoning, not a claimed new theorem. Two stored
trial vectors also define a two-dimensional span. A small projected solve
chooses coefficients; their resulting trial vector is assessed by the same
conservative Rayleigh ratio. A failed or ill-conditioned reduced solve falls
back to the better scalar trial.

Compare (1) all-solid-reference trial, (2) known-training-incumbent trial,
(3) their simple maximum and (4) the two-dimensional span. All receive the
same source geometry/material and their full construction cost. Any future
audit comparator must also receive the same physical bounds; integration with
the audit does not, by itself, establish an optimization advance.

## Inputs fixed before new reference responses

Retain all30 archived source states and all30 previous-holdout source states,
with ten whole seed groups per dataset. The latter has two continuations; these
remain dependent contexts of the same source states. Single-action-class states
remain in the report but require no candidate-bound work.

Use the existing100x50 FE grid, load DOF1=-1, supports and SIMP exponent3,
Emin=1e-9, Emax=1. The existing density map has19 effective parameters and mean
volume0.35. The first reference is all solid; it is a mathematical trial source,
not a feasible volume-constrained design. The second is the initial incumbent
in the first previous-holdout state ordered by block and source. Its input is
chosen from the stored initial X/y archive only, before its first intervention.
No response after the frozen state chooses references or candidate inclusion.

The plan stores source hashes, engine hashes, package versions, reference input,
candidate seeds, full-pool hashes and sampled indices. Use the original seed
rules separately for each dataset; do not mix their GP settings or margins.

## Necessary sharpness screen, never a sample-based certificate

For each nontrivial state, future steps1--5 each have a predeclared1024-point
pool. Remove exact points in the initial training history and evaluate the
first8 remaining pool points. This superset includes future selected actions
without knowing their yet-to-be-observed training responses. It can be broader
than the actually reachable set and makes no claim that a witness is selected
by the continuation.

For a fixed operator, let E be the minimum point lower bound over this entire
superset, and S the minimum over sampled members. Necessarily E<=S. Thus S is
an **upper cap on the lower envelope**, not a terminal lower bound. A small S
disqualifies this full-pool-superset operator's root-level tie sharpness. A large
S does not certify anything: unexamined candidates may have a smaller bound.
No sampled minimum is passed to the monotone audit as a valid terminal bound.

Only after bound computation, inspect the old completed baseline endpoint C
and the original margin. A root-level tie would require a terminal lower bound
at least C-tau*m_init. Count witnessed failures against this necessary condition
for each method, state/continuation and exact nonbaseline class. A failure here
does not prove that all possible later-prefix bounds or smaller reachable sets
fail. Retain per-seed composition rather than adding independent case counts.

## Numerical and cost limits

Use finite float64 trial entries, symmetric stored element KE, and outward
material/energy arithmetic. Conservative local reduction guards use IEEE
round-to-nearest bounds, with positive tiny floors. Check scalar enclosures
against exact Fraction arithmetic on test instances, including negative cross
terms. This supplies a conditional arithmetic implementation; global stiffness
SPD, physical mesh convergence and error in the existing solver's reported
objective are not independently certified. It does not transfer infinite-PDE
certification from reduced-basis literature.

At most **two new physical reference attempts**, including failures. Do not
replace a failed reference or silently repeat it. Preserve raw solved vectors,
responses, residuals, work-energy checks, timing and any failed gate. Initial
source-repeat tolerance is1e-8; reference relative-residual flag is1e-5.
The two-dimensional condition limit is1e12, with a scalar fallback.

At most1800 candidate-design bound queries; at the fixed8-point rule, the
expected nontrivial-state workload is1720. Count the small2x2 system attempts
separately from physical full-system solves. Record density-map, Gram assembly,
candidate-bound, reference-solve and end-to-end run times. This is a necessary
screen, not proof of deployed end-to-end savings.

## Stop/go and manuscript treatment

Do not start independent optimization runs from this partial screen. If sampled
witnesses already invalidate needed tightness, stop this two-reference full-pool
operator before a full-envelope sweep. If they do not, a subsequent separately
specified complete-envelope computation, numerical validity check and matched
full-cost comparison is still required before independent validation.

No coefficient/margin/reference tuning is allowed to convert this screen to a
favorable result. Existing v1/monotone labels, protocols, physics journals,
statistical families and manuscript scientific claims remain unchanged. The
current illustrative margins still lack a certified engineering error basis.
Evidence from this screen must be reported as development, including failures.

The relevant prior certificate work includes
[Yano (2015), DOI10.1016/j.cma.2015.01.003](https://www.sciencedirect.com/science/article/abs/pii/S0045782515000043).
Its abstract describes exact PDE-energy bounds under stated assumptions; this
small trial-space screen is not a replication or an extension of that result.
