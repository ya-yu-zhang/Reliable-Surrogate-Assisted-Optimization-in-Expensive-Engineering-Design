# Selected paired-grid numerical release

This is a fixed-design numerical sensitivity check, not a new optimization
experiment. Read EVIDENCE.md together with analysis.json and paired_contrasts.csv.
The frozen initial protocol was published at 72a519e1bbf7e02bee451076f075a96f307ab7f5;
the explicit failure/recovery amendment was published at
8a278d6ca50ac8746ed02198912f0f5028253e83 before recovery execution.

## Publication boundary

Local restoration and analysis are complete and verified. Public raw-archive
upload remains incomplete because automatic approval review rejected two exact
compressed segments (003/004) after full content/provenance checks. The complete
local review package contains all six parts and the manifest; no broken partial
raw archive is published. The analysis outputs, code and protocols are separately
reviewable. The commands below require that complete archive.

## Restore and reproduce without physics calls

From a clean checkout with requirements-budget-audit.txt installed:

```bash
python -m src.compact_paired_mesh_records --target .
python -m src.analyze_paired_mesh_records
```

The archive includes the exact selected source snapshots, immutable plans,
stopped-run journal/status and completed recovery journal/responses/status.
It restores 25 JSON/JSONL files with byte-hash verification. All three analysis
outputs reproduce identically. Analysis validates the frozen file hashes, every
mesh/density context, ordered request/label records, cache reuse and flag logic;
it does not rerun the physical solver. Existing protocol/source files must have
their exact frozen bytes. Restoration refuses conflicting records.

Do not rerun physics merely to reproduce these tables. The original execution
stopped at its fourth paid attempt; one original response value and duration were
not retained. The recovery remeasured that design, retained the failed flag and
unchanged tolerance, and charged the missing earlier attempt separately.

## Cost and interpretation

There are 624 response requests, 107 exact mesh/density cache uses, 517 new recovery
attempts and four earlier attempts: 521 paid attempts in total. The release
contains 520 unique successful responses. A remeasured value does not restore the
exact missing original value or duration. The three successful original values
were reused without an extra physical solve.

Fourteen contrasts originate from nine already observed states. Eight contrast
pairs have different final endpoint designs; six are identical-endpoint ties.
No independent optimization sample is added. No fine-grid GP optimization or
refinement of all original training labels was performed. All physical attempts,
including stopped/recovery attempts, remain in the full revision cost ledger.
