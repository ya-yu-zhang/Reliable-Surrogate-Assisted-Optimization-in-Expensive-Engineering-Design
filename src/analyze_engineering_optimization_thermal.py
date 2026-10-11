"""Reconstruct measured thermal endpoints; generate factual author-review tables."""
import csv, hashlib, json
from collections import Counter
from pathlib import Path
import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern
from .engineering_optimization_thermal import choose_gate
from .engineering_optimization_transfer import write_json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'paper/engineering_optimization'

def main():
    cfg=json.loads((ROOT/'configs/engineering_optimization_thermal.json').read_text())
    source=ROOT/cfg['out']; status=json.loads((source/'run_status.json').read_text())
    assert status['complete']
    checks=Counter(); cases=[]; all_summaries=[]
    verification=json.loads((OUT/'thermal_verification.json').read_text())
    for path,sha in verification['source_sha256'].items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha
    assert cfg['initial']+3*cfg['pilot_steps']+48==cfg['budget']==96
    assert cfg['initial']+3*cfg['pilot_steps']+2*48+3*72==cfg['case_actual_call_cap']==360
    for folder in sorted(source.glob('condition*_r*')):
        s=json.loads((folder/'summary.json').read_text()); raw=(folder/'events.jsonl').read_bytes()
        assert hashlib.sha256(raw).hexdigest()==s['journal_sha256']
        events=[json.loads(line) for line in raw.splitlines()]; pending=None; groups={}; labels=0
        for event in events:
            if event['event']=='meta':
                assert event['protocol_sha256']==verification['source_sha256']['configs/engineering_optimization_thermal.json']
                assert event['code_sha256']==verification['source_sha256']['src/engineering_optimization_thermal.py']
                assert event['model_sha256']==verification['source_sha256']['src/engineering_thermal_adapter.py']
            elif event['event']=='pre':
                assert pending is None and event['call_id']==labels+1; pending=event
            elif event['event']=='label':
                assert pending and pending['call_id']==event['call_id']
                assert event['relative_residual']<1e-9 and abs(event['boundary_heat_flux']-1)<1e-9
                assert abs(event['mean_density']-.35)<1e-13 and event['minimum_temperature']>=0
                groups.setdefault(pending['workflow'],[]).append((pending,event['y']))
                labels+=1; pending=None; checks['prediction_before_label_pairs']+=1
            elif event['event']=='selection':
                assert labels==48 and not event['validation_labels_seen']
                checks['selection_before_validation_checks']+=1
        assert labels==360 and pending is None and events[-1]['event']=='complete'
        initial=[(p,y) for p,y in groups['shared'] if p['phase']=='initial']; assert len(initial)==24
        X0=np.array([p['x'] for p,y in initial]); y0=np.array([y for p,y in initial]); curves={}; pilots={}
        for policy in cfg['policies']:
            pilots[policy]=[(p,y) for p,y in groups['shared'] if p['phase']=='pilot' and p['policy']==policy]
            assert len(pilots[policy])==8
            curves[policy]=np.minimum.accumulate([min(y0)]+[y for p,y in pilots[policy]]).tolist()
        gate,simple,advantages=choose_gate(curves,cfg)
        assert (gate,simple)==(s['gated_policy'],s['simple_policy'])
        assert curves==s['pilot_curves'] and advantages==s['relative_checkpoint_advantages']
        endpoints={}; histories=[(X0,y0,entries) for entries in pilots.values()]
        for workflow,entries in groups.items():
            if workflow=='shared': continue
            selector=workflow in ['audit_gate','simple_selector']; assert len(entries)==(48 if selector else 72)
            if selector:
                policy=gate if workflow=='audit_gate' else simple
                X=np.vstack([X0,np.array([p['x'] for p,y in pilots[policy]])])
                y=np.concatenate([y0,np.array([v for p,v in pilots[policy]])])
                endpoints[workflow]=min([y for p,y in groups['shared']]+[y for p,y in entries])
            else:
                X,y=X0,y0; endpoints[workflow]=min(y0.tolist()+[y for p,y in entries])
            assert endpoints[workflow]==s['endpoints'][workflow]
            histories.append((X,y,entries)); checks['workflow_budget_endpoint_checks']+=1
        for X,y,entries in histories:
            X,y=X.copy(),y.copy()
            for i,(pre,value) in enumerate(entries):
                assert pre['observations_before']==len(y)
                if i in [0,len(entries)-1]:
                    gp=GaussianProcessRegressor(kernel=Matern(cfg['length_scale'],nu=2.5),alpha=cfg['alpha'],normalize_y=True,optimizer=None)
                    gp.fit(X,y); mu,sd=gp.predict(np.array([pre['x']]),return_std=True)
                    assert np.allclose([mu[0],sd[0]],[pre['mu'],pre['sd']],rtol=1e-9,atol=1e-12)
                    checks['past_only_gp_prediction_replays']+=1
                X=np.vstack((X,pre['x'])); y=np.append(y,value)
        if gate==simple:
            assert s['validation_curves']['audit_gate']==s['validation_curves']['simple_selector']
            checks['same_policy_exact_replays']+=1
        cases.append({'condition':s['condition'],'repeat':s['repeat'],'initial_best':float(y0.min()),
                      'gated_policy':gate,'simple_policy':simple,'gate_changes_choice':gate!=simple,**endpoints})
        all_summaries.append({'case':folder.name,'summary':s})
    assert len(cases)==20
    comparisons=[]
    prior={'central_source':[0.,3.9613670635458065,4.961245754835164,4.961245754835164],
           'offset_source':[0.,.20173943823630358,2.349896832419174,2.349896832419174]}
    lines=['# Thermal equal-budget verification: measured evidence','','Author-review data record; not a drafted manuscript section or a novelty certification.','',
           'Twenty independent initializations, five workflows, 96 paid deployment calls per workflow. Negative paired differences favor the gate. No threshold tuning or confirmatory p-values.','',
           '| Source | Comparator | Median paired difference (%) | Wins/ties/losses |','|---|---|---:|---|']
    for condition in cfg['conditions']:
        group=[v for v in cases if v['condition']==condition]
        for i,comparator in enumerate(['simple_selector','fixed_mean','fixed_ei','fixed_lcb']):
            d=np.array([(v['audit_gate']/v[comparator]-1)*100 for v in group]); median=float(np.median(d))
            assert np.isclose(median,prior[condition][i],rtol=1e-10,atol=1e-10)
            row={'condition':condition,'comparator':comparator,'median_paired_difference_percent':median,
                 'wins':int(sum(d<-1e-8)),'ties':int(sum(abs(d)<=1e-8)),'losses':int(sum(d>1e-8))}
            comparisons.append(row)
            lines.append(f"| {condition} | {comparator} | {median:.6f} | {row['wins']}/{row['ties']}/{row['losses']} |")
    report={'complete':True,'cases':cases,'comparisons':comparisons,'checks':dict(checks),
            'retained_optimization_attempts':7200,'current_verification_attempts':22,
            'previous_lost_session_attempts':7586,'cumulative_thermal_attempts':15888,'additional_record_recovery_attempts':1080,
            'independent_cases':20,'current_replay_added_independent_cases':0,
            'prior_visible_aggregate_results_match':True,'all_original_raw_bytes_recovered':False,
            'gate_superiority_demonstrated':False,'threshold_retuned':False,'inferential_pvalues_added':False}
    write_json(OUT/'thermal_analysis.json',report)
    write_json(OUT/'thermal_retained_summaries.json',{'cases':all_summaries,'status':status})
    with (OUT/'thermal_case_results.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(cases[0])); writer.writeheader(); writer.writerows(cases)
    lines+=['','Gate/simple choices differ in 2/20 cases. Their endpoints in these cases are one tie and one gate loss. The 18 same-policy continuation histories match exactly.','',
            'The replay matches the visible prior aggregate results. It does not certify recovery of every old per-case endpoint or timing byte. Cumulative thermal cost is 15,888 attempts: 7,586 from the lost previous session, plus this replay of 7,200 optimization, 22 numerical verification and 1,080 record-recovery solves. Replay adds no independent case.','',
            '## Verified boundaries','',
            '- Authored small dimensionless thermal model, not a published industrial benchmark or a demonstrably expensive simulator.',
            '- Elastic structure and steady thermal conduction are two physical families. Each family has two conditions, not four independent domains.',
            '- Fixed GP hyperparameters differ from the beam studies. All thermal workflows use identical settings.',
            '- The illustrative temporal gate did not demonstrate superior selection or performance-preserving savings.',
            '- The gate comparison does not isolate every stage of the original auditing framework.',
            '- Final manuscript integration, novelty assessment, scientific interpretation and AI-policy review remain the authors responsibility.','',
            'See THERMAL_PROTOCOL.md and THERMAL_SESSION_RECOVERY.md. Raw records are released with hashes; restoration adds zero solver calls.']
    (OUT/'THERMAL_EVIDENCE.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'cases':len(cases),'checks':dict(checks),'prior_aggregates_match':True,'cumulative_thermal_attempts':15888,'additional_record_recovery_attempts':1080}))
if __name__=='__main__': main()
