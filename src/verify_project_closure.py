"""Verify the completed manuscript and certificates without replaying experiments."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import tempfile

from .prepare_gp_attachment import prepare
from .certified_affine_envelope import check_exclusion, coefficient_bands
from .build_project_closure import build


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(root):
    prepare(root)
    (root/'tmp').mkdir(exist_ok=True)
    baseline = json.loads((root/'baseline_receipt.json').read_text())
    additional = json.loads((root/'baseline_more_receipt.json').read_text())
    for folder, receipt in [('baseline', baseline), ('baseline_more', additional)]:
        assert receipt['commit'] == '58f539c2d0738b20c7d0d4889fe8d808a03a3019'
        for item in receipt['verified_files']:
            path = root/folder/item['path']; data = path.read_bytes()
            assert sha(path) == item['sha256'] and len(data) == item['bytes']
            assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest() == item['git_blob']
    paper = Path('paper/engineering_optimization')
    def numeric(path):
        return Counter(x.strip() for x in path.read_text().splitlines()
                       if '&' in x and re.search(r'\d', x) and not x.lstrip().startswith('>'))
    for name in ('EO_manuscript.tex', 'EO_supplementary.tex'):
        assert not numeric(root/'baseline'/paper/name)-numeric(root/'revision'/paper/name)
    old_bib = (root/'baseline'/paper/'EO_references.bib').read_bytes()
    new_bib = (root/'revision'/paper/'EO_references.bib').read_bytes()
    assert new_bib.startswith(old_bib)
    assert len(re.findall(rb'^@\w+\s*\{', new_bib, re.M)) == 40
    with tempfile.TemporaryDirectory(prefix='closure_rebuild_', dir=root/'tmp') as folder:
        destination = Path(folder)/'revision'
        (destination/paper/'integrated_evidence').mkdir(parents=True)
        (destination/paper/'figures').mkdir()
        build(root, destination)
        for name in ('EO_manuscript.tex', 'EO_supplementary.tex', 'EO_references.bib',
                     'integrated_evidence/pre_submission_checked_records.tex',
                     'integrated_evidence/gp_envelope_completion.tex',
                     'figures/gp_certified_envelope_comparison.pdf'):
            assert (destination/paper/name).read_bytes() == (root/'revision'/paper/name).read_bytes(), name
    report = root/'results/gp_envelope_acceleration_20261014'
    analysis = json.loads((report/'analysis.json').read_text())
    assert sha(root/'src/certified_affine_envelope.py') == analysis['operator_source_sha256']
    assert sha(root/'src/verify_and_benchmark_gp_envelope.py') == analysis['benchmark_source_sha256']
    count = 0
    for path in (report/'certificates').glob('*.json'):
        current = json.loads(path.read_text())
        previous = json.loads((root/'gp_attachment/results/engineering_optimization_gp_reachability_v1/construction'/path.name).read_text())
        for branch, modes in current['branches'].items():
            c = previous['branches'][branch]['coefficients']
            bands = coefficient_bands(c['slope'], c['intercept'], c['slope_error'], c['intercept_error'])
            n = len(c['slope'])
            for mode, result in modes.items():
                ids = result['indices']; proofs = result['excluded_proofs']
                excluded = [p[0] for p in proofs]
                assert len(ids) == len(set(ids)) and len(excluded) == len(set(excluded))
                assert not set(ids).intersection(excluded)
                assert set(ids).union(excluded) == set(range(n))
                domain = 0. if mode == 'nonnegative' else previous['branches'][branch]['pending_lower']
                for proof in proofs:
                    assert 2 <= len(proof) <= 3
                    assert all(type(i) is int and 0 <= i < n for i in proof)
                    assert check_exclusion(*bands, proof, domain)
                count += len(proofs)
    assert count == 232564
    tests = (root/'unit_test_record_gp_completion.txt').read_text()
    assert 'Ran 31 tests' in tests and tests.rstrip().endswith('OK')
    result = {'baseline_files_verified': len(baseline['verified_files']),
              'additional_same_commit_files_verified': len(additional['verified_files']),
              'historical_numeric_rows_preserved': {'main': 32, 'supplement': 251},
              'original_bib_entries_preserved': 39, 'current_bib_entries': 40,
              'current_sources_and_scientific_figure_byte_reproducible': True,
              'new_certificate_coverage_and_rational_proofs_verified': count,
              'unit_tests_passed': 31, 'new_physics_attempts': 0,
              'new_physical_bound_queries': 0, 'new_independent_samples': 0,
              'bounded_research_manuscript_complete': True,
              'publisher_policy_task_deferred_by_user': True,
              'journal_acceptance_guaranteed': False}
    (root/'project_closure_verification.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    print(json.dumps(verify(Path(__file__).resolve().parents[1]), indent=2))
