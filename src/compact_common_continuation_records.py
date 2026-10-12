"""Lossless byte archive for common-continuation plans and measured records."""
import argparse,base64,hashlib,json,lzma
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/engineering_optimization_common_continuation_v1'
def sha(b): return hashlib.sha256(b).hexdigest()
def pack():
    paths=sorted(p for p in (ROOT/'results/engineering_optimization_common_continuation_v1').rglob('*') if p.is_file())
    archive=ROOT/'results/engineering_optimization_common_continuation_recovery'
    paths+=[archive/'events.jsonl',archive/'run_status.json']+sorted((archive/'summaries').glob('*.json'))
    records=[];files=[]
    for p in paths:
        b=p.read_bytes();name=str(p.relative_to(ROOT));records.append({'path':name,'content':base64.b64encode(b).decode()});files.append({'path':name,'sha256':sha(b),'bytes':len(b)})
    payload=json.dumps(records,separators=(',',':')).encode();compressed=lzma.compress(payload,preset=9);text=base64.b85encode(compressed).decode();DATA.mkdir(parents=True,exist_ok=False);parts=[]
    for i,start in enumerate(range(0,len(text),96000)):
        name=f'segments-{i:03d}.b85';b=text[start:start+96000].encode();(DATA/name).write_bytes(b);parts.append({'path':name,'sha256':sha(b)})
    manifest={'codec':'exact file bytes -> base64 JSON -> LZMA -> base85','files':files,'parts':parts,'compressed_sha256':sha(compressed),'payload_sha256':sha(payload),'learned_states':30,'seed_blocks':10,'original_new_fe_attempts':273,'recovery_fe_attempts':9,'total_new_fe_attempts':282,'extra_samples_from_replay':0}
    (DATA/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({'files':len(files),'parts':len(parts),'compressed_bytes':len(compressed)}))
def restore(target):
    m=json.loads((DATA/'manifest.json').read_text());chunks=[]
    for part in m['parts']:
        b=(DATA/part['path']).read_bytes();assert sha(b)==part['sha256'];chunks.append(b)
    compressed=base64.b85decode(b''.join(chunks));assert sha(compressed)==m['compressed_sha256'];payload=lzma.decompress(compressed);assert sha(payload)==m['payload_sha256'];expected={v['path']:v for v in m['files']}
    for r in json.loads(payload):
        p=Path(r['path']);assert not p.is_absolute() and '..' not in p.parts;b=base64.b64decode(r['content']);assert sha(b)==expected[r['path']]['sha256'];out=target/p;out.parent.mkdir(parents=True,exist_ok=True)
        if out.exists() and out.read_bytes()!=b: raise FileExistsError('Conflicting scientific record: '+str(out))
        out.write_bytes(b)
    print(json.dumps({'restored_files':len(expected),'all_hashes_verified':True,'new_solver_calls':0}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pack',action='store_true');p.add_argument('--target',type=Path,default=ROOT);a=p.parse_args()
    if a.pack:pack()
    else:restore(a.target)
