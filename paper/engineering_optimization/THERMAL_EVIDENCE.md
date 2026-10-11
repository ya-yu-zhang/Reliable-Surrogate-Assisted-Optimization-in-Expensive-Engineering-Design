# Thermal equal-budget verification: measured evidence

Author-review data record; not a drafted manuscript section or a novelty certification.

Twenty independent initializations, five workflows, 96 paid deployment calls per workflow. Negative paired differences favor the gate. No threshold tuning or confirmatory p-values.

| Source | Comparator | Median paired difference (%) | Wins/ties/losses |
|---|---|---:|---|
| central_source | simple_selector | 0.000000 | 0/9/1 |
| central_source | fixed_mean | 3.961367 | 1/3/6 |
| central_source | fixed_ei | 4.961246 | 2/2/6 |
| central_source | fixed_lcb | 4.961246 | 2/2/6 |
| offset_source | simple_selector | 0.000000 | 0/10/0 |
| offset_source | fixed_mean | 0.201739 | 4/1/5 |
| offset_source | fixed_ei | 2.349897 | 2/2/6 |
| offset_source | fixed_lcb | 2.349897 | 1/3/6 |

Gate/simple choices differ in 2/20 cases. Their endpoints in these cases are one tie and one gate loss. The 18 same-policy continuation histories match exactly.

The replay matches the visible prior aggregate results. It does not certify recovery of every old per-case endpoint or timing byte. Cumulative thermal cost is 15,888 attempts: 7,586 from the lost previous session, plus this replay of 7,200 optimization, 22 numerical verification and 1,080 record-recovery solves. Replay adds no independent case.

## Verified boundaries

- Authored small dimensionless thermal model, not a published industrial benchmark or a demonstrably expensive simulator.
- Elastic structure and steady thermal conduction are two physical families. Each family has two conditions, not four independent domains.
- Fixed GP hyperparameters differ from the beam studies. All thermal workflows use identical settings.
- The illustrative temporal gate did not demonstrate superior selection or performance-preserving savings.
- The gate comparison does not isolate every stage of the original auditing framework.
- Final manuscript integration, novelty assessment, scientific interpretation and AI-policy review remain the authors responsibility.

See THERMAL_PROTOCOL.md and THERMAL_SESSION_RECOVERY.md. Raw records are released with hashes; restoration adds zero solver calls.
