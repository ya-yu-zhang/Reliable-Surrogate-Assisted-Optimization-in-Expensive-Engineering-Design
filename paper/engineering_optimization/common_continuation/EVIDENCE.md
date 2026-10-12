# Common-continuation measured evidence

Author-review data record, not a drafted manuscript argument or novelty certification.

Thirty frozen states nested within ten seed blocks and three source optimizers. First actions alone vary; all branches then use the same posterior-mean continuation and external candidate seed rule. Horizons count additional steps after the first action. Positive advantages favor the named control over mean.

| Source history | First action | h0 better/tie/worse | h5 better/tie/worse | Median h5 advantage (%) |
|---|---|---|---|---:|
| gp_ei_shared_init | ei | 0/10/0 | 1/9/0 | 0.000000 |
| gp_ei_shared_init | pi | 0/10/0 | 1/8/1 | 0.000000 |
| gp_ei_shared_init | lcb | 0/10/0 | 1/9/0 | 0.000000 |
| gp_pi_shared_init | ei | 0/10/0 | 0/10/0 | 0.000000 |
| gp_pi_shared_init | pi | 0/10/0 | 0/10/0 | 0.000000 |
| gp_pi_shared_init | lcb | 0/10/0 | 0/10/0 | 0.000000 |
| gp_ucb_shared_init | ei | 1/7/2 | 0/7/3 | 0.000000 |
| gp_ucb_shared_init | pi | 0/9/1 | 0/8/2 | 0.000000 |
| gp_ucb_shared_init | lcb | 0/8/2 | 1/6/3 | 0.000000 |

Across 90 dependent state/control contrasts, 8 classifications differ between h0 and h5; 7 immediate ties become non-ties. These are descriptive counts, not 90 independent trials.

| Relative tolerance | Changed classifications | Immediate tie to later non-tie |
|---:|---:|---:|
| 1e-06 | 8 | 7 |
| 1e-05 | 8 | 7 |
| 0.0001 | 8 | 7 |

## Evidence and cost boundary

- The frozen GP prediction error/coverage record is identical across first-action policies. This tests information sufficiency, not superiority over all published diagnostic frameworks.
- Neutral control exactly matches mean in all30 states; it is a constructed instrumentation invariant.
- Common-continuation contrasts isolate a conditional first-action effect under the declared continuation; original whole-policy endpoints measure another estimand.
- The audit reports measured outcomes from exhaustive branches; no blind prospective classification accuracy or universal causal inference is claimed.
- Raw compliance and initial-incumbent-relative percentages are supplied with the fixed1e-6 discrete-model tie threshold. They do not certify physical improvement beyond model discretization error.
- Existing first-label responses are reused76 times. The first execution made273 new FE attempts and107 continuation cache reuses. Ledger recovery adds9 FE attempts; total paid new attempts282. Replay adds no sample; old timing bytes were not recovered.
- Query sharing is exact deterministic duplicate-response avoidance. This does not demonstrate net deployment savings or performance-preserving strategy selection.
- Retrospective source-selected calibration points are biased; no valid coverage guarantee or promotion use is implied.
- Authors must independently assess contribution sufficiency and integrate scientific interpretation.
