"""Audit exact TuRBO recovery and the clean CMA replacement."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ARCHIVE=ROOT/'results/application_interruption_20260922_v2/partial_runs';OUT=ROOT/'results/application_formal_v1'
TURBO=['turbo_1_DNA_r04_b500','turbo_1_synt_simple_r07_b500'];CMA='cma_es_DNA_r08_b500'
def comparable(e):r=dict(e);r.pop('preparation_seconds',None);return r
def main():
    first=json.loads((ROOT/'results/application_recovery_audit_v1/audit.json').read_text('utf-8'));assert first['complete'] and first['objective_calls_by_auditor']==0
    rows=[]
    for runid in TURBO:
        old=[json.loads(x) for x in (ARCHIVE/runid/'events.jsonl').read_text('utf-8').splitlines()];new=[json.loads(x) for x in (OUT/runid/'events.jsonl').read_text('utf-8').splitlines()];rec=json.loads((OUT/runid/'recovery.json').read_text('utf-8'));summary=json.loads((OUT/runid/'summary.json').read_text('utf-8'));paid=rec['old_paid_calls']
        assert len(new)==1001 and summary['algorithm_evaluations']==500 and new[0]==old[0] and all(comparable(a)==comparable(b) for a,b in zip(new[1:1+2*paid],old[1:1+2*paid]))
        physical=(OUT/runid/'recovery_physical_calls.jsonl').read_text('utf-8').splitlines();assert len(physical)==2*rec['new_paid_calls'] and summary['test_method_calls']==1
        rows.append({'runid':runid,'mode':'exact_paid_prefix_replay','old_paid_calls':paid,'new_physical_calls':rec['new_paid_calls'],'prefix_equal':True,'journal_sha256':hashlib.sha256((OUT/runid/'events.jsonl').read_bytes()).hexdigest()})
    old_cma=[json.loads(x) for x in (ARCHIVE/CMA/'events.jsonl').read_text('utf-8').splitlines()];new_cma=[json.loads(x) for x in (OUT/CMA/'events.jsonl').read_text('utf-8').splitlines()];summary=json.loads((OUT/CMA/'summary.json').read_text('utf-8'))
    assert len([x for x in old_cma if x['event']=='label'])==227 and len(new_cma)==1001 and summary['algorithm_evaluations']==500 and summary['test_method_calls']==1
    assert not (OUT/CMA/'recovery.json').exists() and not (OUT/CMA/'recovery_physical_calls.jsonl').exists()
    result={'schema':'application_recovery_audit_v5','complete':True,'objective_calls_by_auditor':0,'exact_recovered_runs':2,'clean_replacement_runs':1,
      'replayed_paid_labels':sum(x['old_paid_calls'] for x in rows),'tuRBO_new_suffix_calls':sum(x['new_physical_calls'] for x in rows),
      'abandoned_cma_paid_calls':227,'clean_cma_replacement_calls':500,'new_physical_calls_after_interruption':803,
      'total_physical_calls_including_interrupted_prefix':1727,'canonical_evaluations':1500,'redundant_physical_calls_due_to_interruption':227,
      'post_completion_test_calls':3,'prior_recovery_audit_preserved':True,'rows':rows,
      'cma_replacement_journal_sha256':hashlib.sha256((OUT/CMA/'events.jsonl').read_bytes()).hexdigest()}
    assert result['replayed_paid_labels']==697 and result['tuRBO_new_suffix_calls']==303
    target=ROOT/'results/application_recovery_audit_v5';target.mkdir(exist_ok=False);(target/'audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k not in {'rows'}},indent=2))
if __name__=='__main__':main()
