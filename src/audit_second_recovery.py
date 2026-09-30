"""Read-only two-generation recovery audit, including redundant physical calls."""
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def events(path):return [json.loads(v) for v in path.read_text('utf-8').splitlines()]


def equal(a,b):
    a=dict(a);b=dict(b);a.pop('preparation_seconds',None);b.pop('preparation_seconds',None);return a==b


def main():
    first=json.loads((ROOT/'results/interruption_20260918_v1/recovery_manifest.json').read_text('utf-8'))
    prior={r['runid']:r for r in first['partial_runs']}
    second_path=ROOT/'results/interruption_20260919_v2/recovery_manifest.json';second=json.loads(second_path.read_text('utf-8'))
    assert len(second['partial_runs'])==8 and second['old_paid_calls']==2014
    for name,value in second['recovery_sources'].items():assert digest(ROOT/name)==value
    rows=[];redundant=0
    for row in second['partial_runs']:
        archive=ROOT/row['archive'];current=ROOT/'results'/row['source']/row['runid']
        for name,value in row['file_sha256'].items():assert digest(archive/name)==value
        recovery=json.loads((current/'recovery.json').read_text('utf-8'))
        assert recovery['old_paid_calls']==row['paid_labels'] and recovery['old_paid_calls']+recovery['new_paid_calls']==recovery['physical_total']
        assert recovery['complete_prefix_states_and_labels_equal'] and recovery['optimizer_source_unchanged']
        old=events(archive/'events.jsonl');full=events(current/'events.jsonl');assert len(full)==1+2*recovery['physical_total']
        assert all(equal(a,b) for a,b in zip(old,full[:len(old)]))
        physical=events(current/'recovery_physical_calls.jsonl');assert len(physical)==2*recovery['new_paid_calls']
        for j,(pre,label) in enumerate(zip(physical[::2],physical[1::2]),row['paid_labels']+1):
            assert pre['event']=='pre' and label['event']=='label' and pre['t']==label['t']==j
            assert pre['x']==full[2*j-1]['x'] and label['y']==full[2*j]['y']
        earlier=prior.get(row['runid']);overlap=0
        if earlier:
            earliest=events(ROOT/earlier['archive']/'events.jsonl');common=min(earlier['paid_labels'],row['paid_labels'])
            assert all(equal(a,b) for a,b in zip(earliest[1:1+2*common],old[1:1+2*common]))
            overlap=max(0,earlier['paid_labels']-row['paid_labels'])
            if overlap:
                assert overlap==1
                t=row['paid_labels']+1
                assert equal(earliest[2*t-1],full[2*t-1]) and equal(earliest[2*t],full[2*t])
                assert physical[0]['t']==physical[1]['t']==t and physical[0]['x']==earliest[2*t-1]['x']
                assert physical[1]['y']==earliest[2*t]['y']
            redundant+=overlap
        summary=json.loads((current/'summary.json').read_text('utf-8'))
        assert summary['algorithm_evaluations']==recovery['physical_total']
        rows.append(dict(runid=row['runid'],source=row['source'],canonical_algorithm_evaluations=recovery['physical_total'],
            second_archive_labels=row['paid_labels'],second_new_physical_calls=recovery['new_paid_calls'],
            redundant_recovery_validation_calls=overlap,canonical_pre_label_pairs_verified=True,
            final_journal_sha256=digest(current/'events.jsonl'),final_summary_sha256=digest(current/'summary.json'),
            second_physical_log_sha256=digest(current/'recovery_physical_calls.jsonl'),
            recovery_sidecar_sha256=digest(current/'recovery.json')))
    assert redundant==1 and sum(r['canonical_algorithm_evaluations'] for r in rows)==2800
    result=dict(objective_calls_by_this_auditor=0,recovered_runs=8,canonical_algorithm_evaluations=2800,
        second_generation_saved_labels=2014,second_generation_new_physical_calls=sum(r['second_new_physical_calls'] for r in rows),
        redundant_recovery_validation_calls=redundant,redundant_call_entered_optimizer_history=False,
        redundant_point_and_label_exactly_equal_to_first_archive=True,all_canonical_trajectories_complete=True,
        recovery_elapsed_excluded_from_exclusive_cost_analysis=True,runs=rows)
    out=ROOT/'results/interruption_20260919_v2/second_recovery_audit.json';out.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='runs'},indent=2))


if __name__=='__main__':main()
