"""Freeze an already reviewed application protocol without objective calls."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def main():
    destination=ROOT/'docs/frozen_application_formal_v1'
    if destination.exists():raise RuntimeError('Application freeze already exists; refuse overwrite')
    assert not (ROOT/'results/application_formal_v1').exists()
    assert sys.version.split()[0]=='3.12.13'
    resource=json.loads((ROOT/'docs/frozen_application_precheck_v1/sha256.json').read_text('utf-8'))
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest for name,digest in resource.items())
    packages={d.metadata['Name']:d.version for d in importlib.metadata.distributions()}
    (ROOT/'docs/application-formal-environment.json').write_text(json.dumps(
        dict(python_version=sys.version.split()[0],packages=dict(sorted(packages.items()))),indent=2),encoding='utf-8')
    lock=subprocess.run(['uv','pip','freeze','--python',sys.executable],capture_output=True,
        text=True,encoding='utf-8',check=True)
    (ROOT/'docs/application-formal-environment-lock.txt').write_text(lock.stdout,encoding='utf-8')
    names=set(Path(name).as_posix() for name in resource)
    names.update(['docs/LassoBench正式机制迁移预先协议.md','configs/application_formal.json',
        'src/generic_internal.py','src/application_methods.py','src/application_experiment.py',
        'src/run_application_batch.py','src/finish_application_batch.py','src/analyze_application.py',
        'src/freeze_application_protocol.py','src/__init__.py','src/core.py','src/experiment.py',
        'src/gp_references.py','src/run_solo_cost.py','src/basic_references.py',
        'docs/application-formal-environment.json','docs/application-formal-environment-lock.txt',
        'requirements-application.txt','requirements-application-gp.txt',
        'tests/test_callable_transfer_integrity.py','tests/test_application_gp_transfer.py',
        'tests/test_application_worker_boundary.py','literature/downloads/dna_source.json',
        'literature/downloads/dna_cache_provenance.json','literature/downloads/dna.scale',
        'literature/downloads/libsvm-cache/libsvm/dna_X.npz',
        'literature/downloads/libsvm-cache/libsvm/dna_y.npy',
        'docs/frozen_application_precheck_v1/sha256.json','literature/source-code/TuRBO/LICENSE.md'])
    names.update(path.relative_to(ROOT).as_posix() for path in (ROOT/'literature/source-code/TuRBO/turbo').glob('*.py'))
    hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sorted(names)}
    destination.mkdir()
    for name in hashes:
        target=destination/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    (destination/'sha256.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
    (destination/'freeze_manifest.json').write_text(json.dumps(dict(files=len(hashes),
        formal_optimization_labels_before_freeze=0,resource_objective_calls=18,
        source_hashes_sha256=hashlib.sha256((destination/'sha256.json').read_bytes()).hexdigest(),
        original_resource_freeze_verified=True),indent=2),encoding='utf-8')
    print(json.dumps(dict(frozen_files=len(hashes),formal_objective_labels=0),indent=2))


if __name__=='__main__':main()
