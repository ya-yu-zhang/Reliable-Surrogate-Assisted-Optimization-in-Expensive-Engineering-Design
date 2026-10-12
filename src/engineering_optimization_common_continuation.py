"""First-action interventions followed by an identical declared continuation.

A conditional deterministic finite-horizon contrast, not a global causal theorem.
First labels reuse the released diagnostic ledger only after all plans are frozen.
Future source observations are retrospective diagnostics and never training data.
"""
from __future__ import annotations
import argparse,hashlib,importlib.metadata,json,os,time,warnings
from pathlib import Path
import numpy as np
from scipy.special import ndtr
from scipy.stats import qmc
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel,Matern
from .engineering_optimization_gp_audit import frozen_state
ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/'configs/engineering_optimization_common_continuation.json'
OLD=ROOT/'results/engineering_optimization_gp_audit_v1'

def sha(b): return hashlib.sha256(b).hexdigest()
def write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
def model(X,y,theta,cfg):
    kernel=ConstantKernel(1.,(.05,20))*Matern(np.full(19,.2),(.005,2.),nu=2.5)
    gp=GaussianProcessRegressor(kernel=kernel.clone_with_theta(np.array(theta)),
                                alpha=cfg['alpha'],normalize_y=True,optimizer=None)
    gp.fit(X,y); return gp

def decision_classes(decisions):
    result={}
    for name,index in decisions.items(): result.setdefault(index,[]).append(name)
    return result

def effect_label(delta,tolerance):
    return 'better' if delta>tolerance else 'worse' if delta < -tolerance else 'tie'

def prepare():
    cfg=json.loads(CONFIG.read_text()); out=ROOT/cfg['out']
    if out.exists(): raise FileExistsError('Existing plan/results; no automatic replay')
    out.mkdir(parents=True)
    old_manifest=json.loads((OLD/'manifest.json').read_text()); plans=[]
    for item in old_manifest['states']:
        if item['t']!=cfg['checkpoint']: continue
        assert sha((ROOT/item['source_events']).read_bytes())==item['source_sha256']
        raw=(OLD/item['snapshot']).read_bytes(); assert sha(raw)==item['snapshot_sha256']
        snap=json.loads(raw); meta,X,y,pre=frozen_state(ROOT/item['source_events'],cfg['checkpoint'])
        assert len(y)==100
        gp=model(X,y,snap['kernel_theta'],cfg); mu,sd=gp.predict(np.array([pre['x_unit']]),return_std=True)
        assert np.allclose([mu[0],sd[0]],[pre['optimizer_state']['mu'],pre['optimizer_state']['sd']],rtol=cfg['prediction_rtol'],atol=cfg['prediction_atol'])
        decisions=dict(snap['decisions']); decisions['mean_common_shift']=decisions['mean']
        classes=decision_classes(decisions)
        # The common-additive control uses canonical unshifted comparison to
        # preserve mathematical ordering without finite-precision cancellation.
        plan={'state':item['snapshot'].removesuffix('.json'),'method':item['method'],
              'rep':item['rep'],'X':X.tolist(),'y':y.tolist(),'theta':snap['kernel_theta'],
              'initial_best':float(y.min()),'decisions':decisions,
              'actions':{str(i):snap['pool'][i] for i in classes},
              'decision_classes':{str(i):names for i,names in classes.items()},
              'source_events':item['source_events'],'source_sha256':item['source_sha256'],
              'snapshot_sha256':item['snapshot_sha256'],'source_prediction_replayed':True}
        path=out/'plans'/(plan['state']+'.json'); write(path,plan)
        plans.append({'path':str(path.relative_to(out)),'sha256':sha(path.read_bytes()),
                      'state':plan['state'],'method':plan['method'],'rep':plan['rep'],
                      'distinct_actions':len(classes)})
    assert len(plans)==30 and {v['method'] for v in plans}==set(cfg['source_methods'])
    manifest={'config':cfg,'config_sha256':sha(CONFIG.read_bytes()),'code_sha256':sha(Path(__file__).read_bytes()),
              'old_diagnostic_journal_sha256':sha((OLD/'diagnostic_events.jsonl').read_bytes()),
              'plans':plans,'future_source_labels_read':False,'new_fe_attempts':0,
              'versions':{p:importlib.metadata.version(p) for p in ['numpy','scipy','scikit-learn','engibench','cvxopt']}}
    write(out/'manifest.json',manifest)
    print(json.dumps({'frozen_states':len(plans),'distinct_actions':sum(v['distinct_actions'] for v in plans),'new_fe_attempts':0}))

