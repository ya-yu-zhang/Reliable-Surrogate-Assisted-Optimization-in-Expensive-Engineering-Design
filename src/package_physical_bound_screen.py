"""Package acquired physical-bound records and verify isolated analysis only.

Never repeats a physical solve. The separate numeric verification has already
recomputed1720 bounds; this package pass runs9 toy/pool tests and3 analyses.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'paper/engineering_optimization/physical_bound_screen_20261013'


def main():
    report = json.loads((DEST / 'analysis.json').read_text())
    raw = ROOT / 'results/engineering_optimization_physical_bound_screen_v1'
    plan = json.loads((raw / 'plan.json').read_text())
    expected = {**report['source_files_sha256'], **plan['frozen_files_sha256']}
    for p, digest in expected.items():
        assert hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == digest, p
    files = set(expected) | {'src/__init__.py', 'tests/__init__.py',
        'src/analyze_monotone_development.py', 'src/monotone_horizon_audit.py',
        'src/verify_physical_bound_screen.py', 'src/package_physical_bound_screen.py',
        'src/correct_repository_availability.py',
        'README.md', 'paper/engineering_optimization/work_status.json',
        'paper/engineering_optimization/EO_manuscript.tex',
        'paper/engineering_optimization/EO_supplementary.tex',
        'paper/engineering_optimization/integrated_evidence/supp_records.tex',
        'paper/engineering_optimization/integrated_evidence/table_inputs.json',
        'paper/engineering_optimization/pdf_build_status.json',
        'requirements-engineering-gp-audit.txt'}
    files.update(str(p.relative_to(ROOT)) for p in DEST.iterdir()
                 if p.suffix in {'.md', '.json', '.csv', '.txt'}
                 and p.name not in {'package_verification.json', 'delivery.json'})
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix='physical_bound_verify_', dir=ROOT.parent) as temp:
        target = Path(temp)
        for name in files:
            dst = target / name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, dst)
        test = subprocess.run([sys.executable, '-m', 'unittest', 'tests.test_reduced_compliance_bounds',
                               'tests.test_physical_bound_screen', '-v'], cwd=target,
                              text=True, capture_output=True, check=True)
        assert 'Ran 9 tests' in test.stderr and test.stderr.rstrip().endswith('OK')
        subprocess.run([sys.executable, '-m', 'src.physical_bound_screen', '--analyze'], cwd=target,
                       capture_output=True, text=True, check=True)
        outputs = {}
        for name in ['analysis.json', 'summary.csv', 'state_sharpness.csv']:
            original = (DEST / name).read_bytes()
            assert (target / DEST.relative_to(ROOT) / name).read_bytes() == original, name
            outputs[name] = hashlib.sha256(original).hexdigest()
    verification = {'exact_source_hashes_checked': len(expected), 'isolated_toy_pool_tests_passed': 9,
        'full_relevant_tests_passed': 55, 'isolated_byte_identical_analysis_outputs': outputs,
        'package_verification_new_physics_attempts': 0,
        'package_verification_bound_design_queries': 0,
        'package_verification_analysis_and_test_seconds': time.perf_counter() - started,
        'scope': 'separate from original1720-bound screen and1720-bound numerical replay'}
    (DEST / 'package_verification.json').write_text(json.dumps(verification, indent=2) + '\n')
    files.add(str((DEST / 'package_verification.json').relative_to(ROOT)))
    archive = ROOT / 'paper/engineering_optimization/EO_physical_bound_screen_20261013.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for name in sorted(files):
            info = zipfile.ZipInfo(name, (2026, 10, 13, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, (ROOT / name).read_bytes(), compresslevel=9)
    with zipfile.ZipFile(archive) as bundle:
        assert set(bundle.namelist()) == files
        for name in files:
            assert bundle.read(name) == (ROOT / name).read_bytes(), name
    delivery = {'path': str(archive.relative_to(ROOT)), 'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
                'bytes': archive.stat().st_size, 'members': len(files),
                'scope': 'scoped development inputs, readable physical references, code/tests, reports, analyses and factual source overlay inputs; no full historical archive or manuscript PDF/template assets',
                'public_binary_upload_attempted': False, 'original_physical_attempts': 2,
                'protocol_commit': plan.get('protocol_commit', report['protocol_commit'])}
    (DEST / 'delivery.json').write_text(json.dumps(delivery, indent=2) + '\n')
    print(json.dumps({'verification': verification, 'delivery': delivery}))


if __name__ == '__main__':
    main()
