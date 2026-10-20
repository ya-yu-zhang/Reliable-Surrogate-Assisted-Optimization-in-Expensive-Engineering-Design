# Contribution positioning: diagnostic methodology

Decision dated 2026-10-19. Supersedes the optimizer-adjacent framing of the earlier
revisions. This record states what the paper claims, what it no longer claims, and why
the alternative route — a new frozen seed-block experiment — is not taken now.

## Decision

The paper is positioned as a **decision-audit methodology with recorded verdicts and a
complete paid-call ledger**. It does not claim a new optimizer, a reliability method for
structural design, an efficiency gain over published optimizers, or selector superiority.
Title after this decision: *Decision-consequence auditing for surrogate-assisted
optimization in expensive engineering design* (before: *A Decision-Consequence Auditing
Framework for Reliable Surrogate-Assisted Optimization in Expensive Engineering Design*).

## Why not run a new seed-block experiment

The project's own gate forbids starting one at this point. `../physical_bound_screen_20261013/NEXT_RESEARCH_GATE.md`
states that independent experiments remain conditional on an implemented, validated
information increment, and that if no increment passes, the narrow diagnostic positioning
and its innovation risk are to be retained.

1. **The precondition does not exist.** `../gp_reachability_20261013/PROTOCOL.md` describes
   the candidate increment (GP action reachability) as a proposed next operation, not an
   implemented or validated certificate, and notes that the affine argument does not
   transfer to EI/PI, refitted hyperparameters or longer horizons.
2. **Two attempts to build that precondition failed.** The two-reference physical envelope
   failed root-tie sharpness on 43 of 43 nontrivial states across 1,720 candidate bounds;
   the monotone certificate candidate failed the full-cost and coverage screen.
3. **The expected outcome is already recorded.** The independent budget audit ran ten fresh
   seed blocks and obtained 0 better / 24 tie / 1 worse (mean continuation) and
   0 better / 23 tie / 2 worse (EI). A pre-registered test whose prior evidence is a tie
   cannot supply a novelty increment; it can only confirm the null.
4. **Order matters to reviewers.** Running seeds first and looking for an increment
   afterwards is the pattern R1 rejected: no amount of additional evidence substitutes for
   a stated technical increment.
5. **Cost asymmetry.** A new study needs reference solves, a full-pool bound library and an
   H5 reachable-history construction, with an outcome the prior record predicts. The
   repositioning needs no new solver call.

## What changes

- Title and abstract: the "reliable optimization" promise is dropped; the object audited is
  named instead.
- Contribution list: four methodological elements, each with its own evidence and cost.
- Section 2.3: an explicit statement that the output is a verdict with stated evidence and
  cost, and that the only performance claims are measured ones.
- Conclusion: the procedure and its records are the contribution.
- Cover letter and highlights follow the same wording.

## What does not change

Every measured number, every adverse result, the failing promotion gate of the temporal
controller, the one promotion / one stop / one held verdict in Section 6.4, the cost
ledger, the released records and their hashes.

## Claims that survive, with their evidence

| Claim | Evidence | Boundary |
|---|---|---|
| The audit separates four evidence levels and returns an explicit unsupported-claim boundary | Algorithm 1, Sections 3.3-3.5, Tables 4 and 6 | A procedure, not a convergence or regret result |
| Exact immediate-utility reporting costs 138 paid solves instead of 480 | Section 6.3 ledger, `gp_audit/summary.json`; minimality from the stored-response oracle | Exact oracle only; certified bounds can reduce it |
| The procedure discriminates: one promotion, one stop, one held for revision | Section 6.4; `data/engineering_optimization_gp_verdicts_v1/` | Retrospective on frozen records, declared thresholds, one design family |
| A calibration statistic close to target does not imply optimization value | Sections 5.2-5.3; `data/engineering_optimization_bbob_validation_v1/` | One controller, BBOB plus one beam family |
| Cheaper selection can lose final performance at a stated cost difference | Section 6.5; `data/engineering_optimization_beam_endpoints_v1/` | Two force positions, one beam family |
| Complete paid-call accounting, including recovery and verification | `COST_LEDGER_DEFINITIONS.md` | Attempts, not deployment cost |

## Residual risk and the trigger to revisit the other route

Novelty sufficiency remains an editorial judgment; narrowing the claims does not guarantee
it. The other route becomes available again only when both conditions hold: (a) the
reachability operation is implemented and validated against the same-state full-pool
reader on whole observed seed groups, including every actual next action, and (b) an H5
reachable-history construction exists. Until then, a new seed block would repeat an
experiment the record already answers.