class Ledger:
    def __init__(self,out,cap,objective,cache):
        self.out,self.cap,self.objective,self.cache=out,cap,objective,cache
        self.calls=0; self.reused=0; self.journal=(out/'events.jsonl').open('x')
    def log(self,row): self.journal.write(json.dumps(row,separators=(',',':'),allow_nan=False)+'\n'); self.journal.flush()
    def evaluate(self,x,state,branch,step,metadata):
        key=np.asarray(x,dtype='<f8').tobytes().hex()
        self.log({'event':'pre','state':state,'branch':branch,'step':step,'x':x.tolist(),**metadata})
        if key in self.cache:
            value=self.cache[key]; self.reused+=1; origin='previous_paid_or_current_cache'; elapsed=0.
        else:
            if self.calls>=self.cap: raise RuntimeError('Prespecified attempt cap reached')
            self.calls+=1; started=time.perf_counter()
            try: value=float(self.objective(x))
            except Exception as exc:
                self.log({'event':'failure','physical_attempt':self.calls,'error':repr(exc)}); raise
            elapsed=time.perf_counter()-started; origin='new_fe_attempt'
            if not np.isfinite(value) or value<=0: raise FloatingPointError('Invalid compliance')
            self.cache[key]=value
        self.log({'event':'label','state':state,'branch':branch,'step':step,'y':value,
                  'origin':origin,'fe_seconds':elapsed,'physical_attempts_so_far':self.calls})
        return value

def diagnostic_cache():
    cache={}; pre=None
    for line in (OLD/'diagnostic_events.jsonl').open():
        row=json.loads(line)
        if row['event']=='diagnostic_pre': pre=row
        elif row['event']=='diagnostic_label':
            key=np.asarray(pre['point'],dtype='<f8').tobytes().hex()
            if key in cache: assert cache[key]==row['y']
            cache[key]=row['y']
    return cache

def retrospective_predictions(plan,gp,cfg):
    meta,X,y,pre=frozen_state(ROOT/plan['source_events'],cfg['checkpoint']+10)
    held_X=X[-10:]; held_y=y[-10:]
    # These ten source-selected points are biased by their original optimizer;
    # coverage is descriptive only and carries no exchangeability guarantee.
    mu,sd=gp.predict(held_X,return_std=True); scale=max(float(np.std(plan['y'])),1e-12)
    return {'held_out_points':10,'normalized_rmse':float(np.sqrt(np.mean((held_y-mu)**2))/scale),
            'empirical_90_interval_coverage':float(np.mean(np.abs(held_y-mu)<=1.6448536269514722*sd)),
            'selection_biased_source_points':True,'identical_across_first_controls':True,
            'used_for_training_or_promotion':False}

