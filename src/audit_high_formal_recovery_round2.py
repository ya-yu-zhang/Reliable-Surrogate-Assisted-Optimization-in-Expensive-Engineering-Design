"""Audit the three second-interruption recoveries."""
import json
from pathlib import Path
from .application_high_journal_audit_safe import audit_high_journal
ROOT=Path(__file__).resolve().parents[1]
EXPECTED={'gp_ei_synt_high_r03_b1000':920,'turbo_1_synt_high_r04_b1000':650,'turbo_1_synt_high_r14_b1000':707}
def main():
    out=ROOT/'results/application_high_formal_v1';new=0
    for runid,old in EXPECTED.items():
        d=out/runid;r=json.loads((d/'recovery.json').read_text('utf-8'));s=json.loads((d/'summary.json').read_text('utf-8'))
        assert r['old_paid_calls']==old and r['new_paid_calls']==1000-old and r['complete_prefix_states_and_labels_numerically_equivalent']
        rows=[json.loads(x) for x in (d/'recovery_physical_calls.jsonl').read_text('utf-8').splitlines()]
        assert len(rows)==2*(1000-old) and sum(x['event']=='label' for x in rows)==1000-old
        assert r['post_completion_test_calls']==1;audit_high_journal(d,s);new+=1000-old
    result={'schema':'high_formal_recovery_audit_v2','runs':3,'old_paid_calls':sum(EXPECTED.values()),
            'new_physical_paid_calls':new,'canonical_algorithm_evaluations':3000,'test_method_calls':3,
            'prefixes_numerically_equivalent':True,'journals_valid':True,'auditor_objective_calls':0}
    target=ROOT/'results/application_high_recovery_audit_v2';target.mkdir(exist_ok=True)
    (target/'audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
