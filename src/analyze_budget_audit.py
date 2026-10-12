"""Frozen prefix-only comparison and independent model/history verification."""
from __future__ import annotations
import argparse,csv,json
from collections import Counter,defaultdict
import numpy as np
from .budgeted_decision_audit import Observation,audit,calibration_rule,classify
from .engineering_optimization_budget_audit import ROOT,CONFIG,sha,key,pool,model,select,seed
from scipy.stats import qmc

DEST=ROOT/'paper/engineering_optimization/budget_audit'
def dump(name,value):
    DEST.mkdir(parents=True,exist_ok=True)
    (DEST/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def table(name,rows):
    DEST.mkdir(parents=True,exist_ok=True)
    with (DEST/name).open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n')
        writer.writeheader();writer.writerows(rows)

def verify_block(cfg,folder):
    complete=json.loads((folder/'complete.json').read_text())
    for name,digest in complete['files'].items():assert sha((folder/name).read_bytes())==digest
    block=complete['block'];pending=None;theta=None;warm_x=[];warm_y=[]
    sources={};branches={};checks=Counter();cache={};plans={};physical=0
    expected_warm=qmc.Sobol(19,scramble=True,seed=seed(cfg,block,0,1)).random_base2(6)[:cfg['warm_start']]
    for line in (folder/'events.jsonl').read_text().splitlines():
        row=json.loads(line);event=row['event']
        if event=='warm_complete':theta=row['theta']
        elif event=='state_frozen':
            p=json.loads((folder/(row['state']+'_plan.json')).read_text());plans[row['state']]=p
            assert row['no_first_action_or_probe_labels_read']
            assert sha((folder/(row['state']+'_plan.json')).read_bytes())==row['plan_sha256']
            xx,yy=sources[p['source']]
            assert np.array_equal(xx,p['X']) and np.array_equal(yy,p['y']) and len(yy)==100
            si=cfg['source_controls'].index(p['source']);gp=model(xx,yy,theta,cfg)
            candidates=pool(cfg,block,si,3);assert sha(candidates.tobytes())==p['root_pool_sha256']
            from .engineering_optimization_gp_audit import scores
            mu,sd=gp.predict(candidates,return_std=True)
            decisions={c:int(np.argmax(v)) for c,v in scores(mu,sd,float(yy.min()),max(float(yy.std()),1e-12),cfg).items()}
            assert decisions==p['root_decisions']
            points={}
            for b,names in p['classes'].items():
                assert all(np.array_equal(candidates[decisions[n]],p['actions'][b]) for n in names)
                points[key(p['actions'][b])]=b
            assert len(points)==len(p['classes']);checks['states_frozen_before_probe_and_action_labels']+=1
        elif event=='pre':
            assert pending is None;phase=row['phase'];x=np.array(row['x'])
            if phase=='warm':assert np.array_equal(x,expected_warm[row['step']])
            elif phase=='source':
                control=row['source'];xx,yy=sources.setdefault(control,(np.array(warm_x),np.array(warm_y)))
                assert len(yy)==50+row['step'];gp=model(xx,yy,theta,cfg)
                expected,meta=select(gp,xx,yy,pool(cfg,block,0,2,row['step']),control,cfg)
                assert np.array_equal(expected,x) and meta['pool_sha256']==row['pool_sha256']
                assert np.allclose([meta['mu'],meta['sd']],[row['mu'],row['sd']],rtol=1e-8,atol=1e-8)
                checks['past_only_source_choices']+=1
            elif phase in {'calibration','oracle'}:
                p=plans[row['state']];si=cfg['source_controls'].index(p['source'])
                if phase=='calibration':
                    assert np.array_equal(x,pool(cfg,block,si,4)[row['step']])
                    xx,yy=np.array(p['X']),np.array(p['y'])
                else:
                    bkey=(p['state'],row['continuation'],row['branch'])
                    xx,yy=branches.setdefault(bkey,(np.array(p['X']),np.array(p['y'])))
                    assert len(yy)==100+row['step']
                    if row['step']==0:assert np.array_equal(x,p['actions'][row['branch']])
                    else:
                        expected,meta=select(model(xx,yy,theta,cfg),xx,yy,
                                             pool(cfg,block,si,5,row['step']),row['continuation'],cfg)
                        assert np.array_equal(expected,x) and meta['pool_sha256']==row['pool_sha256']
                        checks['common_continuation_choices']+=1
                mm,ss=model(xx,yy,theta,cfg).predict(x[None],return_std=True)
                assert np.allclose([mm[0],ss[0]],[row['mu'],row['sd']],rtol=1e-8,atol=1e-8)
                checks['past_only_diagnostic_predictions']+=1
            pending=row
        elif event=='label':
            assert pending and row['request']==pending['request'];phase=pending['phase'];x=np.array(pending['x'])
            cache_key=pending['context']+':'+key(x)
            if row['origin']=='exact_paid_response_cache':assert cache[cache_key]==row['y']
            else:physical+=1
            cache[cache_key]=row['y'];assert physical==row['paid_attempts']
            if phase=='warm':warm_x.append(pending['x']);warm_y.append(row['y'])
            elif phase=='source':
                xx,yy=sources[pending['source']]
                sources[pending['source']]=(np.vstack((xx,x)),np.append(yy,row['y']))
            elif phase=='oracle':
                bkey=(pending['state'],pending['continuation'],pending['branch']);xx,yy=branches[bkey]
                branches[bkey]=(np.vstack((xx,x)),np.append(yy,row['y']))
            checks['ordered_pre_label_pairs']+=1;pending=None
    assert pending is None and physical==complete['new_physics_attempts']
    for p in plans.values():
        summary=json.loads((folder/(p['state']+'_summary.json')).read_text())
        for rule,trajectories in summary['trajectories'].items():
            for b,records in trajectories.items():
                xx,yy=branches[p['state'],rule,b]
                assert [r['y'] for r in records]==yy[-6:].tolist()
                assert [r['incumbent'] for r in records]==[float(yy[:101+h].min()) for h in range(6)]
                checks['endpoint_curves']+=1
    return checks

def evaluate(cfg,summaries):
    rows=[];selections=[];traces=[]
    modes=['calibration','immediate','fixed_depth','fixed_breadth','adaptive','full']
    for s in summaries:
        baseline=s['mapping']['mean'];initial=s['initial_best']
        for continuation,curves in s['trajectories'].items():
            for budget in cfg['budget_sensitivity']:
                for margin in cfg['margin_sensitivity']:
                    truth={b:classify((curves[baseline][5]['incumbent']-c[5]['incumbent'])/initial,margin)
                           for b,c in curves.items()}
                    for mode in modes:
                        if mode=='calibration':
                            local={**cfg,'relative_margin':margin}
                            labels=calibration_rule(s['classes'],baseline,s['root_ei'],
                                                    s['calibration']['nrmse'],s['calibration']['coverage90'],local)
                            effects={n:s['root_ei'][b]-s['root_ei'][baseline] for b,names in s['classes'].items() for n in names}
                            result={'labels':labels,'effects':effects,'requests':cfg['calibration_points'],
                                    'distinct_points':cfg['calibration_points'],'trace':[]}
                            points=[key(x) for x in s['calibration']['points']]
                        else:
                            exposed={b:-1 for b in curves}
                            def observe(branch,step):
                                assert step==exposed[branch]+1;exposed[branch]=step
                                record=curves[branch][step]
                                return Observation(record['incumbent'],record['point_key'])
                            result=audit(s['classes'],baseline,observe,initial,s['root_sd'],
                                         budget=6*len(curves) if mode=='full' else budget,
                                         margin=margin,mode=mode)
                            points=[t['point_key'].split(':',1)[1] for t in result['trace']]
                        initial_keys={key(x) for x in s['X']}
                        paid_unique=len(set(points)-initial_keys)
                        primary=(budget==cfg['audit_budget'] and margin==cfg['relative_margin'])
                        if primary:
                            traces.append({'state':s['state'],'block':s['block'],'continuation':continuation,
                                           'method':mode,'requests':result['requests'],'trace':result['trace']})
                        # Preserve named contrasts AND mark one representative
                        # per distinct nonbaseline action for primary inference.
                        for control in cfg['first_controls'][1:]:
                            branch=s['mapping'][control];pred=result['labels'][control];target=truth[branch]
                            alias=(branch==baseline)
                            representative=(not alias and control==s['classes'][branch][0])
                            end_mean=curves[baseline][5]['incumbent'];end_alt=curves[branch][5]['incumbent']
                            deployed=end_alt if pred=='better' else end_mean
                            rows.append({'block':s['block'],'state':s['state'],'source':s['source'],
                                'continuation':continuation,'budget':budget,'margin':margin,'method':mode,
                                'control':control,'branch':branch,'structural_alias':alias,
                                'unique_nonbaseline_contrast':representative,'prediction':pred,'target':target,
                                'classified':pred!='abstain','classification_error':pred!='abstain' and pred!=target,
                                'false_promotion':pred=='better' and target!='better',
                                'false_rejection':pred in ['tie','worse'] and target=='better',
                                'abstention_missed_positive':pred=='abstain' and target=='better',
                                'pairwise_endpoint_regret_percent':100*(deployed-min(end_mean,end_alt))/initial,
                                'true_advantage_percent':100*(end_mean-end_alt)/initial,
                                'audit_response_requests':result['requests'],
                                'distinct_new_to_training_points':paid_unique,'primary':primary})
                        chosen='mean';best_effect=margin
                        for control in cfg['first_controls'][1:]:
                            if result['labels'][control]=='better' and result['effects'][control]>best_effect:
                                chosen=control;best_effect=result['effects'][control]
                        endpoint=curves[s['mapping'][chosen]][5]['incumbent'];oracle=min(c[5]['incumbent'] for c in curves.values())
                        selections.append({'block':s['block'],'state':s['state'],'continuation':continuation,
                           'budget':budget,'margin':margin,'method':mode,'chosen_control':chosen,
                           'endpoint_compliance':endpoint,'oracle_endpoint_compliance':oracle,
                           'selection_regret_percent':100*(endpoint-oracle)/initial,
                           'audit_response_requests':result['requests'],'distinct_new_to_training_points':paid_unique,
                           'primary':primary})
    return rows,selections,traces

def main(skip_verify=False):
    cfg=json.loads(CONFIG.read_text());out=ROOT/cfg['out'];status=json.loads((out/'run_status.json').read_text())
    assert status['complete'] and status['completed_blocks']==cfg['seed_blocks']
    manifest=json.loads((out/'manifest.json').read_text())
    for p,digest in manifest['frozen_files'].items():assert sha((ROOT/p).read_bytes())==digest
    checks=Counter();summaries=[];physical=0;mesh=[]
    for block in cfg['seed_blocks']:
        folder=out/f'block_{block}';done=json.loads((folder/'complete.json').read_text())
        if not skip_verify:checks.update(verify_block(cfg,folder))
        physical+=done['new_physics_attempts'];mesh.extend(done['mesh_checks'])
        summaries.extend(json.loads((folder/(name+'_summary.json')).read_text()) for name in done['states'])
    assert physical==status['new_physics_attempts'] and len(summaries)==30
    rows,selections,traces=evaluate(cfg,summaries);aggregate=[];block_rows=[]
    groups=defaultdict(list)
    for row in rows:
        if row['unique_nonbaseline_contrast']:
            groups[row['continuation'],row['budget'],row['margin'],row['method']].append(row)
    for (continuation,budget,margin,method),rr in groups.items():
        selected=[s for s in selections if (s['continuation'],s['budget'],s['margin'],s['method'])==(continuation,budget,margin,method)]
        def summarize(part):
            classified=sum(r['classified'] for r in part)
            return {'contrasts':len(part),'classified':classified,'abstained':len(part)-classified,
                    'coverage':classified/len(part) if part else None,
                    **{f:sum(r[f] for r in part) for f in ['classification_error','false_promotion','false_rejection','abstention_missed_positive']},
                    'mean_pairwise_regret_percent':float(np.mean([r['pairwise_endpoint_regret_percent'] for r in part])) if part else None}
        aggregate.append({'continuation':continuation,'budget':budget,'margin':margin,'method':method,
                          **summarize(rr),'state_count':len(selected),
                          'total_audit_requests':sum(s['audit_response_requests'] for s in selected),
                          'total_distinct_new_to_training_points':sum(s['distinct_new_to_training_points'] for s in selected),
                          'mean_selection_regret_percent':float(np.mean([s['selection_regret_percent'] for s in selected]))})
        if budget==cfg['audit_budget'] and margin==cfg['relative_margin']:
            for block in cfg['seed_blocks']:
                part=[r for r in rr if r['block']==block]
                selection=[s for s in selected if s['block']==block]
                block_rows.append({'block':block,'continuation':continuation,'method':method,
                                   **summarize(part),'total_audit_requests':sum(s['audit_response_requests'] for s in selection),
                                   'mean_selection_regret_percent':float(np.mean([s['selection_regret_percent'] for s in selection]))})
    primary=[r for r in aggregate if r['budget']==cfg['audit_budget'] and r['margin']==cfg['relative_margin']]
    report={'complete':True,'protocol_commit':status['protocol_commit'],'seed_blocks':10,'states':30,
            'continuations':cfg['continuations'],'independent_replication_unit':'complete seed block',
            'new_physics_attempts':physical,'recovery_attempts':0,'replacement_blocks':0,
            'checks':dict(checks),'primary':primary,'sensitivity':aggregate,
            'mesh_repeatability_max_relative':max(m['repeat_relative_difference'] for m in mesh),
            'mesh_sensitivity_max_relative':max(m['mesh_relative_difference'] for m in mesh),
            'margin_is_engineering_certified':False,'confirmatory_pvalues':False,
            'live_deployment_trials':False,'novelty_or_superiority_certified':False}
    dump('analysis.json',report);dump('primary_traces.json',traces);dump('mesh_checks.json',mesh)
    table('classifications.csv',[r for r in rows if r['primary']]);table('sensitivity.csv',aggregate)
    table('seed_block_results.csv',block_rows);table('selections.csv',[s for s in selections if s['primary']])
    print(json.dumps({'complete':True,'physics_attempts':physical,'checks':dict(checks),'primary':primary}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--skip-verify',action='store_true');args=p.parse_args()
    main(args.skip_verify)
