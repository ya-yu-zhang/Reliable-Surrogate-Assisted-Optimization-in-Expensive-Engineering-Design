"""Build the complete scoped research packet and a verified repository patch."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile


def package(root):
    files = {}
    receipts = [(folder, json.loads((root/name).read_text())) for folder, name in
                [('baseline', 'baseline_receipt.json'), ('baseline_more', 'baseline_more_receipt.json')]]
    for folder, receipt in receipts:
        for item in receipt['verified_files']:
            files[folder+'/'+item['path']] = root/folder/item['path']
    paper = Path('paper/engineering_optimization')
    for item in receipts[0][1]['verified_files']:
        files['revision/'+item['path']] = root/'revision'/item['path']
    for name in ['integrated_evidence/pre_submission_checked_records.tex',
                 'integrated_evidence/gp_envelope_completion.tex',
                 'figures/transfer_cost_performance.pdf', 'figures/transfer_pilot_horizons.pdf',
                 'figures/gp_certified_envelope_comparison.pdf']:
        files['revision/'+str(paper/name)] = root/'revision'/paper/name
    for folder in ['restored', 'src', 'tests', 'results/innovation_readiness_20261014',
                   'results/gp_envelope_acceleration_20261014']:
        for path in (root/folder).rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
                files[str(path.relative_to(root))] = path
    # Preserve both supplied originals; immutable GP extraction is reproducible.
    for name in ['01-gp_reachability_20261013_results.zip', '02-EO_manuscript_completion_20261014.zip']:
        files['upload/'+name] = root/'upload'/name
    notes = ['PROJECT_CLOSURE_AND_REVIEW.md', 'REPRODUCE_PROJECT_CLOSURE.md', 'BACKUP_BEFORE_CLEANUP.md',
             'AUTHOR_INPUT_AND_EVIDENCE.md', 'PRE_SUBMISSION_ASSESSMENT.md', 'SUBMISSION_PACKET.md',
             'REPRODUCE_PRE_SUBMISSION_REVIEW.md', 'baseline_receipt.json', 'baseline_more_receipt.json',
             'repo_backup_inventory_20261014.json', 'project_closure_verification.json',
             'project_closure_verification_record.txt', 'project_closure_pdf_review.json',
             'unit_test_record_gp_completion.txt', 'unit_test_record.txt', 'runtime_record.json',
             'gp_envelope_execution_record.txt']
    for name in notes:
        files[name] = root/name
    for name in ['Manuscript_20261014.pdf', 'Supplement_20261014.pdf']:
        files['pdf/'+name] = root/'output/pdf'/name
    (root/'tmp').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='closure_patch_', dir=root/'tmp') as folder:
        folder = Path(folder)
        for side in ['before', 'after']:
            (folder/side).mkdir()
            for base, receipt in receipts:
                for item in receipt['verified_files']:
                    target = folder/side/item['path']
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(root/base/item['path'], target)
        # Immutable GP execution increment plus the current closure overlay.
        for source in (root/'gp_attachment').rglob('*'):
            if source.is_file() and source.name != 'DELIVERY_MANIFEST.json':
                target = folder/'after'/source.relative_to(root/'gp_attachment')
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
        for name, source in files.items():
            if name.startswith('revision/'):
                target = folder/'after'/name.removeprefix('revision/')
            elif name.startswith(('src/', 'tests/', 'results/gp_envelope_acceleration_20261014/',
                                  'results/innovation_readiness_20261014/')) or name.endswith('.md'):
                target = folder/'after'/name
            else:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        proc = subprocess.run(['git', 'diff', '--no-index', '--binary', '--src-prefix=a/',
                               '--dst-prefix=b/', 'before', 'after'], cwd=folder, capture_output=True)
        assert proc.returncode == 1
        patch = '\n'.join(line.replace('a/before/', 'a/').replace('a/after/', 'a/')
                          .replace('b/before/', 'b/').replace('b/after/', 'b/')
                          if line.startswith(('diff --git ', '--- ', '+++ ', 'Binary files ')) else line
                          for line in proc.stdout.decode().split('\n'))
        patch_path = root/'project_closure_from_58f539c2.patch'; patch_path.write_text(patch)
        applied = subprocess.run(['git', 'apply', str(patch_path)], cwd=folder/'before', capture_output=True)
        assert applied.returncode == 0, applied.stderr.decode()
        for path in (folder/'after').rglob('*'):
            if path.is_file():
                assert path.read_bytes() == (folder/'before'/path.relative_to(folder/'after')).read_bytes(), str(path.relative_to(folder/'after'))
    files['project_closure_from_58f539c2.patch'] = patch_path
    manifest = {'baseline_commit': receipts[0][1]['commit'], 'prepared_on': '2026-10-14',
                'scope': 'completed bounded manuscript, all inputs for new GP verification and computational increment',
                'contains_both_supplied_original_zip_bytes': True,
                'complete_historical_13_6_GB_archive_included': False,
                'complete_paired_mesh_raw_archive_included': False,
                'publisher_assets_excluded': ['interact.cls', 'tfcad.bst'],
                'repository_publication_performed': False,
                'patch_applies_and_matches_complete_overlay': True,
                'files': [{'path': name, 'bytes': path.stat().st_size,
                           'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
                          for name, path in sorted(files.items())]}
    destination = root/'deliverables/Paper_project_closure_20261014.zip'
    destination.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, path in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 10, 14, 0, 0, 0)); info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16; z.writestr(info, path.read_bytes(), compresslevel=9)
        info = zipfile.ZipInfo('PACKAGE_MANIFEST.json', (2026, 10, 14, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED; info.external_attr = 0o100644 << 16
        z.writestr(info, json.dumps(manifest, indent=2)+'\n', compresslevel=9)
    with zipfile.ZipFile(destination) as z:
        assert z.testzip() is None
        for item in manifest['files']:
            assert hashlib.sha256(z.read(item['path'])).hexdigest() == item['sha256']
        assert not any(Path(n).name in ['interact.cls', 'tfcad.bst'] for n in z.namelist())
    result = {'file': str(destination), 'bytes': destination.stat().st_size,
              'sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
              'members': len(files)+1, 'all_member_hashes_verified': True,
              'patch_applies_and_matches': True, 'both_original_attachments_preserved': True,
              'historical_archive_and_paired_raw_archive_complete': False}
    (root/'deliverables/project_closure_delivery_receipt.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    print(json.dumps(package(Path(__file__).resolve().parents[1]), indent=2))
