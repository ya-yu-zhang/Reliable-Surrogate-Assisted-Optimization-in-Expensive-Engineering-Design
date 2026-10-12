"""Explicit amended continuation of a stopped mesh check; all attempts charged."""
import argparse,json,os,time
from pathlib import Path
import numpy as np
from .engineering_optimization_paired_mesh import ROOT,CONFIG,sha,write,density_field,transfer,normalized_geometry,solve

def prepare():
    cfg=json.loads(CONFIG.read_text());original=ROOT/cfg['out'];out=ROOT/'results/engineering_optimization_paired_mesh_recovery_v1'
    if out.exists():raise FileExistsError('Existing recovery; inspect, never overwrite')
    raw=(original/'events.jsonl').read_bytes();rows=[json.loads(l) for l in raw.splitlines()]
    assert len([r for r in rows if r['event']=='pre'])==4 and len([r for r in rows if r['event']=='label'])==3
    assert rows[-1]['event']=='pre'
    plan=json.loads((original/'plan.json').read_text());files=['src/recover_paired_mesh_records.py','paper/engineering_optimization/PAIRED_MESH_RECOVERY_PLAN.md']
    record={'original_plan_sha256':sha((original/'plan.json').read_bytes()),'original_journal_sha256':sha(raw),
            'original_attempts':4,'completed_original_labels':3,'missing_original_labels':1,
            'config':cfg,'points_and_cases_unchanged':True,'source_agreement_tolerance_unchanged':True,
            'frozen_recovery_files':{p:sha((ROOT/p).read_bytes()) for p in files},'new_physics_attempts':0}
    write(out/'recovery_plan.json',record)
    write(original/'run_status.json',{'complete':False,'stopped':True,'reason':'source_response_agreement_assertion',
          'new_physics_attempts':4,'completed_response_pairs':3,'missing_paid_responses':1,'journal_sha256':sha(raw)})
    print(json.dumps(record))

def run(protocol_commit):
    from engibench.problems.beams2d.v1 import Beams2D
    cfg=json.loads(CONFIG.read_text());original=ROOT/cfg['out'];out=ROOT/'results/engineering_optimization_paired_mesh_recovery_v1'
    frozen=json.loads((out/'recovery_plan.json').read_text());plan=json.loads((original/'plan.json').read_text())
    assert len(protocol_commit)==40 and sha((original/'plan.json').read_bytes())==frozen['original_plan_sha256']
    raw=(original/'events.jsonl').read_bytes();assert sha(raw)==frozen['original_journal_sha256']
    for p,d in {**plan['frozen_files'],**plan['source_files_sha256'],**frozen['frozen_recovery_files']}.items():assert sha((ROOT/p).read_bytes())==d,p
    from engibench.problems.beams2d import backend,v0
    assert sha(Path(backend.__file__).read_bytes())==plan['installed_engine_hashes']['backend.py']
    assert sha(Path(v0.__file__).read_bytes())==plan['installed_engine_hashes']['v0.py']
    cache={};pending=None
    for line in raw.splitlines():
        r=json.loads(line)
        if r['event']=='pre':pending=r
        elif r['event']=='label':
            mesh=pending['context'].split('/')[0];k=mesh+':'+pending['density_sha256']
            cache[k]=(r['y'],{n:r[n] for n in ['equilibrium_relative_residual','work_compliance','relative_energy_work_gap','Emin','Emax','penal']});pending=None
    assert len(cache)==3
    journal=(out/'events.jsonl').open('x');calls=0;requests=0;results={}
    def log(r):journal.write(json.dumps(r,separators=(',',':'),allow_nan=False)+'\n');journal.flush();os.fsync(journal.fileno())
    for nx,ny in cfg['meshes']:
        problem=Beams2D(seed=0,config={'nelx':nx,'nely':ny,'rmin':2*nx/100})
        for mapping in cfg['mappings']:
            context=f'{nx}x{ny}/{mapping}';results[context]={}
            for point,record in sorted(plan['points'].items()):
                base=density_field(np.array(record['x']))
                field=density_field(np.array(record['x']),shape=(ny,nx)) if mapping=='native_parameter_resampling' else transfer(base,(ny,nx))
                assert abs(float(field.mean())-.35)<=cfg['relative_volume_tolerance']
                digest=sha(np.asarray(field,dtype='<f8').tobytes());cache_key=f'{nx}x{ny}:'+digest;requests+=1
                log({'event':'pre','request':requests,'point':point,'context':context,'density_sha256':digest,
                     'volume_fraction':float(field.mean()),'geometry':normalized_geometry(nx,ny)})
                if cache_key in cache:value,checks=cache[cache_key];origin='previous_or_current_exact_mesh_density_cache';elapsed=0.
                else:
                    if calls+frozen['original_attempts']>=cfg['max_new_physics_attempts']:raise RuntimeError('Cumulative frozen cap reached')
                    calls+=1;started=time.perf_counter()
                    try:value,checks=solve(problem,field,nx,ny)
                    except Exception as exc:log({'event':'failure','paid_attempts':calls,'error':repr(exc)});raise
                    elapsed=time.perf_counter()-started;origin='new_physics_attempt';cache[cache_key]=(value,checks)
                relative=abs(value-record['old_y'])/record['old_y']
                coarse=(nx==100)
                flags={**checks,'source_relative_difference':relative if coarse else None,
                       'coarse_source_agreement_flag':coarse and not np.isclose(value,record['old_y'],rtol=cfg['source_prediction_tolerance'],atol=1e-8),
                       'equilibrium_flag':checks['equilibrium_relative_residual']>cfg['equilibrium_residual_flag']}
                log({'event':'label','request':requests,'y':value,'origin':origin,'paid_attempts':calls,'fe_seconds':elapsed,**flags})
                results[context][point]={'y':value,'density_sha256':digest,**flags}
            write(out/'run_status.json',{'complete':False,'new_physics_attempts':calls,'original_attempts':4,'completed_contexts':list(results),'protocol_commit':protocol_commit})
            print(json.dumps({'context':context,'recovery_execution_new_attempts':calls,'cumulative_attempts':calls+4}),flush=True)
    log({'event':'complete','paid_attempts':calls,'cumulative_paid_attempts':calls+4});journal.close()
    write(out/'responses.json',results)
    write(out/'run_status.json',{'complete':True,'new_physics_attempts':calls,'original_attempts':4,
          'total_new_physics_attempts':calls+4,'recovered_missing_labels':1,'original_gate_passed':False,
          'extra_independent_samples':0,'requests':requests,'protocol_commit':protocol_commit,
          'journal_sha256':sha((out/'events.jsonl').read_bytes())})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');p.add_argument('--run',action='store_true');p.add_argument('--protocol-commit');a=p.parse_args()
    if a.prepare:prepare()
    elif a.run:run(a.protocol_commit or '')
    else:p.error('Choose a stage')
