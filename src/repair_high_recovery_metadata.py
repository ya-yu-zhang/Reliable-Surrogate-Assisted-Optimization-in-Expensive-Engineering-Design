"""Reconstruct recovery records after a post-completion relative-path formatting error."""
import hashlib,json
from pathlib import Path
from .recover_interrupted_application_run_v3 import parse_paid_prefix,equivalent
ROOT=Path(__file__).resolve().parents[1]
EXPECTED={'gp_ei_synt_high_r10_b1000':895,'turbo_1_synt_high_r02_b1000':874,
          'turbo_1_synt_high_r03_b1000':954,'turbo_1_synt_high_r10_b1000':691}
def main():
    oldroot=ROOT/'results/application_high_interruption_20260922_v1/partial_runs'
    newroot=ROOT/'results/application_high_formal_v1'
    for runid,paid in EXPECTED.items():
        oldpath=oldroot/runid/'events.jsonl'; meta,pre,labels,dangling,raw=parse_paid_prefix(oldpath)
        assert len(labels)==paid and dangling is None
        directory=newroot/runid; rows=[json.loads(x) for x in (directory/'events.jsonl').read_text('utf-8').splitlines()]
        assert rows[0]==meta and len(rows)==2001
        old=[x for pair in zip(pre,labels) for x in pair]
        assert all(equivalent(a,b) for a,b in zip(rows[1:1+2*paid],old))
        physical=[json.loads(x) for x in (directory/'recovery_physical_calls.jsonl').read_text('utf-8').splitlines()]
        assert len(physical)==2*(1000-paid) and sum(x['event']=='label' for x in physical)==1000-paid
        summary=json.loads((directory/'summary.json').read_text('utf-8')); assert summary['test_method_calls']==1
        record={'schema':'high_paid_prefix_recovery_v1','runid':runid,
                'archive':(oldroot/runid).relative_to(ROOT).as_posix(),
                'original_journal_sha256':hashlib.sha256(raw).hexdigest(),'old_paid_calls':paid,
                'new_paid_calls':1000-paid,'complete_prefix_states_and_labels_numerically_equivalent':True,
                'candidate_absolute_tolerance':2e-12,'optimizer_state_float_absolute_tolerance':2e-12,
                'post_completion_test_calls':1,'objective_timing_scope':'new_suffix_only',
                'optimization_timing_scope':'full_deterministic_replay_plus_new_suffix',
                'record_reconstructed_after_post_completion_path_format_error':True}
        (directory/'recovery.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print(json.dumps({'recovery_records_reconstructed':4,'objective_calls':0,'prefix_calls_verified':3414,'suffix_calls_verified':586}))
if __name__=='__main__':main()
