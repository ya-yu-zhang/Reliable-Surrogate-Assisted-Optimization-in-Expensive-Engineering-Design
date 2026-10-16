"""Verify selected release files and Python import closure without execution."""
import ast
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'public_release/MANIFEST.json'


def verify():
    data=json.loads(MANIFEST.read_text())
    paths=set(data['files'])
    assert not any(Path(p).suffix.lower() in {'.pdf','.zip','.png','.cls','.bst'} for p in paths)
    assert not any(p.startswith(('output/','tmp/','artifacts/','literature/')) for p in paths)
    imports=[]
    for rel,record in data['files'].items():
        p=ROOT/rel
        assert not Path(rel).is_absolute() and '..' not in Path(rel).parts
        raw=p.read_bytes()
        assert hashlib.sha256(raw).hexdigest()==record['sha256'],rel
        assert record['license'] in {'MIT','CC-BY-4.0','LicenseRef-ScopeNotice'}
        if not rel.startswith('src/') or p.suffix!='.py':continue
        for node in ast.walk(ast.parse(raw.decode())):
            if not isinstance(node,ast.ImportFrom) or not node.level:continue
            if node.module:
                local='src/'+node.module.replace('.','/')+'.py'
                assert local in paths,(rel,local)
                imports.append(local)
            else:
                for item in node.names:
                    local='src/'+item.name+'.py'
                    assert local in paths,(rel,local)
                    imports.append(local)
    return dict(files_checked=len(paths),local_imports_resolved=len(imports),
                physical_evaluations=0,posterior_reconstructions=0,
                numerical_execution=False,public_visibility_changed=False,
                PDF_or_ZIP_created_or_uploaded=False)


if __name__=='__main__':
    print(json.dumps(verify(),indent=2))
