# Explicit paired-grid recovery / numerical-flag amendment

Original protocol72a519e1bbf7e02bee451076f075a96f307ab7f5 stopped on the fourth
100x50 solve: source-response agreement at relative1e-8 failed for point
0c6241e8b0aab8a83ffa0ec9bc7629bbb4bf0843dd5e9d5b2a0ec45b9f67f3f5,
whose archived compliance is60220706.07686931. The first3 responses and checks
are fully retained. The fourth physical response was computed but the original
assertion preceded LABEL persistence; its original value/timing cannot be restored.
Count all4 original attempts, with1 paid response requiring recovery. Never
fabricate its missing value or treat the replay as another independent sample.

This amendment retains all14 cases,104 points, six mesh/mapping contexts, effect
margins, source-agreement tolerance and physical setup. The sole interpretation
change is to RECORD source-agreement failures rather than abort the remaining
selected sensitivity measurements. A failed check remains failed; no tolerance
is softened and no original response is overwritten. All LABEL records now precede
flag processing. The resulting record is numerical-sensitivity evidence with
explicit flags, not a declaration that the original validation gate passed.

Reuse the3 completed original labels only after exact mesh/density/context and
hash checks. Remeasure the1 missing response and obtain all remaining labels.
Charge new attempts separately and add the original4 attempts to the cumulative
ledger. Maximum1000 attempts across BOTH executions. Stop on actual solver error,
nonfinite/negative compliance, invalid volume/geometry or the paid-attempt cap.
Keep the original runner/config/plan/journal immutable, apart from adding an
explicit stopped-status record. Publish the recovery runner, plan and amendment
before executing it. No new seed, case, optimization action or statistical family.

In analysis, report the magnitude and locations of coarse-response discrepancies,
equilibrium/energy checks, fixed-design and retained-pool classifications, and
all six contexts. Investigate repeated high-compliance sensitivity without
automatically attributing it to a known physical or solver error. Recovery checks
are not physical-convergence certification or extra independent validation cases.
