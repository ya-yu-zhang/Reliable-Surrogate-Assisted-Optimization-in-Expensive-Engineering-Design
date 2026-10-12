"""Prospective fixed-design/retained-pool mesh check on published audit cases."""
from __future__ import annotations
import argparse,csv,hashlib,importlib.metadata,json,os,time
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from .engineering_beam_adapter import density_field
from .engineering_optimization_common_continuation import effect_label
ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/'configs/engineering_optimization_paired_mesh.json'
def sha(b):return hashlib.sha256(b).hexdigest()
def point_key(x):return sha(np.asarray(x,dtype='<f8').tobytes())
def write(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix(p.suffix+'.tmp')
    with tmp.open('w') as f:f.write(json.dumps(v,indent=2,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
    tmp.replace(p)
def overlap_weights(target,source):
    """Exact cell-average transfer on the same normalized one-dimensional domain."""
    a=np.arange(target)[:,None]/target;b=np.arange(source)[None,:]/source
    return np.maximum(0.,np.minimum(a+1/target,b+1/source)-np.maximum(a,b))*target
def transfer(base,shape):
    if base.shape==tuple(shape):return base.copy()
    result=overlap_weights(shape[0],base.shape[0])@base@overlap_weights(shape[1],base.shape[1]).T
    if not np.isclose(result.mean(),base.mean(),rtol=0,atol=1e-12):raise AssertionError('Lost material volume')
    return result
def normalized_geometry(nx,ny):
    return {'aspect_ratio':nx/ny,'force_position':[0.,0.],'total_vertical_force':-1.,
            'horizontal_support':'left_boundary_all_nodes','vertical_support_position':[1.,1.],
            'horizontal_constraints':ny+1,'vertical_constraints':1}

def prepare():
    cfg=json.loads(CONFIG.read_text());out=ROOT/cfg['out']
    if out.exists():raise FileExistsError('Existing frozen mesh release; no overwrite')
    old=ROOT/'results/engineering_optimization_common_continuation_v1'
    om=json.loads((old/'manifest.json').read_text());plans={}
    for item in om['plans']:
        raw=(old/item['path']).read_bytes();assert sha(raw)==item['sha256'];plans[item['state']]=json.loads(raw)
    events=defaultdict(dict);pending=None
    for line in (old/'events.jsonl').read_text().splitlines():
        r=json.loads(line)
        if r['event']=='pre':assert pending is None;pending=r
        elif r['event']=='label':
            assert pending and (r['state'],r['branch'],r['step'])==(pending['state'],pending['branch'],pending['step'])
            events[r['state']][r['branch'],r['step']]={'x':pending['x'],'y':r['y']};pending=None
    assert pending is None
    old_rows=list(csv.DictReader((ROOT/'paper/engineering_optimization/common_continuation/distinct_action_contrasts.csv').open()))
    changed=[r for r in old_rows if r['classification_changed']=='True']
    unchanged=sorted([r for r in old_rows if r['classification_changed']=='False' and r['h5_effect']=='tie'],key=lambda r:(r['state'],r['control']))[:cfg['unchanged_different_action_controls']]
    aliases=[];seen=set()
    full_rows=list(csv.DictReader((ROOT/'paper/engineering_optimization/common_continuation/diagnostic_classifications.csv').open()))
    for r in sorted(full_rows,key=lambda r:(r['state'],r['control'])):
        if r['first_action_changed']=='False' and r['state'] not in seen:
            aliases.append(r);seen.add(r['state'])
            if len(aliases)==cfg['structural_alias_controls']:break
    new_rows=list(csv.DictReader((ROOT/'paper/engineering_optimization/budget_audit/classifications.csv').open()))
    new_errors=[r for r in new_rows if r['method']=='immediate' and r['classification_error']=='True' and r['unique_nonbaseline_contrast']=='True']
    assert len(changed)==7 and len(new_errors)==1
    points={};cases=[];sources={}
    def register(x,value):
        k=point_key(x)
        if k in points:assert np.isclose(points[k]['old_y'],value,rtol=1e-8,atol=1e-8)
        else:points[k]={'x':list(x),'old_y':float(value)}
        return k
    for source,rows,group in [('common_continuation',changed,'changed'),('budget_audit',new_errors,'independent_proxy_mismatch'),('common_continuation',unchanged,'unchanged_different_action'),('common_continuation',aliases,'structural_alias')]:
        for r in rows:
            state=r['state'];control=r['control'];continuation='mean' if source=='common_continuation' else r['continuation']
            if source=='common_continuation':
                p=plans[state];X,y=np.array(p['X']),np.array(p['y']);initial_index=int(np.argmin(y))
                records={name:[events[state][str(p['decisions'][name]),h] for h in range(6)] for name in ['mean',control]}
                paths=[old/'plans'/(state+'.json'),old/'summaries'/(state+'.json'),old/'events.jsonl']
            else:
                path=ROOT/f"results/engineering_optimization_budget_audit_v1/block_{r['block']}/{state}_summary.json"
                p=json.loads(path.read_text());X,y=np.array(p['X']),np.array(p['y']);initial_index=int(np.argmin(y))
                records={name:p['trajectories'][continuation][p['mapping'][name]] for name in ['mean',control]};paths=[path]
            initial=register(X[initial_index],y[initial_index]);branches={};endpoints={}
            for name,rr in records.items():
                ids=[initial]+[register(v['x'],v['y']) for v in rr];values=[float(y[initial_index])]+[v['y'] for v in rr]
                branches[name]=ids
                endpoints[name]={str(h):ids[int(np.argmin(values[:h+2]))] for h in [0,5]}
            delta={str(h):(points[endpoints['mean'][str(h)]]['old_y']-points[endpoints[control][str(h)]]['old_y'])/float(y[initial_index]) for h in [0,5]}
            cases.append({'case':f'S{len(cases)+1:02d}','group':group,'source':source,'state':state,
                          'control':control,'continuation':continuation,'initial_point':initial,
                          'branches':branches,'fixed_endpoints':endpoints,'old_effects':delta,
                          'relative_margin':cfg['source_relative_margins'][source]})
            for path in paths:sources[str(path.relative_to(ROOT))]=sha(path.read_bytes())
    assert len(cases)==14
    from engibench.problems.beams2d import backend,v0
    frozen=['src/engineering_optimization_paired_mesh.py','src/engineering_beam_adapter.py',
            'src/engineering_optimization_common_continuation.py','configs/engineering_optimization_paired_mesh.json',
            'paper/engineering_optimization/PAIRED_MESH_PROTOCOL.md']
    plan={'config':cfg,'cases':cases,'points':points,'source_files_sha256':sources,
          'frozen_files':{p:sha((ROOT/p).read_bytes()) for p in frozen},
          'installed_engine_hashes':{'backend.py':sha(Path(backend.__file__).read_bytes()),'v0.py':sha(Path(v0.__file__).read_bytes())},
          'versions':{p:importlib.metadata.version(p) for p in ['numpy','scipy','scikit-learn','engibench','cvxopt']},
          'new_physics_attempts':0,'future_mesh_labels_read':False}
    write(out/'plan.json',plan)
    print(json.dumps({'cases':len(cases),'unique_design_points':len(points),'selected_states':len({c['state'] for c in cases}),'new_physics_attempts':0}))

def solve(problem,field,nx,ny):
    value=float(problem.simulate(field)[0]);st=problem._Beams2D__st
    assert np.isfinite(value) and value>0 and st.ndof==2*(nx+1)*(ny+1)
    assert np.array_equal(st.fixed,np.union1d(np.arange(0,2*(ny+1),2),[st.ndof-1]))
    assert np.flatnonzero(st.f.ravel()).tolist()==[1] and float(st.f.sum())==-1.
    material=st.Emin+field.T.reshape(-1)**3*(st.Emax-st.Emin)
    sK=(st.KE.flatten()[:,None]*material[None,:]).flatten(order='F')
    K=coo_matrix((sK,(st.iK,st.jK)),shape=(st.ndof,st.ndof)).tocsc()
    residual=K[st.free,:][:,st.free]@st.u[st.free,0]-st.f[st.free,0]
    relative=float(np.linalg.norm(residual)/np.linalg.norm(st.f[st.free,0]))
    work=float(st.f.ravel()@st.u.ravel())
    return value,{'equilibrium_relative_residual':relative,'work_compliance':work,
                  'relative_energy_work_gap':abs(work-value)/value,
                  'Emin':st.Emin,'Emax':st.Emax,'penal':3.}

def run(protocol_commit):
    from engibench.problems.beams2d.v1 import Beams2D
    cfg=json.loads(CONFIG.read_text());out=ROOT/cfg['out'];plan=json.loads((out/'plan.json').read_text())
    for p,d in {**plan['source_files_sha256'],**plan['frozen_files']}.items():assert sha((ROOT/p).read_bytes())==d,p
    from engibench.problems.beams2d import backend,v0
    assert sha(Path(backend.__file__).read_bytes())==plan['installed_engine_hashes']['backend.py']
    assert sha(Path(v0.__file__).read_bytes())==plan['installed_engine_hashes']['v0.py']
    assert len(protocol_commit)==40
    cache={};results={};calls=0;requests=0;journal=(out/'events.jsonl').open('x')
    def log(row):journal.write(json.dumps(row,separators=(',',':'),allow_nan=False)+'\n');journal.flush();os.fsync(journal.fileno())
    for nx,ny in cfg['meshes']:
        problem=Beams2D(seed=0,config={'nelx':nx,'nely':ny,'rmin':2*nx/100})
        for mapping in cfg['mappings']:
            context=f'{nx}x{ny}/{mapping}';results[context]={}
            for point,record in sorted(plan['points'].items()):
                x=np.array(record['x']);base=density_field(x)
                field=density_field(x,shape=(ny,nx)) if mapping=='native_parameter_resampling' else transfer(base,(ny,nx))
                assert field.shape==(ny,nx) and abs(float(field.mean())-.35)<=cfg['relative_volume_tolerance']
                digest=sha(np.asarray(field,dtype='<f8').tobytes());cache_key=f'{nx}x{ny}:'+digest;requests+=1
                log({'event':'pre','request':requests,'point':point,'context':context,
                     'density_sha256':digest,'volume_fraction':float(field.mean()),'geometry':normalized_geometry(nx,ny)})
                if cache_key in cache:
                    value,checks=cache[cache_key];elapsed=0.;origin='exact_mesh_and_density_cache'
                else:
                    if calls>=cfg['max_new_physics_attempts']:raise RuntimeError('Frozen paid-attempt cap reached')
                    calls+=1;started=time.perf_counter()
                    try:value,checks=solve(problem,field,nx,ny)
                    except Exception as exc:log({'event':'failure','paid_attempts':calls,'error':repr(exc)});raise
                    elapsed=time.perf_counter()-started;origin='new_physics_attempt';cache[cache_key]=(value,checks)
                if nx==100 and mapping=='native_parameter_resampling':assert np.isclose(value,record['old_y'],rtol=cfg['source_prediction_tolerance'],atol=1e-8)
                checks={**checks,'equilibrium_flag':checks['equilibrium_relative_residual']>cfg['equilibrium_residual_flag']}
                results[context][point]={'y':value,'density_sha256':digest,**checks}
                log({'event':'label','request':requests,'y':value,'origin':origin,'paid_attempts':calls,'fe_seconds':elapsed,**checks})
            write(out/'run_status.json',{'complete':False,'completed_contexts':list(results),'new_physics_attempts':calls,'requests':requests,'protocol_commit':protocol_commit})
            print(json.dumps({'context':context,'paid_attempts':calls,'requests':requests}),flush=True)
    log({'event':'complete','paid_attempts':calls,'requests':requests});journal.close()
    write(out/'responses.json',results)
    write(out/'run_status.json',{'complete':True,'completed_contexts':list(results),'new_physics_attempts':calls,'requests':requests,'protocol_commit':protocol_commit,'recovery_attempts':0,'journal_sha256':sha((out/'events.jsonl').read_bytes())})

def analyze():
    cfg=json.loads(CONFIG.read_text());out=ROOT/cfg['out'];plan=json.loads((out/'plan.json').read_text());responses=json.loads((out/'responses.json').read_text());status=json.loads((out/'run_status.json').read_text())
    assert status['complete'] and sha((out/'events.jsonl').read_bytes())==status['journal_sha256']
    rows=[]
    for c in plan['cases']:
        for context,values in responses.items():
            initial=values[c['initial_point']]['y']
            for h in [0,5]:
                for target in ['fixed_endpoint','retained_pool']:
                    if target=='fixed_endpoint':ids={n:c['fixed_endpoints'][n][str(h)] for n in ['mean',c['control']]}
                    else:ids={n:min(c['branches'][n][:h+2],key=lambda p:values[p]['y']) for n in ['mean',c['control']]}
                    mean=values[ids['mean']]['y'];alt=values[ids[c['control']]]['y'];effect=(mean-alt)/initial
                    old=effect_label(c['old_effects'][str(h)],c['relative_margin']);label=effect_label(effect,c['relative_margin'])
                    rows.append({'case':c['case'],'group':c['group'],'state':c['state'],'control':c['control'],'context':context,'horizon':h,'target':target,
                                 'initial_compliance':initial,'mean_design_compliance':mean,'alternative_design_compliance':alt,
                                 'relative_advantage_percent':100*effect,'original_effect':old,'effect':label,'classification_changed':label!=old,
                                 'mean_point':ids['mean'],'alternative_point':ids[c['control']]})
    summary=[]
    for c in plan['cases']:
        fixed=[r for r in rows if r['case']==c['case'] and r['target']=='fixed_endpoint' and r['horizon']==5]
        pool=[r for r in rows if r['case']==c['case'] and r['target']=='retained_pool' and r['horizon']==5]
        summary.append({'case':c['case'],'group':c['group'],'state':c['state'],'control':c['control'],
                        'original_h5_class':fixed[0]['original_effect'],
                        'fixed_h5_all_contexts_stable':all(not r['classification_changed'] for r in fixed),
                        'fixed_h5_class_changes':sum(r['classification_changed'] for r in fixed),
                        'retained_pool_h5_class_changes':sum(r['classification_changed'] for r in pool)})
    dest=ROOT/'paper/engineering_optimization/paired_mesh';dest.mkdir(parents=True,exist_ok=True)
    with (dest/'paired_contrasts.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
    with (dest/'case_summary.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(summary[0]),lineterminator='\n');writer.writeheader();writer.writerows(summary)
    all_values=[v for context in responses.values() for v in context.values()]
    report={'complete':True,'selected_contrasts':len(plan['cases']),'selected_states':len({c['state'] for c in plan['cases']}),'unique_design_points':len(plan['points']),
            'new_physics_attempts':status['new_physics_attempts'],'requests':status['requests'],'recovery_attempts':0,
            'protocol_commit':status['protocol_commit'],'fixed_h5_stable_cases':sum(r['fixed_h5_all_contexts_stable'] for r in summary),
            'case_summaries':summary,'max_equilibrium_relative_residual':max(v['equilibrium_relative_residual'] for v in all_values),
            'max_energy_work_gap':max(v['relative_energy_work_gap'] for v in all_values),'equilibrium_flags':sum(v['equilibrium_flag'] for v in all_values),
            'extra_independent_optimization_samples':0,'fine_grid_gp_rerun':False,'all_original_training_points_refined':False,
            'mesh_convergence_certified':False,'engineering_margin_certified':False}
    write(dest/'analysis.json',report);print(json.dumps(report))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');p.add_argument('--run',action='store_true');p.add_argument('--analyze',action='store_true');p.add_argument('--protocol-commit');args=p.parse_args()
    if args.prepare:prepare()
    elif args.run:run(args.protocol_commit or '')
    elif args.analyze:analyze()
    else:p.error('Choose a stage')
