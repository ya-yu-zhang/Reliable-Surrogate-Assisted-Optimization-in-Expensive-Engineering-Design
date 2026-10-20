# Beam finite-element endpoints and paired contrasts

Machine-readable record for the structural-optimization results in the main text
(Section 6.2 and 6.4 of the submission manuscript). Everything here is copied or
recomputed from the retained application archives; no new solver call is involved.

## Files

| File | Content |
|---|---|
| `endpoints_shared_initialization.csv` | The eight methods of the endpoint table: median, Q1, Q3 compliance, median improvement over each run's initial incumbent, `n = 10` repeats |
| `endpoints_native_initialization.csv` | GP-EI and TuRBO-1 under their native 38-point initialization (the prespecified sensitivity contrast) |
| `paired_repeats_internal.csv` | Per-repeat compliance for greedy, fixed 01 and PEM-T (50 rows) |
| `paired_repeats_shared.csv` | Per-repeat compliance for the five shared-initialization external methods, each paired with the PEM-T run of the same repeat (50 rows) |
| `paired_summary.csv` | The seven paired contrasts quoted in the main text |
| `source_hashes.json` | SHA-256 of every source file in the retained archive |

## Conventions

- Compliance is lower-is-better.
- A contrast is written `A minus B` on compliance, so a **positive** value means A
  is worse and a negative value means A is better.
- `median_difference` is the median of the ten repeat-matched differences, not the
  difference of the two medians in the endpoint table.
- `first_better`, `ties` and `first_worse` count repeats for the first-named method.

## Initialization

Greedy, fixed 01 and PEM-T share one 58-point initialization by design. GP-EI and
TuRBO-1 were first run from their native 38-point initialization and then re-run from
exactly the same 58 points as the internal methods; GP-PI, GP-UCB and DRSO were run
from that same archive. The endpoint table reports the shared-initialization runs for
all eight methods, and the native-initialization rows are kept separately so the two
batches are never mixed.

## Provenance

Sources: `engineering_beam_formal_v1`, `engineering_beam_shared_init_v1`,
`engineering_beam_acquisition_refs_v1` and `engineering_beam_drso_shared_init_v1`
in the retained results archive. Per-file hashes are in `source_hashes.json`.
Restoring the archive and re-running the summary scripts reproduces these files
byte for byte; no finite-element response is re-solved.
