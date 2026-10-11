"""Exact JSONL bytes via Sobol point regeneration and gzip/base85 packaging."""
import argparse,base64,gzip,hashlib,json
from pathlib import Path
import numpy as np
from scipy.stats import qmc
from .engineering_optimization_thermal import random_seed
from .engineering_optimization_transfer import write_json
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/engineering_optimization_thermal_v1'
def sha(b): return hashlib.sha256(b).hexdigest()

def restore_records(records,cfg):
    meta=records[0]; c=cfg['conditions'].index(meta['condition']); r=meta['repeat']
    initial=qmc.Sobol(12,scramble=True,seed=random_seed(cfg,c,r,1)).random_base2(5)[:cfg['initial']]
    histories={}; selection=None; pending=None
    for row in records:
        if row['event']=='selection': selection=row
        elif row['event']=='pre':
            if row['phase']=='initial': x=initial[row['step']]; key=None
            else:
                key=(row['workflow'],row['policy'])
                if key not in histories:
                    if row['workflow'] in ['audit_gate','simple_selector']:
                        histories[key]=list(histories['shared',row['policy']])
                    else: histories[key]=list(initial.copy())
                namespace=2 if row['phase']=='pilot' else 3
                pool=qmc.Sobol(12,scramble=True,seed=random_seed(cfg,c,r,namespace,row['step'])).random_base2(cfg['pool_power'])
                observed={x.tobytes() for x in histories[key]}
                pool=np.asarray([x for x in pool if x.tobytes() not in observed])
                x=pool[row['pool_index']]
                assert len(histories[key])==row['observations_before']
            row['x']=x.tolist(); pending=(row,key,x)
        elif row['event']=='label':
            pre,key,x=pending; assert pre['call_id']==row['call_id']
            if key is not None: histories[key].append(x)
            pending=None
    return (''.join(json.dumps(v,separators=(',',':'))+'\n' for v in records)).encode()

def pack():
    cfg=json.loads((ROOT/'configs/engineering_optimization_thermal.json').read_text()); source=ROOT/cfg['out']
    archive={'config':cfg,'cases':[],'extra':[]}; files=[]
    for folder in sorted(source.glob('condition*_r*')):
        raw=(folder/'events.jsonl').read_bytes(); records=[json.loads(v) for v in raw.splitlines()]
        for row in records:
            if row['event']=='pre': row['x']=None
        restored=restore_records(json.loads(json.dumps(records)),cfg); assert restored==raw
        summary=(folder/'summary.json').read_bytes()
        assert json.loads(summary)['journal_sha256']==sha(raw)
        archive['cases'].append({'case':folder.name,'records':records,'summary':base64.b64encode(summary).decode()})
        files.extend([{'path':str(folder.relative_to(ROOT)/'events.jsonl'),'sha256':sha(raw)},
                      {'path':str(folder.relative_to(ROOT)/'summary.json'),'sha256':sha(summary)}])
    extras=[source/'run_status.json',ROOT/'paper/engineering_optimization/thermal_record_recovery.json']
    extras+=sorted((ROOT/'results/engineering_optimization_thermal_record_recovery').glob('original*/*'))
    for p in extras:
        raw=p.read_bytes(); path=str(p.relative_to(ROOT)); archive['extra'].append({'path':path,'content':base64.b64encode(raw).decode()}); files.append({'path':path,'sha256':sha(raw)})
    payload=json.dumps(archive,separators=(',',':')).encode(); packed=gzip.compress(payload,compresslevel=9,mtime=0); text=base64.b85encode(packed).decode()
    DATA.mkdir(parents=True,exist_ok=False); parts=[]
    for i,start in enumerate(range(0,len(text),96000)):
        name=f'segments-{i:03d}.b85'; b=text[start:start+96000].encode(); (DATA/name).write_bytes(b); parts.append({'path':name,'sha256':sha(b)})
    manifest={'codec':'exact JSONL via Sobol regeneration; gzip+base85','parts':parts,'files':files,
              'packed_sha256':sha(packed),'payload_sha256':sha(payload),'independent_cases':20,
              'retained_optimization_attempts':7200,'current_verification_attempts':22,
              'additional_record_recovery_attempts':1080,'previous_lost_session_attempts':7586,
              'cumulative_thermal_attempts':15888}
    write_json(DATA/'manifest.json',manifest)
    return {'parts':len(parts),'packed_bytes':len(packed),'exact_byte_reconstruction_cases':20,'files':len(files)}

def restore(target):
    manifest=json.loads((DATA/'manifest.json').read_text()); chunks=[]
    for part in manifest['parts']:
        b=(DATA/part['path']).read_bytes(); assert sha(b)==part['sha256']; chunks.append(b)
    packed=base64.b85decode(b''.join(chunks)); assert sha(packed)==manifest['packed_sha256']
    payload=gzip.decompress(packed); assert sha(payload)==manifest['payload_sha256']; archive=json.loads(payload)
    expected={v['path']:v['sha256'] for v in manifest['files']}; written=[]
    def write(path,b):
        p=Path(path)
        if p.is_absolute() or '..' in p.parts: raise ValueError('Unsafe archived path')
        assert sha(b)==expected[path]; dest=target/p; dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists() and dest.read_bytes()!=b: raise FileExistsError('Conflicting scientific record: '+str(dest))
        dest.write_bytes(b); written.append(path)
    for case in archive['cases']:
        folder=Path(archive['config']['out'])/case['case']
        write(str(folder/'events.jsonl'),restore_records(case['records'],archive['config']))
        write(str(folder/'summary.json'),base64.b64decode(case['summary']))
    for record in archive['extra']: write(record['path'],base64.b64decode(record['content']))
    assert len(written)==len(expected)
    return {'restored_files':len(written),'all_file_hashes_verified':True,'new_solver_calls':0}
if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--pack',action='store_true'); parser.add_argument('--target',type=Path,default=ROOT); args=parser.parse_args()
    print(json.dumps(pack() if args.pack else restore(args.target)))
