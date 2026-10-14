"""Package the scoped evidence without publisher assets or internal transfers."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile


def package(root: Path) -> dict:
    (root/'tmp').mkdir(exist_ok=True)
    paper = Path('paper/engineering_optimization')
    receipt = json.loads((root/'baseline_receipt.json').read_text())
    files = {}
    for item in receipt['verified_files']:
        name = item['path']
        files['baseline/'+name] = root/'baseline'/name
        files['revision/'+name] = root/'revision'/name
    new_review = [paper/'integrated_evidence/pre_submission_checked_records.tex',
                  paper/'figures/transfer_cost_performance.pdf',
                  paper/'figures/transfer_pilot_horizons.pdf']
    for name in new_review:
        files['revision/'+str(name)] = root/'revision'/name
    for folder, pattern in [('src', '*.py'), ('tests', '*.py'),
                            ('results/innovation_readiness_20261014', '*')]:
        for path in (root/folder).glob(pattern):
            if path.is_file():
                files[str(path.relative_to(root))] = path
    for path in (root/'restored').rglob('*'):
        if path.is_file():
            files[str(path.relative_to(root))] = path
    for name in ['PRE_SUBMISSION_ASSESSMENT.md', 'AUTHOR_INPUT_AND_EVIDENCE.md',
                 'REPRODUCE_PRE_SUBMISSION_REVIEW.md', 'SUBMISSION_PACKET.md',
                 'baseline_receipt.json', 'release_verification.json',
                 'release_verification_record.txt', 'runtime_record.json',
                 'unit_test_record.txt', 'pdf_review.json']:
        files[name] = root/name
    for name in ['EO_manuscript', 'EO_supplementary']:
        files[f'pdf/{name}_review_20261014.pdf'] = root/'revision'/paper/'build'/(name+'.pdf')
    # Build a reviewable git patch from an isolated snapshot, not a remote write.
    with tempfile.TemporaryDirectory(prefix='patch_review_', dir=root/'tmp') as temp:
        temp = Path(temp)
        for side in ('before', 'after'):
            (temp/side).mkdir()
        for item in receipt['verified_files']:
            for side, source in [('before', 'baseline'), ('after', 'revision')]:
                target = temp/side/item['path']
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(root/source/item['path'], target)
        additions = {str(name): root/'revision'/name for name in new_review}
        additions.update({name: path for name, path in files.items()
                          if name.startswith(('src/', 'tests/', 'results/innovation_readiness_20261014/'))
                          or name in ['PRE_SUBMISSION_ASSESSMENT.md', 'AUTHOR_INPUT_AND_EVIDENCE.md',
                                      'REPRODUCE_PRE_SUBMISSION_REVIEW.md', 'SUBMISSION_PACKET.md']})
        for name, source in additions.items():
            target = temp/'after'/name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        process = subprocess.run(['git', 'diff', '--no-index', '--binary',
                                  '--src-prefix=a/', '--dst-prefix=b/', 'before', 'after'],
                                 cwd=temp, capture_output=True, check=False)
        assert process.returncode == 1, process.stderr.decode(errors='replace')
        text = process.stdout.decode()
        patch = '\n'.join(line.replace('a/before/', 'a/').replace('a/after/', 'a/')
                          .replace('b/before/', 'b/').replace('b/after/', 'b/')
                          if line.startswith(('diff --git ', '--- ', '+++ ', 'Binary files ')) else line
                          for line in text.splitlines())+'\n'
        patch_path = root/'changes_from_58f539c2.patch'
        patch_path.write_text(patch)
        # Apply the exact patch in the isolated baseline tree, and compare bytes.
        check = subprocess.run(['git', 'apply', '--check', str(patch_path)],
                               cwd=temp/'before', capture_output=True)
        assert check.returncode == 0, check.stderr.decode(errors='replace')
        applied = subprocess.run(['git', 'apply', str(patch_path)],
                                 cwd=temp/'before', capture_output=True)
        assert applied.returncode == 0, applied.stderr.decode(errors='replace')
        for p in (temp/'after').rglob('*'):
            if p.is_file():
                assert p.read_bytes() == (temp/'before'/p.relative_to(temp/'after')).read_bytes()
    files['changes_from_58f539c2.patch'] = patch_path
    manifest = {
        'baseline_commit': receipt['commit'], 'prepared_on': '2026-10-14',
        'document_status': 'author-review; novelty and submission gates false',
        'publisher_assets_excluded': ['interact.cls', 'tfcad.bst'],
        'full_historical_archive_included': False, 'private_gp_proof_package_included': False,
        'patch_applies_to_selected_baseline_and_matches_overlay': True,
        'files': [{'path': name, 'bytes': path.stat().st_size,
                   'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
                  for name, path in sorted(files.items())]}
    manifest_bytes = (json.dumps(manifest, indent=2)+'\n').encode()
    out = root/'deliverables'
    out.mkdir(exist_ok=True)
    archive = out/'EO_manuscript_completion_20261014.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, path in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 10, 14, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, path.read_bytes(), compresslevel=9)
        info = zipfile.ZipInfo('PACKAGE_MANIFEST.json', (2026, 10, 14, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        z.writestr(info, manifest_bytes, compresslevel=9)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for item in manifest['files']:
            assert hashlib.sha256(z.read(item['path'])).hexdigest() == item['sha256']
        assert len(z.namelist()) == len(files)+1
        assert not any(Path(name).name in {'interact.cls', 'tfcad.bst'} for name in z.namelist())
    result = {'archive': str(archive), 'bytes': archive.stat().st_size,
              'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
              'members': len(files)+1, 'all_member_hashes_verified': True,
              'patch_applies_and_matches': True, 'submission_ready': False}
    (out/'delivery_receipt.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    print(json.dumps(package(Path(__file__).resolve().parents[1]), indent=2))
