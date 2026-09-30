"""Offline A/B diagnostics: reads frozen runs; never writes optimization histories."""
import os
for _key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[_key]='1'
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import hashlib
import io
import json
import zipfile
import numpy as np
import pandas as pd
from .core import bounds, management, choose, distances, Settings
from .experiment import problem


def load_events(directory):
    entries=[json.loads(s) for s in (Path(directory)/'events.jsonl').read_text('utf-8').splitlines()]
    meta=entries[0]
    pre=entries[1::2]; post=entries[2::2]
    assert len(pre)==len(post)
    for a,b in zip(pre,post):
        assert a['event']=='pre' and b['event']=='label' and a['t']==b['t']
        assert a['n_observed']==a['t']-1 and 'y' not in a
    return meta,pre,post


def diagnostic_one(args):
    directory,out,fixed=args
    directory=Path(directory); out=Path(out)/directory.name
    out.mkdir(parents=True,exist_ok=True)
    cfg=Settings(); meta,pre,post=load_events(directory)
    digest=hashlib.sha256((directory/'events.jsonl').read_bytes()).hexdigest()
    manifest=dict(source_hash=digest,fixed=fixed,schema=1)
    if (out/'count.json').exists():
        count=json.loads((out/'count.json').read_text('utf-8'))
        if count['manifest']!=manifest:
            raise RuntimeError('Diagnostic manifest mismatch.')
        return count
    diag_objective=problem(meta['fid'],meta['dim'],meta['instance'])
    x,y,residuals=[],[],[]
    monitors={v:[] for v in ['G','T','S','ST']}
    stagnation=0; calibration_rows=[]; decision_rows=[]
    archive=zipfile.ZipFile(directory/'candidate_pools.npz')
    labels=zipfile.ZipFile(out/'hidden_labels.npz','w',compression=zipfile.ZIP_DEFLATED)
    journal=(out/'decisions_before_diagnostic_labels.jsonl').open('w',encoding='utf-8')
    n_states=0
    for a,b in zip(pre,post):
        t=a['t']
        if a['mu'] is not None:
            # All recalibrator histories consist only of original PREQUENTIAL residuals.
            selected_bounds={v:bounds(np.array([a['mu']]),a['scale'],np.array([a['x_unit']]),residuals,t,v,cfg) for v in monitors}
            if t in meta['checkpoints']:
                pool=np.load(io.BytesIO(archive.read(f't{t}_points.npy')),allow_pickle=False)
                mu=np.load(io.BytesIO(archive.read(f't{t}_mu.npy')),allow_pickle=False)
                # Source audit: stored selected prediction and candidate prediction coincide.
                np.testing.assert_allclose(mu[a['selection_index']],a['mu'],rtol=0,atol=1e-10)
                cb={v:bounds(mu,a['scale'],pool,residuals,t,v,cfg) for v in monitors}
                top=np.argsort(mu,kind='stable')[:int(np.ceil(len(mu)*.1))]
                decisions={}
                for v,bo in cb.items():
                    fullstate=management(monitors[v],stagnation,'full',fixed,cfg)
                    fixedstate=management(monitors[v],stagnation,'fixed',fixed,cfg)
                    fk,fmode,_,_=choose(pool,np.array(x),mu,bo,min(y),a['scale'],fullstate,meta['seed'],t,True,cfg)
                    kk,kmode,_,_=choose(pool,np.array(x),mu,bo,min(y),a['scale'],fixedstate,meta['seed'],t,False,cfg)
                    eligibility=bo['support'] & (bo['H']<min(y)-cfg.tau_factor*a['scale'])
                    uk=int(np.argmin(np.where(bo['support'],bo['H'],np.inf))) if np.any(eligibility) else int(np.argmin(mu))
                    decisions[v]={
                        'mean':dict(k=int(np.argmin(mu)),mode='mean'),
                        'fixed':dict(k=kk,mode=kmode),
                        'upper':dict(k=uk,mode='upper' if np.any(eligibility) else 'mean'),
                        'feedback':dict(k=fk,mode=fmode,p=fullstate['p'],a=fullstate['a']),
                        'max_distance':dict(k=int(np.argmax(distances(pool,np.array(x)).min(axis=1))),mode='explore')}
                # Freeze decisions before the extra oracle is accessed.
                journal.write(json.dumps(dict(t=t,n_observed=len(y),decisions=decisions))+'\n'); journal.flush()
                yy=np.array([diag_objective((np.array(meta['lb'])+(np.array(meta['ub'])-np.array(meta['lb']))*point).tolist()) for point in pool])
                buffer=io.BytesIO(); np.save(buffer,yy,allow_pickle=False); labels.writestr(f't{t}_y.npy',buffer.getvalue())
                n_states+=1
                base=dict(runid=directory.name,history=meta['method'],fid=meta['fid'],dim=meta['dim'],instance=meta['instance'],rep=meta['rep'],t=t,phase=t/meta['budget'])
                for v,bo in cb.items():
                    groups={'pool':np.arange(len(pool)),'top10':top,'actual_selected':np.array([a['selection_index']])}
                    groups.update({strategy:np.array([dd['k']]) for strategy,dd in decisions[v].items()})
                    declaration_set=np.where(bo['support'] & (bo['H']<min(y)-cfg.tau_factor*a['scale']))[0]
                    groups['pool_declared']=declaration_set
                    for group,ix in groups.items():
                        u=(yy[ix]-bo['H'][ix])/a['scale']
                        failure=yy[ix]>bo['H'][ix]
                        calibration_rows.append(dict(**base,calibrator=v,group=group,n=len(ix),failures=int(failure.sum()),
                            failure_rate=float(failure.mean()) if len(ix) else np.nan,
                            quantile_loss=float(np.mean(u*(.9-(u<0)))) if len(ix) else np.nan,
                            margin=float(bo['q'][ix].mean()) if len(ix) else np.nan,
                            neff=float(bo['neff'][ix].mean()) if len(ix) else np.nan,
                            fallback=float(np.mean(bo['used'][ix]!=v)) if len(ix) else np.nan,
                            support=float(bo['support'][ix].mean()) if len(ix) else np.nan,
                            weighted_distance=float(bo['weighted_distance'][ix].mean()) if len(ix) else np.nan))
                    actual_improves=yy<min(y)-cfg.tau_factor*a['scale']
                    pool_best=float(yy.min())
                    for strategy,dd in decisions[v].items():
                        j=dd['k']; declared=bool(bo['support'][j] and bo['H'][j]<min(y)-cfg.tau_factor*a['scale'])
                        false=declared and not bool(actual_improves[j])
                        assert not false or yy[j]>bo['H'][j]
                        decision_rows.append(dict(**base,calibrator=v,strategy=strategy,index=j,mode=dd['mode'],
                            normalized_improvement=max(0.,min(y)-float(yy[j]))/a['scale'],
                            opportunity_loss=(float(yy[j])-pool_best)/a['scale'],
                            declared=declared,false_claim=false,upper_failure=bool(yy[j]>bo['H'][j]),
                            improvement_success=bool(actual_improves[j]),no_improving_candidate=not bool(actual_improves.any()),
                            pool_recall=float(np.sum(actual_improves & np.isin(np.arange(len(pool)),declaration_set))/actual_improves.sum()) if actual_improves.any() else np.nan,
                            p=dd.get('p',np.nan)))
            # Updating AFTER diagnostic scoring does not affect x/y chosen by the source run.
            for v,bo in selected_bounds.items():
                monitors[v].append((float(b['y']>bo['H'][0]),float(bo['q'][0])))
            residuals.append((t,np.array(a['x_unit']),b['residual']))
            stagnation=0 if b['significant_improvement'] else stagnation+1
        x.append(np.array(a['x_unit'])); y.append(b['y'])
    journal.close();labels.close();archive.close()
    pd.DataFrame(calibration_rows).to_csv(out/'calibration.csv',index=False)
    pd.DataFrame(decision_rows).to_csv(out/'decisions.csv',index=False)
    count=dict(manifest=manifest,algorithm_evaluations=meta['budget'],diagnostic_evaluations=diag_objective.state.evaluations,states=n_states)
    assert diag_objective.state.evaluations==n_states*cfg.candidates
    assert hashlib.sha256((directory/'events.jsonl').read_bytes()).hexdigest()==digest
    (out/'count.json').write_text(json.dumps(count,indent=2),encoding='utf-8')
    return count


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--out',required=True)
    ap.add_argument('--fixed',type=float,default=.3);ap.add_argument('--workers',type=int,default=4)
    args=ap.parse_args();source=Path(args.source);out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    jobs=[(str(f.parent),str(out),args.fixed) for f in sorted(source.glob('*/summary.json'))]
    count=0;charged=0;diagnostic=0
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures=[executor.submit(diagnostic_one,j) for j in jobs]
        for fu in as_completed(futures):
            c=fu.result();count+=1;charged+=c['algorithm_evaluations'];diagnostic+=c['diagnostic_evaluations']
            if count%20==0 or count==len(jobs):print(f'{count}/{len(jobs)} diagnostic runs',flush=True)
    (out/'counts.json').write_text(json.dumps(dict(runs=count,algorithm=charged,diagnostic=diagnostic),indent=2),encoding='utf-8')


if __name__=='__main__':main()
