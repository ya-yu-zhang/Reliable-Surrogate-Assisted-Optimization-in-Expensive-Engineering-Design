"""Restore the immutable supplied GP ZIP; no experiment or overwrite."""
import hashlib
import json
from pathlib import Path
import zipfile


def prepare(root):
    archive = root/'upload/01-gp_reachability_20261013_results.zip'
    expected = '25501c61eedfb379312693829be3fe612c2285ed5f2e7e677c3dc4892ca8b139'
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == expected
    destination = root/'gp_attachment'
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for item in z.infolist():
            name = Path(item.filename)
            assert not name.is_absolute() and '..' not in name.parts
            assert (item.external_attr >> 16) & 0o170000 != 0o120000
            if item.is_dir():
                continue
            target = destination/name
            data = z.read(item)
            if target.exists():
                assert target.read_bytes() == data, name
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
    manifest = json.loads((destination/'DELIVERY_MANIFEST.json').read_text())
    for item in manifest['files']:
        p = destination/item['path']
        assert p.stat().st_size == item['bytes']
        assert hashlib.sha256(p.read_bytes()).hexdigest() == item['sha256']
    return {'restored_manifest_files': 70, 'new_physics_attempts': 0}


if __name__ == '__main__':
    print(json.dumps(prepare(Path(__file__).resolve().parents[1])))
