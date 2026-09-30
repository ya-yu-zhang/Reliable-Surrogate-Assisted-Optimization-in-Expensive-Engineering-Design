"""Read-only scientific records audit; does not import or call an objective."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / 'results/interruption_20260918_v1'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def load(path):
    return json.loads(path.read_text('utf-8'))


def main():
    manifest = load(ARCHIVE / 'recovery_manifest.json')
    for name, expected in manifest['recovery_sources'].items():
        assert digest(ROOT / name) == expected, name
    completed, pending = [], []
    for item in manifest['partial_runs']:
        old = ROOT / item['archive']
        for name, expected in item['file_sha256'].items():
            assert digest(old / name) == expected, str(old / name)
        events = [json.loads(v) for v in (old / 'events.jsonl').read_text('utf-8').splitlines()]
        assert len(events) == 1 + 2 * item['paid_labels']
        assert all(a['event'] == 'pre' and b['event'] == 'label' and a['t'] == b['t']
                   for a, b in zip(events[1::2], events[2::2]))
        if item['source'] == 'budget_prefix_integrity_v1':
            current = ROOT / 'results/budget_prefix_integrity_v1/budget_15D' / item['runid']
        else:
            current = ROOT / 'results' / item['source'] / item['runid']
        sidecar = current / 'recovery.json'
        if not sidecar.exists():
            pending.append(item['runid'])
            continue
        recovered = load(sidecar)
        assert recovered['original_journal_sha256'] == digest(old / 'events.jsonl')
        assert recovered['old_paid_calls'] == item['paid_labels']
        assert recovered['complete_prefix_states_and_labels_equal'] is True
        assert recovered['elapsed_is_reconstruction_segment_not_uninterrupted_runtime'] is True
        assert recovered['source_sha256'] == digest(ROOT / 'src/recover_interrupted_run.py')
        full = [json.loads(v) for v in (current / 'events.jsonl').read_text('utf-8').splitlines()]
        for a, b in zip(full[1:len(events)], events[1:]):
            a.pop('preparation_seconds', None)
            b.pop('preparation_seconds', None)
            assert a == b
        physical = [json.loads(v) for v in (current / 'recovery_physical_calls.jsonl').read_text('utf-8').splitlines()]
        assert len(physical) == 2 * recovered['new_paid_calls']
        for i, (pre, label) in enumerate(zip(physical[::2], physical[1::2]), 1):
            t = item['paid_labels'] + i
            assert pre['event'] == 'pre' and label['event'] == 'label'
            assert pre['t'] == label['t'] == t
            assert pre['x'] == full[2*t-1]['x']
            assert label['y'] == full[2*t]['y']
        assert len(full) == 1 + 2 * recovered['physical_total']
        summary = load(current / 'summary.json')
        assert summary['algorithm_evaluations'] == recovered['physical_total']
        assert recovered['old_paid_calls'] + recovered['new_paid_calls'] == recovered['physical_total']
        completed.append({k: recovered[k] for k in ['runid', 'old_paid_calls', 'new_paid_calls', 'physical_total']})
    prefix = ROOT / 'results/budget_prefix_integrity_v1'
    audit = load(prefix / 'audit.json')
    assert audit['complete'] and audit['all_three_budget_prefixes_equal'] and not audit['performance_sample']
    hashes = load(prefix / 'source_hashes.json')
    assert len(hashes) == 135
    for name, expected in hashes.items():
        assert digest(ROOT / name) == expected, name
    provenance = load(ARCHIVE / 'console_provenance.json')
    for item in provenance['original_console_records']:
        assert digest(ARCHIVE / 'console_records' / item['source'] / (item['runid'] + '.log')) == item['sha256']
    for item in provenance['cache_console_overwrites']:
        derived = load(ARCHIVE / 'console_records' / item['source'] / (item['runid'] + '.derived.json'))
        summary = load(ROOT / 'results' / item['source'] / item['runid'] / 'summary.json')
        for key in ['runid', 'algorithm_evaluations', 'elapsed', 'process_peak_working_set_bytes', 'warning_counts']:
            assert derived[key] == summary[key]
        assert 'original console output overwritten' in derived['provenance']
    # Reuse the frozen read-only per-run auditor without computing a partial-batch performance table.
    from .analyze_gp_references import adapter_hash, audit_run
    original_files = provenance['original_console_records'] + provenance['cache_console_overwrites']
    assert len(original_files) == 335
    complete_hashes = []
    expected_hash = adapter_hash()
    for item in original_files:
        _, _, raw_hashes = audit_run(ROOT / 'results' / item['source'] / item['runid'] / 'summary.json', expected_hash)
        complete_hashes.append(dict(source=item['source'], **raw_hashes))
    (ARCHIVE / 'completed_original_raw_audit.json').write_text(json.dumps(dict(
        objective_calls=0, audited_runs=len(complete_hashes), hash_time='post-recovery-cache-validation',
        pre_interruption_byte_snapshot_available=False, source_sha256=digest(ROOT / 'src/analyze_gp_references.py'),
        raw_file_hashes=complete_hashes), indent=2), encoding='utf-8')
    stages = {name: load(ROOT / 'results' / name / 'status.json')
              for name in ['turbo_reference_v1', 'gp_ei_reference_v1']}
    result = dict(audited_at_utc=datetime.now(timezone.utc).isoformat(), objective_calls=0,
                  auditor_sha256=digest(Path(__file__)),
                  frozen_recovery_sources_verified=len(manifest['recovery_sources']),
                  archived_partial_runs_verified=len(manifest['partial_runs']),
                  prefix_result_hashes_verified=len(hashes), prefix_fixture_calls=6300,
                  original_console_records_verified=len(provenance['original_console_records']),
                  derived_console_records_verified=len(provenance['cache_console_overwrites']),
                  original_completed_runs_structurally_audited=len(complete_hashes),
                  completed_recoveries=completed, pending_recoveries=pending,
                  formal_batch_statuses=stages,
                  full_formal_batches_complete=all(v['completed'] == v['expected'] == 648 and v['failed'] == 0
                                                   and v['stage'] == 'complete' for v in stages.values()),
                  note='Pending runs are not inspected for performance. Derived records are not original console output.')
    (ARCHIVE / 'records_audit.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
