"""Build a local, versioned minimum conditional-audit reproduction package.

This is not a complete historical raw-data archive and does not publish any
binary or previously rejected payload. It contains existing budget raw records,
the paired CSV used in replay, current sources/PDFs and explicit scope records.
"""
from __future__ import annotations
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / 'paper/engineering_optimization'
DEST = PAPER / 'submission_revision_20261013'


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    reference = json.loads((PAPER / 'review_revision/analysis.json').read_text())
    paths = set(reference['source_files_sha256'])
    for p, digest in reference['source_files_sha256'].items():
        assert sha((ROOT / p).read_bytes()) == digest, p
    paths.update(str(p.relative_to(ROOT)) for p in (ROOT / 'src').glob('*.py'))
    paths.update(str(p.relative_to(ROOT)) for p in (ROOT / 'tests').glob('test_*.py'))
    paths.update(str(p.relative_to(ROOT)) for p in (PAPER / 'integrated_evidence').glob('*.tex'))
    paths.update(str(p.relative_to(ROOT)) for p in (PAPER / 'figures').glob('*') if p.is_file())
    for folder in [PAPER / 'review_revision', DEST]:
        paths.update(str(p.relative_to(ROOT)) for p in folder.iterdir()
                     if p.is_file() and p.suffix in {'.md', '.json', '.csv', '.txt'}
                     and p.name not in {'delivery_manifest.json', 'package_verification.json'})
    for n in ['EO_manuscript.tex', 'EO_supplementary.tex', 'EO_references.bib',
              'EO_manuscript.pdf', 'EO_supplementary.pdf', 'interact.cls', 'tfcad.bst',
              'template_provenance.json', 'pdf_build_status.json', 'work_status.json']:
        paths.add(str((PAPER / n).relative_to(ROOT)))
    paths.update(str(p.relative_to(ROOT)) for p in ROOT.glob('requirements*txt'))
    paths.add('README.md')
    contents = {p: (ROOT / p).read_bytes() for p in sorted(paths)}
    contents['REPRODUCTION_SCOPE.md'] = b'''# Minimum conditional-audit reproduction package

This version contains 30 dependent states in ten complete budget-validation
seed blocks, frozen v1 code/configuration, the published paired-contrast CSV,
current manuscript sources/figures and working PDFs. All-author
approval is excluded from the project task list; affiliations b/c remain blank.
This is not the full historical experiment archive, physical convergence
certification, independent new validation or a publisher-policy certificate.

In Python3.12, the core replay and following tests use the standard library:

    python verify_package.py
    python -m src.analyze_review_revision
    python -m src.analyze_operational_comparison
    python -m src.integrate_submission_revision
    python verify_package.py
    python -m unittest tests.test_budgeted_decision_audit tests.test_review_revision tests.test_operational_comparison

Seven review-analysis outputs, three operational-analysis outputs, two new TeX
inputs and current sources should remain byte-identical. This does not refit
GPs or call a physical solver. The original numerical replay and full relevant
tests require the documented external dependencies. Use requirements-budget-
audit.txt where that fuller verification is intended.

To compile with a complete TeX installation (including Latin Modern fonts),
from paper/engineering_optimization run pdflatex, bibtex, then pdflatex twice
for each of EO_manuscript and EO_supplementary. Class/style hashes match the
official publisher bundle; no general redistribution license is asserted.

Read submission_revision_20261013/CORE_OBJECT_AND_CLOSEST_WORK.md and
AI_USE_HISTORY_AUDIT.md in that paper directory for remaining novelty and
historical AI-policy limits. No previously rejected public raw/PDF payload
has been retried or indirectly published by producing this local package.
'''
    contents['verify_package.py'] = b'''from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parent
m=json.loads((r/'PACKAGE_MANIFEST.json').read_text())
for p,h in m['files_sha256'].items():
    assert hashlib.sha256((r/p).read_bytes()).hexdigest()==h,p
print('Verified',len(m['files_sha256']),'package files; scope:',m['scope'])
'''
    manifest = {'scope': 'minimum conditional-audit replay and current working manuscript; not all historical experiments',
                'baseline_commit': 'a8a04d797c23a6c205fbf48f83c127a8903bfae4',
                'original_analysis_inputs': len(reference['source_files_sha256']),
                'new_physics_attempts': 0, 'all_author_approval_task_required': False,
                'files_sha256': {p: sha(b) for p, b in contents.items()}}
    contents['PACKAGE_MANIFEST.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
    archive = PAPER / 'EO_conditional_evidence_20261013.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p, b in sorted(contents.items()):
            info = zipfile.ZipInfo(p, date_time=(2026, 10, 13, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, b)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for p, b in contents.items():
            assert z.read(p) == b
    delivery = {'archive': str(archive.relative_to(ROOT)), 'sha256': sha(archive.read_bytes()),
                'bytes': archive.stat().st_size, 'members': len(contents), 'scope': manifest['scope'],
                'all_author_approval_task_required': False,
                'public_binary_upload_attempted': False,
                'documents': json.loads((PAPER / 'pdf_build_status.json').read_text())['documents'],
                'files_sha256': manifest['files_sha256']}
    (DEST / 'delivery_manifest.json').write_text(json.dumps(delivery, indent=2) + '\n')
    print(json.dumps({k: delivery[k] for k in ['archive', 'sha256', 'bytes', 'members']}))


if __name__ == '__main__':
    main()
