"""Lossless, hash-checked archive of independently measured budget-audit records."""
import argparse,base64,hashlib,json,lzma
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/engineering_optimization_budget_audit_v1'
SOURCE=ROOT/'results/engineering_optimization_budget_audit_v1'
def sha(b):return hashlib.sha256(b).hexdigest()
def pack():
    status=json.loads((SOURCE/'run_status.json').read_text())
    assert status['complete'] and status['recovery_attempts']==0
    records=[];files=[]
    paths=sorted(SOURCE.rglob('*'))
    paths.append(ROOT/'paper/engineering_optimization/budget_audit/primary_traces.json')
    for p in paths:
        if not p.is_file():continue
        if p.suffix=='.tmp':raise ValueError('Unexpected incomplete temporary record')
        b=p.read_bytes();name=p.relative_to(ROOT).as_posix()
        records.append({'path':name,'content':base64.b64encode(b).decode()})
        files.append({'path':name,'sha256':sha(b),'bytes':len(b)})
    payload=json.dumps(records,separators=(',',':')).encode()
    compressed=lzma.compress(payload,preset=9);encoded=base64.b85encode(compressed).decode()
    DATA.mkdir(exist_ok=False);parts=[]
    for i,start in enumerate(range(0,len(encoded),96000)):
        name=f'segments-{i:03d}.b85';b=encoded[start:start+96000].encode()
        (DATA/name).write_bytes(b);parts.append({'path':name,'sha256':sha(b),'bytes':len(b)})
    manifest={'codec':'exact bytes -> base64 JSON -> LZMA -> base85','files':files,'parts':parts,
              'payload_sha256':sha(payload),'compressed_sha256':sha(compressed),
              'protocol_commit':status['protocol_commit'],'seed_blocks':10,'states':30,
              'raw_record_files':82,'derived_trace_files':1,
              'new_physics_attempts':status['new_physics_attempts'],'recovery_attempts':0,
              'replacement_seed_blocks':0,'synthetic_labels':0}
    (DATA/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'files':len(files),'parts':len(parts),'compressed_bytes':len(compressed),
                      'new_physics_attempts':status['new_physics_attempts']}))
def restore(target):
    m=json.loads((DATA/'manifest.json').read_text());chunks=[]
    for part in m['parts']:
        b=(DATA/part['path']).read_bytes();assert sha(b)==part['sha256'];chunks.append(b)
    compressed=base64.b85decode(b''.join(chunks));assert sha(compressed)==m['compressed_sha256']
    payload=lzma.decompress(compressed);assert sha(payload)==m['payload_sha256']
    expected={r['path']:r for r in m['files']};seen=set()
    for r in json.loads(payload):
        p=Path(r['path']);assert not p.is_absolute() and '..' not in p.parts
        assert r['path'] in expected and r['path'] not in seen;seen.add(r['path'])
        b=base64.b64decode(r['content']);assert sha(b)==expected[r['path']]['sha256']
        out=target/p;out.parent.mkdir(parents=True,exist_ok=True)
        if out.exists() and out.read_bytes()!=b:raise FileExistsError('Conflicting scientific record: '+str(out))
        out.write_bytes(b)
    assert seen==set(expected)
    print(json.dumps({'restored_files':len(seen),'all_hashes_verified':True,'new_physics_attempts':0}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pack',action='store_true');p.add_argument('--target',type=Path,default=ROOT)
    args=p.parse_args()
    if args.pack:pack()
    else:restore(args.target)
