"""Install the unmodified official publisher template for local author use."""
from __future__ import annotations
import hashlib
import io
import json
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'paper/engineering_optimization'
URL = 'https://files.taylorandfrancis.com/InteractCADLaTeX.zip'
SHA256 = '5aeb0952b0021ad98653fe8ca6a1ea8edf35fbd639af5ee5443e6662dff90e25'


def install(archive: Path | None = None) -> dict:
    data = archive.read_bytes() if archive else urllib.request.urlopen(URL, timeout=60).read()
    digest = hashlib.sha256(data).hexdigest()
    if digest != SHA256:
        raise ValueError('Publisher template checksum changed; inspect the new archive before using it.')
    OUT.mkdir(parents=True, exist_ok=True)
    files = {}
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for name in ['interact.cls', 'tfcad.bst']:
            raw = z.read(name)
            (OUT / name).write_bytes(raw)
            files[name] = hashlib.sha256(raw).hexdigest()
    record = {'source_url': URL, 'archive_sha256': digest, 'files': files,
              'sample_version': 'v1.04 May 2023', 'class_version': 'v1.03 2016/10/17',
              'reference_style': 'Chicago author-date (official Interact-CAD bundle)',
              'journal_specific_instructions_fully_verified': False,
              'verification_limit': 'Official journal instructions endpoint returned HTTP 403.',
              'redistribution': 'Publisher assets installed locally; no public repository license is asserted.'}
    (OUT / 'template_provenance.json').write_text(json.dumps(record, indent=2) + '\n')
    return record

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--archive', type=Path)
    print(json.dumps(install(p.parse_args().archive), indent=2))
