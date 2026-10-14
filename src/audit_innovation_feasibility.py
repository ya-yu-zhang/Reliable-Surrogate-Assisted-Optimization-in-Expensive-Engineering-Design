"""Screen innovation assumptions on complete frozen records, without new labels.

The proposed loss-only certificate is assessed under nonnegative, monotone
terminal intervals. It makes no claim about GP/model reachability or PDE error.
Learning-curve checks are descriptive and do not test stochastic expectations.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

BASELINE = '58f539c2d0738b20c7d0d4889fe8d808a03a3019'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def datasets(root):
    results = root/'results'
    common=results/'engineering_optimization_common_continuation_v1'
    rows=[]
    for path in sorted((common/'summaries').glob('*.json')):
        s=json.loads(path.read_text());assert s['complete']
        p=json.loads((common/'plans'/(s['state']+'.json')).read_text())
        classes={str(k):[n for n in names if n in ['mean','ei','pi','lcb']]
                 for k,names in s['decision_classes'].items()}
        assert all(classes.values())
        curves={k:list(s['control_curves'][names[0]]) for k,names in classes.items()}
        for k,names in classes.items():
            assert all(s['control_curves'][n]==curves[k] for n in names)
        rows.append({'dataset':'archived_common','continuation':'mean','state':s['state'],
                     'block':int(s['rep']),'initial':float(s['initial_best']),'margin':1e-6,
                     'classes':classes,'baseline':str(s['decisions']['mean']),'curves':curves,
                     'source_path':str(path),'source_sha256':digest(path)})
    budget=results/'engineering_optimization_budget_audit_v1'
    for path in sorted(budget.glob('block_*/*_summary.json')):
        s=json.loads(path.read_text());assert s['complete']
        for continuation,trajectories in s['trajectories'].items():
            curves={k:[float(r['incumbent']) for r in records] for k,records in trajectories.items()}
            rows.append({'dataset':'previous_holdout','continuation':continuation,'state':s['state'],
                         'block':int(s['block']),'initial':float(s['initial_best']),'margin':.001,
                         'classes':s['classes'],'baseline':s['mapping']['mean'],'curves':curves,
                         'source_path':str(path),'source_sha256':digest(path)})
    assert len(rows)==90 and len({(r['dataset'],r['state']) for r in rows})==60
    return rows


def verify_archives(baseline, restored):
    checked={}
    for folder in ['engineering_optimization_budget_audit_v1','engineering_optimization_common_continuation_v1']:
        path=baseline/'data'/folder/'manifest.json';manifest=json.loads(path.read_text())
        for item in manifest['files']:
            p=restored/item['path'];assert p.stat().st_size==item['bytes'];assert digest(p)==item['sha256']
            checked[item['path']]=item['sha256']
    return checked


def candidate_interval_regret(upper, lower, chosen):
    """Tight worst-case chosen-arm loss for independent terminal intervals."""
    other=[v for k,v in lower.items() if k!=chosen]
    return max(0.,upper[chosen]-min(other)) if other else 0.


def run(baseline, restored, output):
    receipt=verify_archives(baseline,restored)
    records=datasets(restored);state_rows=[];curve_rows=[];witnesses=[]
    grouped=defaultdict(list)
    for r in records:
        scale=r['initial'];assert scale>0
        k=len(r['classes']);assert set(r['curves'])==set(r['classes'])
        violations=0;smallest=float('inf')
        for branch,curve in r['curves'].items():
            assert len(curve)==6 and all(v>0 for v in curve)
            extended=[scale]+curve
            increments=[(a-b)/scale for a,b in zip(extended,extended[1:])]
            assert all(v>=-1e-12 for v in increments)
            jumps=[i for i in range(5) if increments[i+1]>increments[i]+1e-12]
            violations+=bool(jumps);smallest=min(smallest,curve[-1]/scale)
            cr={'dataset':r['dataset'],'continuation':r['continuation'],'state':r['state'],
                'block':r['block'],'branch':branch,'names':'/'.join(r['classes'][branch]),
                'diminishing_returns_violated':bool(jumps),'violation_count':len(jumps),
                'largest_upward_increment_jump_fraction':max([0.]+[increments[i+1]-increments[i] for i in range(5)]),
                'terminal_incumbent_over_initial':curve[-1]/scale}
            curve_rows.append(cr)
            if jumps:
                witnesses.append({**cr,'initial':scale,'incumbent_h0_to_h5':curve,
                                  'gain_increment_fractions':increments,'source_sha256':r['source_sha256']})
        # Any observed prefix incumbent is >= its terminal value. A positive
        # unfinished competitor has interval lower=0. If every possible chosen
        # prefix upper > tau*initial, it cannot rule that competitor out.
        condition=smallest>r['margin']
        assert condition
        better=[]
        b=r['curves'][r['baseline']][-1]
        for branch,curve in r['curves'].items():
            if branch!=r['baseline'] and (b-curve[-1])/scale>r['margin']:better.append(branch)
        # All one-open-competitor frontiers at every stored chosen prefix fail
        # the loss-only interval certificate; complete terminal truth grades
        # these frontiers only after the mathematical interval check.
        checks=0
        if k>1:
            for chosen,curve in r['curves'].items():
                for h in range(6):
                    for other in r['curves']:
                        if other==chosen:continue
                        upper={name:values[-1] for name,values in r['curves'].items()}
                        lower=dict(upper);upper[chosen]=curve[h];lower[other]=0.
                        worst=candidate_interval_regret(upper,lower,chosen)
                        assert worst/scale>r['margin'];checks+=1
        sr={'dataset':r['dataset'],'continuation':r['continuation'],'state':r['state'],'block':r['block'],
            'margin':r['margin'],'classes':k,'alias_only':k==1,'branches':k,
            'branches_violating_diminishing_returns':violations,
            'minimum_terminal_over_initial':smallest,'zero_lower_loss_only_condition':condition,
            'all_selection_plus_execution_request_requirement':6*k,
            'one_open_competitor_frontiers_checked':checks,
            'better_distinct_branches':len(better),'state_with_better_branch':bool(better)}
        state_rows.append(sr);grouped[r['dataset'],r['continuation']].append(sr)
    summaries=[]
    for (dataset,continuation),rows in grouped.items():
        assert len(rows)==30 and len({x['block'] for x in rows})==10
        curves=[x for x in curve_rows if (x['dataset'],x['continuation'])==(dataset,continuation)]
        summary={'dataset':dataset,'continuation':continuation,'metadata_states':30,'all_seed_groups':10,
                 'nonalias_states':sum(not x['alias_only'] for x in rows),'alias_states':sum(x['alias_only'] for x in rows),
                 'distinct_branch_curves':len(curves),
                 'curves_violating_diminishing_returns':sum(x['diminishing_returns_violated'] for x in curves),
                 'states_with_a_diminishing_returns_violation':sum(x['branches_violating_diminishing_returns']>0 for x in rows),
                 'nonalias_states_with_zero_lower_loss_only_barrier':sum(not x['alias_only'] and x['zero_lower_loss_only_condition'] for x in rows),
                 'all_selection_plus_execution_request_requirement':sum(x['all_selection_plus_execution_request_requirement'] for x in rows),
                 'minimum_terminal_over_initial':min(x['minimum_terminal_over_initial'] for x in rows),
                 'one_open_competitor_frontiers_checked':sum(x['one_open_competitor_frontiers_checked'] for x in rows),
                 'better_distinct_branches':sum(x['better_distinct_branches'] for x in rows),
                 'states_with_better_branch':sum(x['state_with_better_branch'] for x in rows)}
        summaries.append(summary)
    m=json.loads((baseline/'paper/engineering_optimization/monotone_development_20261013/analysis.json').read_text())
    reconciled=[]
    specs=[('archived_common_mean','mean',18,n) for n in ['v1_fixed_depth','h0_largest_upper','alternative_depth']]
    for c in ['mean','ei']:
        specs += [('previous_holdout',c,18,n) for n in ['v1_fixed_depth','h0_largest_upper','alternative_depth']]
        specs += [('previous_holdout',c,12,n) for n in ['v1_fixed_depth','h0_largest_upper']]
    for dataset,c,budget,name in specs:
        cells=[x for x in m['primary']+m['sensitivity'] if
               (x['dataset'],x['continuation'],x['budget'],x['method'],x['target'])==(dataset,c,budget,name,'categories_and_selection')]
        assert cells and all(x==cells[0] for x in cells)
        x=cells[0];alias=x['alias_only_selected_execution_requests'];completion=x['selected_completion_requests']-alias
        assert x['requests']+completion+alias==x['audit_plus_selected_completion_requests']
        reconciled.append({'dataset':dataset,'continuation':c,'budget':budget,'reader':name,
                           'classified':x['classified'],'contrasts':x['contrasts'],'audit':x['requests'],
                           'chosen_nonalias_completion':completion,'alias_execution':alias,
                           'total_all_states':x['audit_plus_selected_completion_requests'],
                           'certified_nonalias_selection':x['certified_nontrivial_selection'],
                           'nonalias_states':x['nontrivial_state']})
    report={'baseline_commit':BASELINE,'analysis_type':'posthoc descriptive innovation-feasibility screen',
            'new_physics_attempts':0,'new_bounds':0,'new_gp_fits':0,'new_independent_samples':0,
            'new_confirmatory_families':0,'retained_metadata_states':60,'dependent_contexts':90,
            'restored_hash_verified_files':len(receipt),'source_file_sha256':receipt,
            'information_scope':'independent branch terminal intervals, nonnegative responses and monotone incumbents; no GP-reachability or shared-response inference',
            'shape_scope':'observed deterministic curves; not stochastic expected-loss or polynomial-model falsification',
            'novelty_certified':False,'independent_study_gate':False,'submission_ready':False,
            'summaries':summaries,
            'candidate_decisions':{
              'diminishing_returns_envelope':'not valid as an exact envelope for all observed branch curves; empirical stochastic models would require separately validated assumptions',
              'loss_only_zero_lower_certificate':'does not reduce all-state certified selection plus execution requirements under the declared information model',
              'current_monotone_schedule':'no complete-cost/quality increment over strong simple fixed depth in existing records'},
            'all_primary_margins_and_labels_unchanged':True}
    output.mkdir(parents=True,exist_ok=True)
    (output/'innovation_feasibility.json').write_text(json.dumps(report,indent=2)+'\n')
    for name,rows in [('state_results.csv',state_rows),('curve_shape_results.csv',curve_rows),
                      ('development_cost_reconciliation.csv',reconciled),('summary.csv',summaries)]:
        with (output/name).open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
    (output/'shape_counterexamples.json').write_text(json.dumps(witnesses,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='source_file_sha256'},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--restored',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();run(a.baseline,a.restored,a.out)
