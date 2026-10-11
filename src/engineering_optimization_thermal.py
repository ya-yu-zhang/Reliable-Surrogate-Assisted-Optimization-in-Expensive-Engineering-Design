"""Prospective equal-paid-budget test of a declared decision gate.

This gate is a testable instantiation, not a novel acquisition or a guarantee.
No objective labels are consulted when creating the protocol or tuning settings.
Pilot labels are paid search observations and warm-start the selected arm.
Both selectors pay all arms. Validation uses a new candidate namespace.
Shared initial/pilot solves reduce execution duplication only; each workflow
still charges these observations in its 96-call deployment budget.
"""
from __future__ import annotations
import argparse, hashlib, json, time, warnings
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import numpy as np
from scipy.stats import qmc
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern
from .engineering_optimization_transfer import policy_choice, write_json
from .engineering_thermal_adapter import ThermalDesign
ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/'configs/engineering_optimization_thermal.json'

def random_seed(cfg,c,r,namespace,step=0):
    return int(np.random.SeedSequence([cfg['master_seed'],c,r,namespace,step]).generate_state(1)[0])

def choose_gate(curves,cfg):
    priority=cfg['policies']
    best=min(priority,key=lambda p:(curves[p][-1],priority.index(p)))
    improvements=[(curves['mean'][t]-curves[best][t])/curves['mean'][t]
                  for t in cfg['gate_checkpoints']]
    passed=best!='mean' and min(improvements)>=cfg['promotion_margin']
    return (best if passed else 'mean'),best,improvements

def run_case(cfg,c,r):
    folder=ROOT/cfg['out']/f'condition{c}_r{r:02d}'
    folder.mkdir(parents=True,exist_ok=False)
    model=ThermalDesign(cfg['mesh'],cfg['conditions'][c])
    calls=0; started=time.perf_counter()
    journal=(folder/'events.jsonl').open('x')
    def log(d): journal.write(json.dumps(d,separators=(',',':'))+'\n'); journal.flush()
    log({'event':'meta','condition':cfg['conditions'][c],'repeat':r,
         'protocol_sha256':hashlib.sha256(CONFIG.read_bytes()).hexdigest(),
         'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         'model_sha256':hashlib.sha256((ROOT/'src/engineering_thermal_adapter.py').read_bytes()).hexdigest()})
    def evaluate(x,workflow,phase,policy,step,metadata=None):
        nonlocal calls
        if calls>=cfg['case_actual_call_cap']: raise RuntimeError('Call cap reached')
        calls+=1
        log({'event':'pre','call_id':calls,'workflow':workflow,'phase':phase,
             'policy':policy,'step':step,'x':x.tolist(),**(metadata or {})})
        t=time.perf_counter()
        try: y,checks=model.solve(x)
        except Exception as exc:
            log({'event':'failure','call_id':calls,'error':repr(exc)}); raise
        log({'event':'label','call_id':calls,'y':y,'seconds':time.perf_counter()-t,**checks})
        return y
    X0=qmc.Sobol(12,scramble=True,seed=random_seed(cfg,c,r,1)).random_base2(5)[:cfg['initial']]
    y0=np.array([evaluate(x,'shared','initial',None,i) for i,x in enumerate(X0)])
    def run(X,y,policy,steps,workflow,namespace):
        X,y=X.copy(),y.copy(); curve=[float(y.min())]
        for s in range(steps):
            pool=qmc.Sobol(12,scramble=True,seed=random_seed(cfg,c,r,namespace,s)).random_base2(cfg['pool_power'])
            observed={x.tobytes() for x in X}
            pool=np.asarray([x for x in pool if x.tobytes() not in observed])
            gp=GaussianProcessRegressor(kernel=Matern(cfg['length_scale'],nu=2.5),
                                        alpha=cfg['alpha'],normalize_y=True,optimizer=None)
            with warnings.catch_warnings(record=True) as ws:
                warnings.simplefilter('always'); gp.fit(X,y); mu,sd=gp.predict(pool,return_std=True)
            index=policy_choice(mu,sd,float(y.min()),max(float(y.std()),1e-12),policy,cfg)
            x=pool[index]
            value=evaluate(x,workflow,'pilot' if namespace==2 else 'validation',policy,s,
                           {'mu':float(mu[index]),'sd':float(sd[index]),'pool_index':index,
                            'observations_before':len(y),'warnings':[str(w.message) for w in ws]})
            X=np.vstack((X,x)); y=np.append(y,value); curve.append(float(y.min()))
        return X,y,curve
    pilots={p:run(X0,y0,p,cfg['pilot_steps'],'shared',2) for p in cfg['policies']}
    curves={p:v[2] for p,v in pilots.items()}
    gated,simple,improvements=choose_gate(curves,cfg)
    # All decisions are persisted before any independent validation labels.
    log({'event':'selection','gated':gated,'simple':simple,'pilot_curves':curves,
         'relative_checkpoint_advantages':improvements,'actual_calls_so_far':calls,
         'validation_labels_seen':False})
    remaining=cfg['budget']-cfg['initial']-len(cfg['policies'])*cfg['pilot_steps']
    endpoints={}; histories={}
    for name,policy in [('audit_gate',gated),('simple_selector',simple)]:
        X,y,_=pilots[policy]
        _,_,curve=run(X,y,policy,remaining,name,3)
        # All paid trials produce usable engineering designs, including other arms.
        paid_best=min(v[2][-1] for v in pilots.values())
        histories[name]=curve
        endpoints[name]=min(paid_best,curve[-1])
    for p in cfg['policies']:
        _,_,curve=run(X0,y0,p,cfg['budget']-cfg['initial'],'fixed_'+p,3)
        histories['fixed_'+p]=curve; endpoints['fixed_'+p]=curve[-1]
    assert calls==cfg['case_actual_call_cap']
    log({'event':'complete','actual_calls':calls}); journal.close()
    summary={'condition':cfg['conditions'][c],'repeat':r,'initial_best':float(y0.min()),
             'gated_policy':gated,'simple_policy':simple,'pilot_curves':curves,
             'relative_checkpoint_advantages':improvements,'endpoints':endpoints,
             'validation_curves':histories,'paid_budget_per_workflow':cfg['budget'],
             'actual_calls':calls,'complete':True,'elapsed_seconds':time.perf_counter()-started,
             'journal_sha256':hashlib.sha256((folder/'events.jsonl').read_bytes()).hexdigest()}
    write_json(folder/'summary.json',summary)
    return {'condition':c,'repeat':r,'actual_calls':calls}

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--run',action='store_true'); args=parser.parse_args()
    cfg=json.loads(CONFIG.read_text())
    if not args.run: print(json.dumps(cfg,indent=2)); return
    out=ROOT/cfg['out']
    if out.exists(): raise FileExistsError('Existing results: no automatic replay')
    assert cfg['global_actual_call_cap']==cfg['case_actual_call_cap']*len(cfg['conditions'])*cfg['repeats']
    out.mkdir(parents=True)
    completed=[]
    with ProcessPoolExecutor(max_workers=cfg['workers']) as ex:
        futures=[ex.submit(run_case,cfg,c,r) for c in range(len(cfg['conditions'])) for r in range(cfg['repeats'])]
        for future in as_completed(futures):
            completed.append(future.result())
            write_json(out/'run_status.json',{'complete':False,'completed':completed,'config':cfg})
            print(json.dumps(completed[-1]),flush=True)
    write_json(out/'run_status.json',{'complete':True,'completed':completed,'config':cfg})
if __name__=='__main__': main()
