# Common first-action / continuation release

Exact bytes of96 files: frozen plans, measured journals, all30 summaries, manifests,
run status, recovery accounting and damaged-original forensic records. Eight
LZMA/base85 segments have hashes in manifest.json. All files restore exactly; clean
reanalysis reproduces all four output files byte-for-byte with zero physics calls.

Use the original GP audit environment: numpy2.2.6, scipy1.15.3, scikit-learn1.7.2;
engibench0.2.0 and cvxopt1.3.2 are needed for optional physical reruns. Restore the
record packet from the repository root:

```bash
python -m src.compact_common_continuation_records --target /tmp/common-restored
```

For analysis in an isolated checkout, restore with the default target and run:

```bash
python -m src.compact_common_continuation_records
OPENBLAS_NUM_THREADS=1 python -m src.analyze_common_continuation
```

No earlier source histories are needed for reanalysis: frozen plans retain the
required100-observation past histories and fitted kernels. Optional full physics
reruns additionally require restoring the original curated GP histories/diagnostic
ledger and use a fresh isolated checkout. Never remove retained records to permit
a rerun. Read COMMON_CONTINUATION_PROTOCOL.md and both recovery plans first.

The first execution cost273 new FE attempts; explicit cache-aware ledger recovery
adds9, for282 total. The retained run_status describes the replay execution's9;
recovery_accounting is the authoritative cumulative record. Generic replay status
fields do not supersede that cumulative accounting. Replays add no sample.

Thirty learned states are nested in ten shared seed blocks and three source
histories; ninety policy contrasts are dependent.150 named choices include30
constructed neutral controls;120 real choices form76 distinct actions. First
responses were already paid in the released diagnostic study. Common five-step
continuation adds conditional first-action contrasts, not an unconditional causal
or universally superior optimization result. Query sharing is deterministic exact
response reuse and not demonstrated deployment net savings.
