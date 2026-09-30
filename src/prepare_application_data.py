"""Provision the verified official DNA bytes using the original library parser."""
import hashlib
import json
import os
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
RAW_SHA256 = '03d39477c5e48415e9cd18e006efc8f7a3b5c3deaee8289a72511c35070e3cfe'


def main():
    raw = ROOT/'literature/downloads/dna.scale'
    body = raw.read_bytes()
    assert hashlib.sha256(body).hexdigest()==RAW_SHA256 and len(body.splitlines())==2000
    provenance = json.loads((raw.parent/'dna_source.json').read_text('utf-8'))
    assert provenance['sha256']==RAW_SHA256 and provenance['tls_certificate_verification']
    cache = ROOT/'literature/downloads/libsvm-cache'
    os.environ['LIBSVMDATA_HOME'] = str(cache)
    from libsvmdata.core import ALL_DATASETS
    dataset = ALL_DATASETS['dna']; directory = dataset.dataset_dir
    assert directory.resolve().is_relative_to(cache.resolve())
    directory.mkdir(parents=True,exist_ok=True)
    destination = directory/dataset.dataset_file
    if destination.exists():
        assert hashlib.sha256(destination.read_bytes()).hexdigest()==RAW_SHA256
    else:
        shutil.copy2(raw,destination)
    # This is exactly the unmodified decoder used by get_X_y after download.
    X,y = dataset._load_file_and_save_data(destination,directory/dataset.dataset_name)
    assert X.shape==(2000,180) and y.shape==(2000,)
    record = dict(raw_sha256=RAW_SHA256,official_url=provenance['url'],tls_verified=True,
        original_library_parser_used=True,source_matrix_shape=list(X.shape),
        cache_files_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.glob('dna_*')},
        objective_calls=0,test_method_calls=0)
    (raw.parent/'dna_cache_provenance.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print(json.dumps(record,indent=2))


if __name__=='__main__':main()
