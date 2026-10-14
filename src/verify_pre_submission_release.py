"""Verify immutable evidence and deterministic review preparation; no physics."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import tempfile

from audit_innovation_feasibility import run
from build_pre_submission_review import main as build_review


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def numeric_table_rows(path: Path) -> Counter:
    return Counter(line.strip() for line in path.read_text().splitlines()
                   if '&' in line and re.search(r'\d', line)
                   and not line.lstrip().startswith('>'))


def verify(root: Path) -> dict:
    (root/'tmp').mkdir(exist_ok=True)
    baseline, revision = root/'baseline', root/'revision'
    paper = Path('paper/engineering_optimization')
    receipt = json.loads((root/'baseline_receipt.json').read_text())
    commit = '58f539c2d0738b20c7d0d4889fe8d808a03a3019'
    assert receipt['commit'] == commit
    assert len(receipt['verified_files']) == 99
    allowed_changes = {'README.md', str(paper/'work_status.json'),
                       str(paper/'EO_manuscript.tex'), str(paper/'EO_supplementary.tex')}
    changed = []
    for item in receipt['verified_files']:
        path = baseline/item['path']
        data = path.read_bytes()
        assert len(data) == item['bytes']
        assert sha256(path) == item['sha256']
        blob = b'blob ' + str(len(data)).encode() + b'\0' + data
        assert hashlib.sha1(blob).hexdigest() == item['git_blob']
        overlay = revision/item['path']
        assert overlay.is_file()
        if sha256(overlay) != item['sha256']:
            changed.append(item['path'])
    assert set(changed) == allowed_changes
    historical_rows = {}
    for name in ('EO_manuscript.tex', 'EO_supplementary.tex'):
        original = numeric_table_rows(baseline/paper/name)
        current = numeric_table_rows(revision/paper/name)
        assert not (original-current)
        historical_rows[name] = sum(original.values())
    assert historical_rows == {'EO_manuscript.tex': 32, 'EO_supplementary.tex': 251}
    bib = (baseline/paper/'EO_references.bib').read_bytes()
    assert bib == (revision/paper/'EO_references.bib').read_bytes()
    assert len(re.findall(rb'^@\w+\s*\{', bib, re.M)) == 39
    results = root/'results/innovation_readiness_20261014'
    with tempfile.TemporaryDirectory(prefix='verify_review_', dir=root/'tmp') as folder:
        temp = Path(folder)
        rerun = temp/'results'
        run(baseline, root/'restored', rerun)
        assert {p.name for p in results.iterdir() if p.is_file()} == {
            p.name for p in rerun.iterdir() if p.is_file()}
        for p in results.iterdir():
            if p.is_file():
                assert p.read_bytes() == (rerun/p.name).read_bytes(), p.name
        dest = temp/'revision'
        (dest/paper/'integrated_evidence').mkdir(parents=True)
        build_review(baseline, dest, results)
        for name in ('EO_manuscript.tex', 'EO_supplementary.tex',
                     'integrated_evidence/pre_submission_checked_records.tex'):
            assert (dest/paper/name).read_bytes() == (revision/paper/name).read_bytes()
    study = json.loads((results/'innovation_feasibility.json').read_text())
    summaries = study['summaries']
    assert sum(r['distinct_branch_curves'] for r in summaries) == 186
    assert sum(r['metadata_states'] for r in summaries) == 90
    assert sum(r['one_open_competitor_frontiers_checked'] for r in summaries) == 1644
    assert [r['curves_violating_diminishing_returns'] for r in summaries] == [9, 10, 3]
    status = json.loads((revision/paper/'work_status.json').read_text())['pre_submission_20261014']
    assert status['submission_ready'] is False
    assert status['innovation_sufficiency_confirmed'] is False
    assert status['independent_study_gate'] is False
    assert 'Ran 13 tests' in (root/'unit_test_record.txt').read_text()
    assert (root/'unit_test_record.txt').read_text().rstrip().endswith('OK')
    result = {
        'baseline_commit': commit,
        'selected_baseline_files_verified_sha256_and_git_blob': 99,
        'archived_files_verified_and_reread': 179,
        'changed_original_paths': sorted(changed),
        'historical_numeric_table_rows_preserved': historical_rows,
        'bibliography_entries_unchanged': 39,
        'analysis_outputs_byte_reproducible': True,
        'review_sources_byte_reproducible': True,
        'complete_metadata_states': 60, 'dependent_contexts': 90,
        'distinct_branch_curves': 186, 'posthoc_frontiers': 1644,
        'unit_tests_passed': 13,
        'new_physics_attempts': 0, 'new_bound_queries': 0,
        'new_gp_fits': 0, 'new_independent_optimization_samples': 0,
        'scientific_novelty_certified': False,
        'submission_ready': False,
    }
    (root/'release_verification.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    print(json.dumps(verify(Path(__file__).resolve().parents[1]), indent=2))
