# Frozen paired-grid numerical verification v1

Prospectively freeze exact cases, points, mappings and interpretation before new
mesh labels. These are selected secondary numerical checks, not new independent
optimization cases, an allocator-tuning set, or a mesh-convergence theorem.

## Selection

Retain all7 distinct h0/h5-changed contrasts in the archived common continuation.
Retain the independent budget release's1 distinct immediate-proxy mismatch under
EI continuation at the frozen primary margin/budget. Add the first4 unchanged
different-action h5 ties from the distinct-action CSV, sorted by state/control,
and2 baseline-action aliases in different states, sorted by state/control. No
favorable-sign selection or replacement case. Expected14 contrasts. Cases may
share states, endpoints and design points; report each level separately.

Each case freezes the original100x50 initial-incumbent design, both branches'
six retained actions, and each originally selected h0/h5 incumbent-design point.
All identities, old physical responses and source-file hashes are recorded before
the new numerical evaluation. Original full training histories are not refined.

## Objective / mappings

Meshes100x50,150x75,200x100 retain the2:1 aspect ratio, unit downward nodal force
at normalized top-left position(0,0), horizontal constraint along the entire left
boundary and vertical constraint at normalized bottom-right(1,1). Preserve default
material Emin1e-9,Emax1,SIMP exponent3,overhang off,volume0.35. Scale rmin2/3/4;
the simulation's stiffness evaluation does not apply an additional density filter.
Normalized geometry is dimensionless, not a claim of metre-scale geometry.

Two explicit mapping contexts:

* Native: unchanged19-variable4x5 anchored-logit wrapper, cubic zoom to each mesh,
  then discrete-mean volume normalization. Sampling positions and fitted volume
  shift can differ with resolution; this changes the represented density field.
* Conservative: form the original100x50 density field once, treat its cells as
  piecewise constant, transfer exact overlapping cell averages to the new mesh.
  This preserves integrated material fraction. It is a field-transfer sensitivity
  context, not a rerun of the optimizer with the historical parameterization.

At100x50 both mappings use the exact same original field. Cached response sharing
requires identical mesh/material/load/support and exact density bytes. Matching
19 parameters across different meshes/mappings alone never permits response reuse.

## Targets and checks

Primary: evaluate the originally selected h0/h5 endpoint designs at each mesh and
mapping; report (mean-design compliance - alternative-design compliance) divided
by the frozen initial-design compliance at that context. Use each source's original
relative margin (1e-6 or0.001). Report raw compliance, class stability, raw sign
and margin-boundary changes. This is a fixed-design contrast, not a reconstructed
fine-grid first-action optimization effect.

Secondary: select the best among each branch's six retained candidates and the
original initial-incumbent design after reevaluation at each context. Report this
limited retained-pool contrast separately. It omits99 other training points and
does not refit GPs or generate new actions, so it is not fine-grid optimization.

Validate all100x50 native responses against old paid responses (relative1e-8),
volume error<=1e-12, normalized force/support coordinates, material/configuration,
equilibrium residual norm||Kff*u-f||/||f||, and element compliance versus f^T*u.
The residual1e-6 threshold is a numerical flag, not a physical error bound. Retain
flags and all adverse classifications; do not tune effect margins afterwards.

Three resolutions do not prove convergence, especially without an asymptotic
range/regularity assessment. Distinguish solver repeatability, field-transfer
dependence, absolute objective variation and paired ranking stability. Do not
identify24.63% as a known solver error or treat it as an engineering tolerance.

## Paid attempts and reproducibility

Maximum1000 new attempts, all revalidation and failures charged. Every PRE/LABEL
pair is flushed/fsynced. Stop on failure/cap; no automatic rerun or replacement.
No old source labels seed the new physics cache:100x50 is actually rechecked.
Exact within-release duplicates may reuse a paid response. Record source-code,
configuration, selected-plan and installed-engine hashes. Publish the protocol
before executing. Analysis/restoration makes zero physical calls.

This numerical release supports independent author review and factual table
integration. It does not establish method novelty, physical convergence, optimizer
superiority, broad engineering applicability, or journal acceptance.
