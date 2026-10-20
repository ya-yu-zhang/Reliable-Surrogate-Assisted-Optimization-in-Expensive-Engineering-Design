# Paid physics-attempt ledger: authoritative definitions

Every document that quotes a cumulative solver count must name which of the three
definitions below it uses. The numbers are attempts, not independent solves: failed,
recovered and verification attempts are all charged.

## 1. Reported optimizer and audit attempts: 55,305

| Component | Attempts | Source |
|---|---:|---|
| Frozen GP intervention (138 new labels) | 138 | `gp_audit/summary.json` |
| Solver-compatibility verification (42 unretained + 60 retained) | 102 | `gp_audit/solver_replay.json` |
| Retained transfer execution | 18,120 | `transfer_validation/summary.json` |
| Unchanged-protocol transfer recovery | 18,120 | `transfer_recovery_plan.json` |
| Common continuation (273 first execution + 9 ledger recovery) | 282 | `common_continuation/analysis.json` |
| Independent budget audit | 2,134 | `budget_audit/cost_accounting.json` |
| Small thermal verification (7,200 + 22 + 1,080 + 7,586) | 15,888 | `thermal_analysis.json` |
| Selected paired-grid check (4 + 517) | 521 | `paired_mesh/analysis.json` |
| **Total** | **55,305** | `integrated_evidence/table_inputs.json` |

## 2. Cumulative project attempts: 55,307

55,305 plus two auxiliary physical-bound reference solves used by the failed
root-tie-sharpness development screen
(`physical_bound_screen_20261013/RESULT_AND_REVIEW_DECISION.md`).

## 3. Budget-audit-stage snapshot: 54,784

Recorded in `budget_audit/EVIDENCE.md`. It is 55,305 minus the later 521 paired-grid
attempts and supersedes nothing; it is an intermediate point in the same ledger.

## Rules

1. A cumulative number is not a deployment cost. It includes recovery, verification
   and development screens that no single audit run would pay.
2. Do not mix the three definitions in one sentence. The submitted manuscript quotes
   only the stage it reports (36,480 for the GP and transfer stages); it makes no
   project-total claim.
3. `integrated_evidence/release_validation.json` records 55,305 because it was written
   before the two reference solves; its note field says so.