def run():
    cfg=json.loads(CONFIG.read_text()); out=ROOT/cfg['out']; manifest=json.loads((out/'manifest.json').read_text())
    assert manifest['code_sha256']==sha(Path(__file__).read_bytes()) and manifest['config_sha256']==sha(CONFIG.read_bytes())
    assert manifest['old_diagnostic_journal_sha256']==sha((OLD/'diagnostic_events.jsonl').read_bytes())
    cache=diagnostic_cache()
    for item in manifest['plans']:
        assert sha((out/item['path']).read_bytes())==item['sha256']
        p=json.loads((out/item['path']).read_text()); assert sha((ROOT/p['source_events']).read_bytes())==p['source_sha256']
        for action in p['actions'].values(): assert np.asarray(action,dtype='<f8').tobytes().hex() in cache
    from .engineering_beam_adapter import make_problem
    ledger=Ledger(out,cfg['max_new_fe_attempts'],make_problem(),cache)
    ledger.log({'event':'meta','manifest_sha256':sha((out/'manifest.json').read_bytes()),'objective_context':'Beams2D default force, mesh100x50, material/supports unchanged'})
    summaries=[]
    for item in manifest['plans']:
        plan=json.loads((out/item['path']).read_text()); curves={}; branch_records={}; before=ledger.calls
        X0,y0=np.array(plan['X']),np.array(plan['y']); root_gp=model(X0,y0,plan['theta'],cfg)
        ledger.log({'event':'state_start','state':plan['state'],'decisions':plan['decisions'],
                    'initial_history_sha256':sha(X0.tobytes()+y0.tobytes()),'all_first_choices_frozen':True})
        for branch,action in plan['actions'].items():
            X,y=X0.copy(),y0.copy(); x=np.array(action); mu,sd=root_gp.predict(x[None],return_std=True)
            value=ledger.evaluate(x,plan['state'],branch,0,{'observations_before':len(y),'mu':float(mu[0]),'sd':float(sd[0]),'choice_origin':'released_frozen_acquisition_action'})
            X=np.vstack((X,x)); y=np.append(y,value); curve=[float(y.min())]; gp_seconds=0.
            for step in range(1,cfg['continuation_steps']+1):
                started=time.perf_counter(); sequence_seed=int(np.random.SeedSequence([cfg['master_seed'],cfg['source_methods'].index(plan['method']),plan['rep'],step]).generate_state(1)[0])
                pool=qmc.Sobol(19,scramble=True,seed=sequence_seed).random_base2(cfg['pool_power'])
                observed={a.tobytes() for a in X}; pool=np.array([a for a in pool if a.tobytes() not in observed])
                with warnings.catch_warnings(record=True) as ws:
                    warnings.simplefilter('always'); gp=model(X,y,plan['theta'],cfg); mu,sd=gp.predict(pool,return_std=True)
                index=int(np.argmin(mu)); x=pool[index]; elapsed=time.perf_counter()-started; gp_seconds+=elapsed
                value=ledger.evaluate(x,plan['state'],branch,step,{'observations_before':len(y),
                    'mu':float(mu[index]),'sd':float(sd[index]),'pool_seed':sequence_seed,'pool_index':index,
                    'pool_sha256':sha(pool.tobytes()),'gp_seconds':elapsed,'warnings':[str(w.message) for w in ws]})
                X=np.vstack((X,x)); y=np.append(y,value); curve.append(float(y.min()))
            curves[branch]=curve; branch_records[branch]={'curve':curve,'gp_seconds':gp_seconds,'training_observations_final':len(y)}
        prediction=retrospective_predictions(plan,root_gp,cfg)
        controls={name:curves[str(index)] for name,index in plan['decisions'].items()}
        summary={'state':plan['state'],'method':plan['method'],'rep':plan['rep'],'initial_best':plan['initial_best'],
                 'decision_classes':plan['decision_classes'],'decisions':plan['decisions'],'control_curves':controls,
                 'branch_records':branch_records,'retrospective_prediction_diagnostics':prediction,
                 'new_fe_attempts':ledger.calls-before,'complete':True}
        write(out/'summaries'/(plan['state']+'.json'),summary); summaries.append(summary)
        ledger.log({'event':'state_complete','state':plan['state'],'new_fe_attempts':ledger.calls-before})
        os.fsync(ledger.journal.fileno())
        write(out/'run_status.json',{'complete':False,'states_completed':len(summaries),'new_fe_attempts':ledger.calls})
        print(json.dumps({'state':plan['state'],'states_completed':len(summaries),'new_fe_attempts':ledger.calls}),flush=True)
    ledger.log({'event':'complete','new_fe_attempts':ledger.calls,'cache_reuses':ledger.reused}); os.fsync(ledger.journal.fileno()); ledger.journal.close()
    write(out/'run_status.json',{'complete':True,'states_completed':len(summaries),'new_fe_attempts':ledger.calls,'cache_reuses':ledger.reused,'journal_sha256':sha((out/'events.jsonl').read_bytes()),'recovery_attempts':0})

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--prepare',action='store_true'); p.add_argument('--run',action='store_true'); args=p.parse_args()
    if args.prepare: prepare()
    elif args.run: run()
    else: p.error('Choose --prepare or --run')
