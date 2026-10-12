"""Exact archive of selected grid inputs, stopped/recovery journals and provenance."""
import argparse,base64,json,lzma
from pathlib import Path
from .engineering_optimization_paired_mesh import ROOT,CONFIG,sha
DATA=ROOT/'data/engineering_optimization_paired_mesh_v1'
def pack():
    cfg=json.loads(CONFIG.read_text());original=ROOT/cfg['out'];recovery=ROOT/'results/engineering_optimization_paired_mesh_recovery_v1'
    plan=json.loads((original/'plan.json').read_text());status=json.loads((recovery/'run_status.json').read_text());assert status['complete']
    paths=set(p for folder in [original,recovery] for p in folder.iterdir() if p.is_file())
    paths.update(ROOT/p for p in plan['source_files_sha256'])
    records=[];files=[]
    for p in sorted(paths):
        b=p.read_bytes();name=p.relative_to(ROOT).as_posix();assert p.suffix in ['.json','.jsonl']
        records.append({'path':name,'content':base64.b64encode(b).decode()});files.append({'path':name,'sha256':sha(b),'bytes':len(b)})
    payload=json.dumps(records,separators=(',',':')).encode();compressed=lzma.compress(payload,preset=9);encoded=base64.b85encode(compressed).decode()
    DATA.mkdir(exist_ok=False);parts=[]
    for i,start in enumerate(range(0,len(encoded),96000)):
        name=f'segments-{i:03d}.b85';b=encoded[start:start+96000].encode();(DATA/name).write_bytes(b);parts.append({'path':name,'sha256':sha(b),'bytes':len(b)})
    manifest={'codec':'exact bytes -> base64 JSON -> LZMA -> base85','files':files,'parts':parts,
              'payload_sha256':sha(payload),'compressed_sha256':sha(compressed),'selected_contrasts':14,'selected_states':9,
              'unique_design_points':104,'extra_independent_optimization_samples':0,'original_attempts':4,
              'recovery_execution_new_attempts':status['new_physics_attempts'],'total_new_physics_attempts':status['total_new_physics_attempts'],
              'missing_original_response_value_restored':False,'missing_response_remeasured':1,
              'original_gate_passed':False,'protocol_commit':status['protocol_commit'],'synthetic_labels':0}
    (DATA/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({'files':len(files),'parts':len(parts),'compressed_bytes':len(compressed),'paid_attempts':status['total_new_physics_attempts']}))
def restore(target):
    m=json.loads((DATA/'manifest.json').read_text());chunks=[]
    for part in m['parts']:
        b=(DATA/part['path']).read_bytes();assert sha(b)==part['sha256'];chunks.append(b)
    compressed=base64.b85decode(b''.join(chunks));assert sha(compressed)==m['compressed_sha256'];payload=lzma.decompress(compressed);assert sha(payload)==m['payload_sha256']
    expected={r['path']:r for r in m['files']};seen=set()
    for r in json.loads(payload):
        p=Path(r['path']);assert not p.is_absolute() and '..' not in p.parts and r['path'] in expected and r['path'] not in seen;seen.add(r['path'])
        b=base64.b64decode(r['content']);assert sha(b)==expected[r['path']]['sha256'];out=target/p;out.parent.mkdir(parents=True,exist_ok=True)
        if out.exists() and out.read_bytes()!=b:raise FileExistsError('Conflicting scientific record: '+str(out))
        out.write_bytes(b)
    assert seen==set(expected);print(json.dumps({'restored_files':len(seen),'all_hashes_verified':True,'new_physics_attempts':0}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pack',action='store_true');p.add_argument('--target',type=Path,default=ROOT);a=p.parse_args()
    if a.pack:pack()
    else:restore(a.target)
