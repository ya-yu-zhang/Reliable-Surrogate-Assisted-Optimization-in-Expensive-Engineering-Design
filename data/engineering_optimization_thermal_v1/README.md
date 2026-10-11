# Thermal decision-usefulness verification release

Twenty independent cases, exact measured JSONL records and summaries, recovery
records and damaged-original forensic files. Ten gzip/base85 segments have hashes
in manifest.json. Regenerating deterministic Sobol candidate coordinates restores
original JSONL bytes; it does not generate measured objective labels. All 48 files
were restored and their hashes verified. Clean-directory reanalysis is byte-identical.

Install requirements-engineering-thermal.txt. From the repository root:

```bash
python -m src.compact_engineering_thermal_records --target /tmp/thermal-restored
```

Restore into a clean checkout with the default target, then analyze without new
physical solver calls:

```bash
python -m src.compact_engineering_thermal_records
OPENBLAS_NUM_THREADS=1 python -m src.analyze_engineering_optimization_thermal
```

Conflicting existing scientific bytes are rejected. Optional optimization reruns
must use an isolated checkout and incur their full cost; never delete scientific
records merely to permit rerunning. The frozen protocol and session-recovery plan
are in paper/engineering_optimization/. Published records are the retained replay;
they do not certify recovery of all earlier timing bytes or per-case labels.

Every workflow charges 96 deployment calls. Retained replay optimization: 7,200.
Current numerical verification: 22. Additional record recovery: 1,080. Lost previous
session: 7,586, still charged. Cumulative thermal attempts: 15,888. Replays do not
increase the twenty-case independent sample. Original structural revision costs
remain separate. Gate superiority and performance-preserving savings were not
shown. This is an authored small numerical conduction model, not EngiBench or an
industrially qualified expensive thermal simulator. See THERMAL_EVIDENCE.md.
