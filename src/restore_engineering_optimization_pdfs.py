"""Restore compiled review PDFs from a checksum-verified lossless text release."""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import lzma
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'paper/engineering_optimization'


def restore(output=BASE,release=BASE/'pdf_release'):
    manifest=json.loads((release/'manifest.json').read_text())
    checked=[]
    for record in manifest['documents']:
        segments=[]
        for segment in record['segments']:
            raw=(release/segment['path']).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=segment['sha256']:
                raise ValueError('Corrupt release segment: '+segment['path'])
            segments.append(raw.decode('ascii').strip())
        raw=lzma.decompress(base64.b85decode(''.join(segments)))
        if len(raw)!=record['bytes'] or hashlib.sha256(raw).hexdigest()!=record['sha256']:
            raise ValueError('PDF checksum mismatch: '+record['name'])
        if not raw.startswith(b'%PDF-'): raise ValueError('Invalid PDF header')
        checked.append((record['name'],raw))
    # Validate every input before writing any output; never overwrite a different file.
    for name,raw in checked:
        target=output/name
        if target.exists() and target.read_bytes()!=raw:
            raise FileExistsError('Refusing to overwrite a different file: '+str(target))
    output.mkdir(parents=True,exist_ok=True)
    for name,raw in checked:(output/name).write_bytes(raw)
    return {'restored':[name for name,_ in checked],'verified':True}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=BASE)
    print(json.dumps(restore(p.parse_args().output),indent=2))
