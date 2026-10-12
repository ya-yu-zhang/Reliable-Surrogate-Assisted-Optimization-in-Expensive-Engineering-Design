"""Independent history/pool/prediction reconstruction and factual evidence tables."""
import csv,hashlib,json
from collections import Counter
from pathlib import Path
import numpy as np
from scipy.stats import qmc
from .engineering_optimization_common_continuation import ROOT,CONFIG,model,effect_label

def sha(b): return hashlib.sha256(b).hexdigest()
def main():
    cfg=json.loads(CONFIG.read_text()); out=ROOT/cfg['out']; dest=ROOT/'paper/engineering_optimization/common_continuation'
    dest.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((out/'manifest.json').read_text()); status=json.loads((out/'run_status.json').read_text())
    recovery=json.loads((out/'recovery_accounting.json').read_text())
    raw=(out/'events.jsonl').read_bytes(); assert status['complete'] and sha(raw)==status['journal_sha256']
    plans={v['state']:json.loads((out/v['path']).read_text()) for v in manifest['plans']}
    for item in manifest['plans']: assert sha((out/item['path']).read_bytes())==item['sha256']
    histories={}; curves={}; pending=None; checks=Counter(); state_order=[]; physical=0; first_count=0
    for line in raw.splitlines():
        row=json.loads(line); event=row['event']
        if event=='state_start':
            p=plans[row['state']]; X0,y0=np.array(p['X']),np.array(p['y'])
            assert sha(X0.tobytes()+y0.tobytes())==row['initial_history_sha256']
            assert row['all_first_choices_frozen'] and row['decisions']==p['decisions']
            state_order.append(row['state']); checks['frozen_state_boundaries']+=1
        elif event=='pre':
            assert pending is None; p=plans[row['state']]; key=row['state'],row['branch']
            X,y=histories.setdefault(key,(np.array(p['X']),np.array(p['y'])))
            assert row['observations_before']==len(y)==100+row['step']
            gp=model(X,y,p['theta'],cfg); point=np.array(row['x'])
            if row['step']==0:
                assert np.array_equal(point,p['actions'][row['branch']]); first_count+=1
            else:
                expected_seed=int(np.random.SeedSequence([cfg['master_seed'],cfg['source_methods'].index(p['method']),p['rep'],row['step']]).generate_state(1)[0])
                assert row['pool_seed']==expected_seed
                pool=qmc.Sobol(19,scramble=True,seed=expected_seed).random_base2(cfg['pool_power'])
                observed={x.tobytes() for x in X}; pool=np.array([x for x in pool if x.tobytes() not in observed])
                assert sha(pool.tobytes())==row['pool_sha256']
                mu,sd=gp.predict(pool,return_std=True); index=int(np.argmin(mu))
                assert index==row['pool_index'] and np.array_equal(point,pool[index])
                checks['common_rule_seed_pool_action_checks']+=1
            mu,sd=gp.predict(point[None],return_std=True)
            assert np.allclose([mu[0],sd[0]],[row['mu'],row['sd']],rtol=1e-8,atol=1e-8)
            checks['past_only_gp_prediction_replays']+=1; pending=row
        elif event=='label':
            assert pending and (row['state'],row['branch'],row['step'])==(pending['state'],pending['branch'],pending['step'])
            key=row['state'],row['branch']; X,y=histories[key]
            X=np.vstack((X,pending['x'])); y=np.append(y,row['y']); histories[key]=(X,y)
            curves.setdefault(key,[]).append(float(y.min()))
            physical+=row['origin']=='new_fe_attempt'; checks['pre_label_pairs']+=1; pending=None
    assert pending is None and len(state_order)==30 and len(histories)==76 and first_count==76
    assert physical==status['new_fe_attempts']==recovery['recovery_attempts']
    rows=[]; comparisons=[]; class_rows=[]; for_horizon=Counter(); gain_rows=[]
    for name in state_order:
        p=plans[name]; s=json.loads((out/'summaries'/(name+'.json')).read_text()); controls=s['control_curves']; initial=p['initial_best']
        for control,index in p['decisions'].items():
            assert curves[name,str(index)]==controls[control]
            assert len(curves[name,str(index)])==6
            checks['control_endpoint_curve_checks']+=1
        assert controls['mean']==controls['mean_common_shift']; checks['neutral_control_exact_equivalence']+=1
        for control in ['mean','ei','pi','lcb','mean_common_shift']:
            for horizon in cfg['report_horizons']:
                J=controls[control][horizon]; mean=controls['mean'][horizon]
                contrast=(mean-J)/initial
                rows.append({'state':name,'method':p['method'],'seed_block':p['rep'],'control':control,'horizon':horizon,
                             'initial_compliance':initial,'endpoint_compliance':J,
                             'incumbent_relative_gain_percent':100*(initial-J)/initial,
                             'old_scale_normalized_gain':max(0.,initial-J)/max(float(np.std(p['y'])),1e-12),
                             'relative_advantage_over_mean_percent':100*contrast,
                             'effect':effect_label(contrast,cfg['relative_effect_tolerance']),
                             'same_first_action_as_mean':p['decisions'][control]==p['decisions']['mean']})
                if control!='mean_common_shift': gain_rows.append(100*(initial-J)/initial)
        for control in ['ei','pi','lcb']:
            labels={h:effect_label((controls['mean'][h]-controls[control][h])/initial,cfg['relative_effect_tolerance']) for h in cfg['report_horizons']}
            class_rows.append({'state':name,'method':p['method'],'seed_block':p['rep'],'control':control,
                               'first_action_changed':p['decisions'][control]!=p['decisions']['mean'],
                               'immediate_effect':labels[0],'h5_effect':labels[5],
                               'classification_changed':labels[0]!=labels[5],
                               'immediate_tie_later_non_tie':labels[0]=='tie' and labels[5]!='tie'})
    for method in cfg['source_methods']:
        for control in ['ei','pi','lcb']:
            for horizon in [0,5]:
                group=[r for r in rows if r['method']==method and r['control']==control and r['horizon']==horizon]
                comparisons.append({'method':method,'control':control,'horizon':horizon,'states':len(group),
                                    'median_paired_advantage_percent':float(np.median([r['relative_advantage_over_mean_percent'] for r in group])),
                                    'better':sum(r['effect']=='better' for r in group),
                                    'tie':sum(r['effect']=='tie' for r in group),'worse':sum(r['effect']=='worse' for r in group)})
    sensitivity=[]
    for tol in [1e-6,1e-5,1e-4]:
        changes=0; delayed=0
        for name in state_order:
            p=plans[name]; s=json.loads((out/'summaries'/(name+'.json')).read_text()); c=s['control_curves']; initial=p['initial_best']
            for control in ['ei','pi','lcb']:
                a=effect_label((c['mean'][0]-c[control][0])/initial,tol)
                b=effect_label((c['mean'][5]-c[control][5])/initial,tol)
                changes+=a!=b; delayed+=a=='tie' and b!='tie'
        sensitivity.append({'relative_tolerance':tol,'classification_changes':changes,'immediate_ties_later_non_ties':delayed})
    report={'complete':True,'checks':dict(checks),'states':30,'seed_blocks':10,'distinct_first_actions':76,
            'four_real_control_choices':120,'choices_including_constructed_neutral':150,
            'state_control_contrasts':90,'contrasts_are_not_independent_samples':True,
            'classification_changes_h0_h5':sum(v['classification_changed'] for v in class_rows),
            'immediate_ties_later_non_ties':sum(v['immediate_tie_later_non_tie'] for v in class_rows),
            'comparisons':comparisons,'tolerance_sensitivity':sensitivity,'recovery':recovery,
            'new_fe_attempts_total':recovery['total_new_fe_attempts'],
            'logical_branch_response_requests':len(histories)*6,'retained_replay_new_attempts':physical,
            'prior_paid_first_responses':76,'continuation_response_requests':380,
            'first_execution_new_attempts':recovery['original_attempts'],
            'within_and_across_state_exact_reuses_in_first_execution':380-recovery['original_attempts'],
            'future_diagnostics_used_for_training':False,'confirmatory_pvalues_added':False,
            'superior_optimizer_claim_supported':False,'diagnostic_accuracy_against_published_algorithms_claimed':False}
    def save(name,value): (dest/name).write_text(json.dumps(value,indent=2)+'\n')
    save('analysis.json',report)
    for name,data in [('engineering_endpoints.csv',rows),('diagnostic_classifications.csv',class_rows)]:
        with (dest/name).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(data[0]),lineterminator='\n');w.writeheader();w.writerows(data)
    lines=['# Common-continuation measured evidence','','Author-review data record, not a drafted manuscript argument or novelty certification.','',
           'Thirty frozen states nested within ten seed blocks and three source optimizers. First actions alone vary; all branches then use the same posterior-mean continuation and external candidate seed rule. Horizons count additional steps after the first action. Positive advantages favor the named control over mean.','',
           '| Source history | First action | h0 better/tie/worse | h5 better/tie/worse | Median h5 advantage (%) |','|---|---|---|---|---:|']
    for method in cfg['source_methods']:
        for c in ['ei','pi','lcb']:
            a=next(v for v in comparisons if v['method']==method and v['control']==c and v['horizon']==0)
            b=next(v for v in comparisons if v['method']==method and v['control']==c and v['horizon']==5)
            lines.append(f"| {method} | {c} | {a['better']}/{a['tie']}/{a['worse']} | {b['better']}/{b['tie']}/{b['worse']} | {b['median_paired_advantage_percent']:.6f} |")
    lines += ['',f"Across 90 dependent state/control contrasts, {report['classification_changes_h0_h5']} classifications differ between h0 and h5; {report['immediate_ties_later_non_ties']} immediate ties become non-ties. These are descriptive counts, not 90 independent trials.",'',
              '| Relative tolerance | Changed classifications | Immediate tie to later non-tie |','|---:|---:|---:|']
    for s in sensitivity: lines.append(f"| {s['relative_tolerance']} | {s['classification_changes']} | {s['immediate_ties_later_non_ties']} |")
    lines += ['', '## Evidence and cost boundary','',
              '- The frozen GP prediction error/coverage record is identical across first-action policies. This tests information sufficiency, not superiority over all published diagnostic frameworks.',
              '- Neutral control exactly matches mean in all30 states; it is a constructed instrumentation invariant.',
              '- Common-continuation contrasts isolate a conditional first-action effect under the declared continuation; original whole-policy endpoints measure another estimand.',
              '- The audit reports measured outcomes from exhaustive branches; no blind prospective classification accuracy or universal causal inference is claimed.',
              '- Raw compliance and initial-incumbent-relative percentages are supplied with the fixed1e-6 discrete-model tie threshold. They do not certify physical improvement beyond model discretization error.',
              f"- Existing first-label responses are reused76 times. The first execution made273 new FE attempts and107 continuation cache reuses. Ledger recovery adds{recovery['recovery_attempts']} FE attempts; total paid new attempts{recovery['total_new_fe_attempts']}. Replay adds no sample; old timing bytes were not recovered.",
              '- Query sharing is exact deterministic duplicate-response avoidance. This does not demonstrate net deployment savings or performance-preserving strategy selection.',
              '- Retrospective source-selected calibration points are biased; no valid coverage guarantee or promotion use is implied.',
              '- Authors must independently assess contribution sufficiency and integrate scientific interpretation.']
    (dest/'EVIDENCE.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'checks':dict(checks),'classification_changes':report['classification_changes_h0_h5'],'delayed_non_ties':report['immediate_ties_later_non_ties'],'new_paid_attempts':report['new_fe_attempts_total']}))
if __name__=='__main__': main()
