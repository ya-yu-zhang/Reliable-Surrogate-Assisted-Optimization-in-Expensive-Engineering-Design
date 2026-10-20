# BBOB independent-validation contrasts and scores

Machine-readable record for the mechanism results in the main text (Sections 5.2 and
5.3). Copied from the retained analysis archive; no optimizer run or surrogate fit is
repeated here.

## Files

| File | Content |
|---|---|
| `prespecified_comparisons.csv` | The nine contrasts of the single Holm family: estimate, bootstrap interval, raw p, direction counts, Holm p |
| `prespecified_function_contrasts.csv` | The 72 function-level contrasts behind the endpoint figure (24 functions x 3 dimensions) |
| `endpoint_scores.csv` | Suite-level log-relative endpoint scores by dimension and method |
| `function_scores.csv` | Per-function log-relative endpoint scores |
| `source_hashes.json` | SHA-256 of each source file in the retained archive |

## Reading the direction counts

`positive`, `negative` and `zero` count repeat-level outcomes out of 24
(function-instance cells) for every contrast. `zero` is the number of exact ties, so
the non-tied denominator is `24 - zero`: 24 for the endpoint and history-interaction
rows, and 19, 21 and 21 for the three immediate-improvement rows.

`estimate` is positive when the first-named quantity is larger. For the endpoint rows a
positive value therefore means PEM-T has the larger (worse) relative error, and for the
immediate-improvement rows a negative value means feedback declares less improvement
than mean-greedy selection.

## Provenance

Source: `mechanism_validation_analysis_v1` in the retained results archive, generated
from the frozen independent-validation runs with the archived configurations and seed
maps. Per-file hashes are in `source_hashes.json`.
