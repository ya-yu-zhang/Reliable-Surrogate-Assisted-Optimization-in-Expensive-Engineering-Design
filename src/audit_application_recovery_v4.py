"""Audit second-interruption recoveries with bounded CMA state roundoff."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import numpy as np
from .recover_interrupted_application_run_v3 import equivalent as cma_equivalent
ROOT=Path(__file__).resolve().parents[1];ARCHIVE=ROOT/'results/application_interruption_20260922_v2/partial_runs';OUT=ROOT/'results/application_formal_v1'
RUNS=['cma_es_DNA_r08_b500','turbo_1_DNA_r04_b500','turbo_1_synt_simple_r07_b500']
def exact(a,b):
    a=dict(a);b=dict(b);a.pop('preparation_seconds',None);b.pop('preparation_seconds',None);return a==b
def main():
    first=json.loads((ROOT/'results/application_recovery_audit_v1/audit.json').read_text('utf-8'));assert first['complete'] and first['objective_calls_by_auditor']==0
    rows=[]
    for runid in RUNS:
        old=[json.loads(x) for x in (ARCHIVE/runid/'events.jsonl').read_text('utf-8').splitlines()];new=[json.loads(x) for x in (OUT/runid/'events.jsonl').read_text('utf-8').splitlines()]
        rec=json.loads((OUT/runid/'recovery.json').read_text('utf-8'));summary=json.loads((OUT/runid/'summary.json').read_text('utf-8'));paid=rec['old_paid_calls'];eq=cma_equivalent if runid.startswith('cma_es_') else exact
        assert len(new)==1001 and summary['algorithm_evaluations']==500 and new[0]==old[0]
        assert all(eq(a,b) for a,b in zip(new[1:1+2*paid],old[1:1+2*paid]));dangling=len(old)==2+2*paid
        if dangling:assert eq(new[1+2*paid],old[-1])
        physical=(OUT/runid/'recovery_physical_calls.jsonl').read_text('utf-8').splitlines();assert len(physical)==2*rec['new_paid_calls'] and summary['test_method_calls']==1
        rows.append({'runid':runid,'old_paid_calls':paid,'new_paid_calls':rec['new_paid_calls'],'prefix_equivalent':True,
          'cma_float_absolute_tolerance':2e-12 if runid.startswith('cma_es_') else 0,'journal_sha256':hashlib.sha256((OUT/runid/'events.jsonl').read_bytes()).hexdigest()})
    result={'schema':'application_recovery_audit_v4','complete':True,'objective_calls_by_auditor':0,'recovered_runs':3,
      'saved_paid_labels':sum(x['old_paid_calls'] for x in rows),'new_physical_calls':sum(x['new_paid_calls'] for x in rows),
      'canonical_evaluations':1500,'post_completion_test_calls':3,'prior_recovery_audit_preserved':True,'rows':rows}
    assert result['saved_paid_labels']==924 and result['new_physical_calls']==576
    target=ROOT/'results/application_recovery_audit_v4';target.mkdir(exist_ok=False);(target/'audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))
if __name__=='__main__':main()
