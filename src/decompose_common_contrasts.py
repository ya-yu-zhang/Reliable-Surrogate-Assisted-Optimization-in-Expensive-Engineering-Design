"""Supplement original named contrasts with exact-action denominators.

Original reported estimands/counts remain intact. No solver, p-value or filtering
on favorable outcomes. Utilities never define equivalence classes.
"""
import csv,json
from collections import Counter
from .engineering_optimization_common_continuation import ROOT,CONFIG,sha,effect_label

def main():
    cfg=json.loads(CONFIG.read_text());out=ROOT/cfg['out']
    manifest=json.loads((out/'manifest.json').read_text());rows=[];nominal=[]
    for item in manifest['plans']:
        raw=(out/item['path']).read_bytes();assert sha(raw)==item['sha256'];p=json.loads(raw)
        s=json.loads((out/'summaries'/(p['state']+'.json')).read_text())
        baseline=p['decisions']['mean'];curves=s['control_curves'];seen=set()
        for control in ['ei','pi','lcb']:
            action=p['decisions'][control]
            labels=[effect_label((curves['mean'][h]-curves[control][h])/p['initial_best'],cfg['relative_effect_tolerance']) for h in [0,5]]
            row={'state':p['state'],'source':p['method'],'seed_block':p['rep'],
                 'control':control,'first_action_class':action,'same_as_mean':action==baseline,
                 'immediate_effect':labels[0],'h5_effect':labels[1],
                 'classification_changed':labels[0]!=labels[1],
                 'immediate_tie_later_non_tie':labels[0]=='tie' and labels[1]!='tie'}
            nominal.append(row)
            if action!=baseline and action not in seen:rows.append(row);seen.add(action)
    report={'original_named_contrasts':len(nominal),'structural_alias_contrasts':sum(r['same_as_mean'] for r in nominal),
            'different_action_named_contrasts':sum(not r['same_as_mean'] for r in nominal),
            'distinct_nonbaseline_action_contrasts':len(rows),
            'named_classification_changes':sum(r['classification_changed'] for r in nominal),
            'distinct_action_classification_changes':sum(r['classification_changed'] for r in rows),
            'named_delayed_non_ties':sum(r['immediate_tie_later_non_tie'] for r in nominal),
            'distinct_action_delayed_non_ties':sum(r['immediate_tie_later_non_tie'] for r in rows),
            'changed_states':sorted({r['state'] for r in rows if r['classification_changed']}),
            'changed_seed_blocks':sorted({r['seed_block'] for r in rows if r['classification_changed']}),
            'distinct_action_h5_counts':dict(Counter(r['h5_effect'] for r in rows)),
            'independent_replication_unit':'ten shared seed blocks; not named or action contrasts',
            'original_primary_denominator_changed':False,'new_physics_attempts':0}
    assert (len(nominal),report['structural_alias_contrasts'],len(rows))==(90,34,46)
    dest=ROOT/'paper/engineering_optimization/common_continuation'
    (dest/'denominator_analysis.json').write_text(json.dumps(report,indent=2)+'\n')
    with (dest/'distinct_action_contrasts.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
    print(json.dumps(report))
if __name__=='__main__':main()
