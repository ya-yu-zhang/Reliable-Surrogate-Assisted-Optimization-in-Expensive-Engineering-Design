"""Independent seed-block collection for frozen budgeted-audit replay.

Raw simulations, not generated/synthetic outcomes. Historical data are never
read. Each block is journalled and fsynced; failures stop without replacement.
"""
from __future__ import annotations
import argparse,hashlib,importlib.metadata,json,os,time,warnings
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from scipy.stats import qmc
from .engineering_optimization_common_continuation import model
from .engineering_optimization_gp_audit import scores

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/'configs/engineering_optimization_budget_audit.json'

def sha(data):return hashlib.sha256(data).hexdigest()
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    # Atomic durable replacement; a completed record is never a partial JSON.
    tmp=path.with_suffix(path.suffix+'.tmp')
    with tmp.open('w') as f:
        f.write(json.dumps(value,indent=2,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
    tmp.replace(path)
def key(x):return np.asarray(x,dtype='<f8').tobytes().hex()
def seed(cfg,*namespace):
    return int(np.random.SeedSequence([cfg['master_seed'],*namespace]).generate_state(1)[0])
def pool(cfg,block,source,phase,step=0):
    return qmc.Sobol(19,scramble=True,seed=seed(cfg,block,source,phase,step)).random_base2(cfg['pool_power'])
def select(gp,X,y,candidates,control,cfg):
    observed={key(x) for x in X}
    candidates=np.array([x for x in candidates if key(x) not in observed])
    mu,sd=gp.predict(candidates,return_std=True)
    values=scores(mu,sd,float(np.min(y)),max(float(np.std(y)),1e-12),cfg)
    index=int(np.argmax(values[control]))
    return candidates[index],{'pool_index':index,'pool_sha256':sha(candidates.tobytes()),
                              'mu':float(mu[index]),'sd':float(sd[index]),
                              'training_count':len(y),'control':control}
def fit_theta(X,y,cfg):
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import ConstantKernel,Matern
    def optimizer(fun,theta,bounds):
        result=minimize(fun,theta,method='L-BFGS-B',jac=True,bounds=bounds,
                        options={'maxiter':cfg['kernel_fit_maxiter']})
        return result.x,result.fun
    kernel=ConstantKernel(1.,(.05,20))*Matern(np.full(19,.2),(.005,2.),nu=2.5)
    with warnings.catch_warnings(record=True) as ws:
        warnings.simplefilter('always')
        gp=GaussianProcessRegressor(kernel=kernel,alpha=cfg['alpha'],normalize_y=True,
                                    optimizer=optimizer,n_restarts_optimizer=0).fit(X,y)
    return gp.kernel_.theta.tolist(),[str(w.message) for w in ws]

def prepare():
    cfg=json.loads(CONFIG.read_text());out=ROOT/cfg['out']
    if out.exists():raise FileExistsError('Existing frozen experiment; inspect, never overwrite')
    sources=['src/engineering_optimization_budget_audit.py','src/budgeted_decision_audit.py',
             'src/analyze_budget_audit.py','configs/engineering_optimization_budget_audit.json',
             'paper/engineering_optimization/BUDGET_AUDIT_PROTOCOL.md',
             'src/engineering_optimization_common_continuation.py','src/engineering_optimization_gp_audit.py',
             'src/engineering_beam_adapter.py']
    manifest={'version':1,'config':cfg,'frozen_files':{p:sha((ROOT/p).read_bytes()) for p in sources},
              'versions':{p:importlib.metadata.version(p) for p in ['numpy','scipy','scikit-learn','engibench','cvxopt']},
              'historical_labels_used':False,'holdout_labels_acquired':False,
              'validation_mode':'preregistered sequential replay of independently collected oracle trajectories'}
    write(out/'manifest.json',manifest)
    print(json.dumps({'prepared':True,'new_physics_attempts':0,'seed_blocks':cfg['seed_blocks']}))

class Ledger:
    def __init__(self,path,cfg,previous):
        from .engineering_beam_adapter import make_problem
        self.problem=make_problem();self.fine=None;self.cfg=cfg;self.previous=previous
        self.calls=0;self.lookups=0;self.cache={};self.pending=None
        self.handle=path.open('x')
    def log(self,row):
        self.handle.write(json.dumps(row,separators=(',',':'),allow_nan=False)+'\n')
        self.handle.flush();os.fsync(self.handle.fileno())
    def evaluate(self,x,metadata,context='default100x50',force=False):
        x=np.asarray(x,dtype=float);cache_key=context+':'+key(x);self.lookups+=1
        self.log({'event':'pre','request':self.lookups,'context':context,'x':x.tolist(),**metadata})
        if cache_key in self.cache and not force:
            value=self.cache[cache_key];elapsed=0.;origin='exact_paid_response_cache'
        else:
            if self.previous+self.calls>=self.cfg['max_physics_attempts']:
                self.log({'event':'budget_stop','paid_attempts':self.calls});raise RuntimeError('Frozen cap reached')
            self.calls+=1;started=time.perf_counter()
            try:
                if context=='default100x50':value=float(self.problem(x))
                elif context=='fine200x100':
                    from engibench.problems.beams2d.v1 import Beams2D
                    from .engineering_beam_adapter import density_field
                    if self.fine is None:self.fine=Beams2D(seed=0,config={'nelx':200,'nely':100,'rmin':4.})
                    value=float(self.fine.simulate(density_field(x,shape=(100,200)))[0])
                else:raise ValueError('Unknown objective context')
                if not np.isfinite(value) or value<=0:raise FloatingPointError('Invalid compliance')
            except Exception as exc:
                self.log({'event':'failure','paid_attempts':self.calls,'error':repr(exc)});raise
            elapsed=time.perf_counter()-started;origin='new_physics_attempt';self.cache[cache_key]=value
        self.log({'event':'label','request':self.lookups,'y':value,'origin':origin,
                  'fe_seconds':elapsed,'paid_attempts':self.calls})
        return value,cache_key
    def close(self):self.handle.close()

def collect_block(cfg,block,out,previous):
    folder=out/f'block_{block}';folder.mkdir(exist_ok=False)
    ledger=Ledger(folder/'events.jsonl',cfg,previous);states=[]
    warm_X=qmc.Sobol(19,scramble=True,seed=seed(cfg,block,0,1)).random_base2(6)[:cfg['warm_start']]
    warm_y=np.array([ledger.evaluate(x,{'phase':'warm','block':block,'step':i})[0] for i,x in enumerate(warm_X)])
    theta,fit_warnings=fit_theta(warm_X,warm_y,cfg)
    ledger.log({'event':'warm_complete','block':block,'theta':theta,'kernel_fit_warnings':fit_warnings})
    mesh=[]
    if block==cfg['seed_blocks'][0]:
        for i,x in enumerate(warm_X[:cfg['mesh_check_points']]):
            base=float(warm_y[i]);repeat,_=ledger.evaluate(x,{'phase':'numerical_repeat','point':i},force=True)
            fine,_=ledger.evaluate(x,{'phase':'mesh_sensitivity','point':i},context='fine200x100')
            mesh.append({'point':i,'x':x.tolist(),'base_compliance':base,'repeat_compliance':repeat,
                         'fine_compliance':fine,'repeat_relative_difference':abs(repeat-base)/base,
                         'mesh_relative_difference':abs(fine-base)/base})
    for source_index,source in enumerate(cfg['source_controls']):
        X,y=warm_X.copy(),warm_y.copy()
        for step in range(cfg['training_count']-cfg['warm_start']):
            gp=model(X,y,theta,cfg)
            # Shared external pools between sources; histories can still differ.
            x,meta=select(gp,X,y,pool(cfg,block,0,2,step),source,cfg)
            value,_=ledger.evaluate(x,{'phase':'source','block':block,'source':source,'step':step,**meta})
            X=np.vstack((X,x));y=np.append(y,value)
        name=f'beam_holdout_r{block}_{source}';root_gp=model(X,y,theta,cfg)
        candidates=pool(cfg,block,source_index,3);mu,sd=root_gp.predict(candidates,return_std=True)
        acquisition=scores(mu,sd,float(y.min()),max(float(y.std()),1e-12),cfg)
        decisions={control:int(np.argmax(acquisition[control])) for control in cfg['first_controls']}
        by_point={};classes={};actions={};mapping={};root_sd={};root_ei={}
        for control,index in decisions.items():
            point_key=key(candidates[index])
            if point_key not in by_point:
                branch=f'b{len(by_point)}';by_point[point_key]=branch
                actions[branch]=candidates[index].tolist();classes[branch]=[]
                root_sd[branch]=float(sd[index]);root_ei[branch]=float(acquisition['ei'][index]/y.min())
            branch=by_point[point_key];classes[branch].append(control);mapping[control]=branch
        state={'state':name,'block':block,'source':source,'X':X.tolist(),'y':y.tolist(),
               'theta':theta,'initial_best':float(y.min()),'classes':classes,'actions':actions,
               'mapping':mapping,'root_sd':root_sd,'root_ei':root_ei,
               'root_pool_sha256':sha(candidates.tobytes()),'root_decisions':decisions,
               'root_selected_predictions':{b:{'mu':float(mu[decisions[names[0]]]),
                                                 'sd':root_sd[b]} for b,names in classes.items()}}
        write(folder/(name+'_plan.json'),state)
        ledger.log({'event':'state_frozen','state':name,'plan_sha256':sha((folder/(name+'_plan.json')).read_bytes()),
                    'no_first_action_or_probe_labels_read':True,'classes':classes})
        probes=pool(cfg,block,source_index,4)[:cfg['calibration_points']]
        pm,ps=root_gp.predict(probes,return_std=True)
        probe_y=[]
        for i,x in enumerate(probes):
            value,_=ledger.evaluate(x,{'phase':'calibration','state':name,'step':i,
                                      'mu':float(pm[i]),'sd':float(ps[i]),'training_count':len(y)})
            probe_y.append(value)
        probe_y=np.array(probe_y)
        calibration={'nrmse':float(np.sqrt(np.mean((probe_y-pm)**2))/max(float(y.std()),1e-12)),
                     'coverage90':float(np.mean(np.abs(probe_y-pm)<=1.6448536269514722*ps)),
                     'points':probes.tolist(),'labels':probe_y.tolist(),'mu':pm.tolist(),'sd':ps.tolist(),
                     'used_for_training':False}
        trajectories={}
        for continuation in cfg['continuations']:
            trajectories[continuation]={}
            for branch,action in actions.items():
                bx,by=X.copy(),y.copy();records=[];x=np.array(action)
                for step in range(cfg['horizon']+1):
                    started=time.perf_counter();gp=model(bx,by,theta,cfg)
                    if step:
                        x,meta=select(gp,bx,by,pool(cfg,block,source_index,5,step),continuation,cfg)
                    else:
                        mm,ss=gp.predict(x[None],return_std=True)
                        meta={'mu':float(mm[0]),'sd':float(ss[0]),'training_count':len(by),
                              'control':'frozen_first_action'}
                    meta['gp_seconds']=time.perf_counter()-started
                    value,point_key=ledger.evaluate(x,{'phase':'oracle','state':name,
                               'continuation':continuation,'branch':branch,'step':step,**meta})
                    bx=np.vstack((bx,x));by=np.append(by,value)
                    records.append({'step':step,'x':x.tolist(),'y':value,'incumbent':float(by.min()),
                                    'point_key':point_key,**meta})
                trajectories[continuation][branch]=records
        summary={**state,'calibration':calibration,'trajectories':trajectories,'complete':True}
        write(folder/(name+'_summary.json'),summary);states.append(name)
        ledger.log({'event':'state_complete','state':name,'paid_attempts':ledger.calls})
        print(json.dumps({'block':block,'source':source,'states_this_block':len(states),
                          'new_physics_attempts_this_block':ledger.calls}),flush=True)
    ledger.log({'event':'block_complete','block':block,'paid_attempts':ledger.calls,'requests':ledger.lookups})
    ledger.close()
    result={'block':block,'states':states,'complete':True,'new_physics_attempts':ledger.calls,
            'requests':ledger.lookups,'mesh_checks':mesh,
            'files':{p.name:sha(p.read_bytes()) for p in folder.iterdir() if p.is_file()}}
    write(folder/'complete.json',result)
    return result

def run(protocol_commit):
    cfg=json.loads(CONFIG.read_text());out=ROOT/cfg['out'];manifest=json.loads((out/'manifest.json').read_text())
    for p,digest in manifest['frozen_files'].items():
        if sha((ROOT/p).read_bytes())!=digest:raise ValueError('Frozen file changed: '+p)
    if len(protocol_commit)!=40:raise ValueError('Provide verified published protocol commit')
    completed=[];total=0
    for block in cfg['seed_blocks']:
        folder=out/f'block_{block}'
        if folder.exists():
            if not (folder/'complete.json').exists():
                raise RuntimeError('Incomplete block: stop; explicit failure/recovery accounting required')
            result=json.loads((folder/'complete.json').read_text())
            for name,digest in result['files'].items():
                if sha((folder/name).read_bytes())!=digest:raise ValueError('Changed completed record')
        else:result=collect_block(cfg,block,out,total)
        completed.append(block);total+=result['new_physics_attempts']
        write(out/'run_status.json',{'complete':False,'completed_blocks':completed,
                                    'new_physics_attempts':total,'protocol_commit':protocol_commit,
                                    'recovery_attempts':0,'replacement_seed_blocks':0})
    write(out/'run_status.json',{'complete':True,'completed_blocks':completed,
                                'new_physics_attempts':total,'protocol_commit':protocol_commit,
                                'recovery_attempts':0,'replacement_seed_blocks':0})
    print(json.dumps({'complete':True,'seed_blocks':len(completed),'new_physics_attempts':total}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true')
    parser.add_argument('--run',action='store_true');parser.add_argument('--protocol-commit')
    args=parser.parse_args()
    if args.prepare:prepare()
    elif args.run:run(args.protocol_commit or '')
    else:parser.error('Choose --prepare or --run')
