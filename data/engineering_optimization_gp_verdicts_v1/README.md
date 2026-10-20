# Recorded verdicts for the Gaussian-process acquisition rules

Machine-readable record for the promotion verdicts reported in Section 6.4 of the
submission manuscript. Everything is derived from two already frozen records; no
finite-element call, optimizer run or surrogate fit is involved.

## Files

| File | Content |
|---|---|
| `frozen_state_utility.csv` | Per source history and per control: action-change fraction, mean immediate utility, difference from the mean-selection control |
| `acquired_rule_verdicts.csv` | The three declaration criteria and the resulting verdict for EI, PI and LCB |
| `source_hashes.json` | SHA-256 of the two source records this directory is derived from |

## The declared rule

A control is **promoted** when (i) it changes the selected point by at least 20% of
states in at least two of the three source histories, (ii) its mean immediate utility
is not below the mean-selection control in any history, and (iii) its held-out endpoint
under the shared 58-point initialization is below the mean-selection endpoint at the
same budget. It is **stopped** when (ii) fails in every history, and **held for
revision** otherwise.

The thresholds are illustrative. The rule is applied to records that already existed
when it was written: it is a retrospective reading, not a pre-registered promotion test,
and it selected no policy for any comparison in the paper.

## Result

| Control | Utility ≥ mean in all histories | Endpoint below mean selection | Verdict |
|---|---|---|---|
| PI | yes | yes (1233.1 vs 1445.1) | promote |
| EI | no (negative in PI history) | no (2308.5) | hold for revision |
| LCB | no (negative in all three) | no (2308.7) | stop |

## Provenance

- Immediate utility and action-change fractions: `gp_audit/summary.json` (frozen
  120-state intervention, 138 paid diagnostic calls).
- Endpoints: `data/engineering_optimization_beam_endpoints_v1/endpoints_shared_initialization.csv`
  (mean-selection control = the greedy mean rule).
- The mapping from each control to its closed-loop counterpart is the same shared
  initialization and budget of 200 evaluations used throughout the application study.
