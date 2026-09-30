"""Audit the four recovered formal runs and their physical suffix accounting."""
import json,hashlib
from pathlib import Path
from .application_high_journal_audit_safe import audit_high_journal
ROOT=Path(__file__).resolve().parents[1]
EXPECTED={'gp_ei_synt_high_r10_b1000':895,'turbo_1_synt_high_r02_b1000':874,
          'turbo_1_synt_high_r03_b1000':954,'turbo_1_synt_high_r10_b1000':691}
def main():
    out=ROOT/'results/application_high_formal_v1'; total_new=0
    for runid,old in EXPECTED.items():
        d=out/runid; record=json.loads((d/'recovery.json').read_text('utf-8')); summary=json.loads((d/'summary.json').read_text('utf-8'))
        assert record['old_paid_calls']==old and record['new_paid_calls']==1000-old
        rows=[json.loads(x) for x in (d/'recovery_physical_calls.jsonl').read_text('utf-8').splitlines()]
        assert len(rows)==2*(1000-old) and sum(x['event']=='label' for x in rows)==1000-old
        assert record['complete_prefix_states_and_labels_numerically_equivalent'] and record['post_completion_test_calls']==1
        audit_high_journal(d,summary); total_new+=1000-old
    result={'schema':'high_formal_recovery_audit_v1','runs':4,'old_paid_calls':sum(EXPECTED.values()),
            'new_physical_paid_calls':total_new,'canonical_algorithm_evaluations':4000,
            'test_method_calls':4,'prefixes_numerically_equivalent':True,'journals_valid':True,
            'auditor_objective_calls':0,'recovery_source_sha256':hashlib.sha256((ROOT/'src/recover_interrupted_high_run.py').read_bytes()).hexdigest()}
    target=ROOT/'results/application_high_recovery_audit_v1';target.mkdir(exist_ok=True)
    (target/'audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
