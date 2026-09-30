"""One-use byte-preserving archive of the confirmed 2026-09-19 interruption."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'results/interruption_20260919_v2'
SOURCES=['src/recover_interrupted_run.py','src/resume_interrupted_gp_batch_v2.py',
         'src/archive_second_interruption.py','src/gp_references.py','src/run_gp_batch.py',
         'configs/turbo_reference.json','configs/gp_ei_reference.json','docs/baselines-environment-lock.txt',
         'tests/test_paid_prefix_recovery.py','tests/test_second_recovery_driver.py']
SOURCES += ['literature/source-code/TuRBO/turbo/'+name for name in ['turbo_1.py','gp.py','utils.py','__init__.py']]


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    DEST.mkdir(parents=True,exist_ok=True)
    assert not (DEST/'recovery_manifest.json').exists()
    rows=[];prior=json.loads((ROOT/'results/interruption_20260918_v1/recovery_manifest.json').read_text('utf-8'))
    prior_by_id={row['runid']:row for row in prior['partial_runs']}
    for source in ['turbo_reference_v1','gp_ei_reference_v1']:
        base=ROOT/'results'/source;archived=DEST/'partial_runs'/source
        candidates=[p for p in base.iterdir() if p.is_dir() and (p/'events.jsonl').exists() and not (p/'summary.json').exists()]
        if archived.exists():candidates += [p for p in archived.iterdir() if p.is_dir() and (p/'events.jsonl').exists()]
        for directory in sorted(candidates):
            events=[json.loads(v) for v in (directory/'events.jsonl').read_text('utf-8').splitlines()]
            assert events[0]['event']=='meta' and len(events)%2==1
            paid=(len(events)-1)//2
            assert paid and all(a['event']=='pre' and b['event']=='label' and a['t']==b['t']==i
                for i,(a,b) in enumerate(zip(events[1::2],events[2::2]),1))
            chain=None
            if directory.name in prior_by_id:
                oldrow=prior_by_id[directory.name];old=ROOT/oldrow['archive']/'events.jsonl'
                oldevents=[json.loads(v) for v in old.read_text('utf-8').splitlines()]
                compare=min(oldrow['paid_labels'],paid)
                for a,b in zip(events[1:1+2*compare],oldevents[1:1+2*compare]):
                    a=dict(a);b=dict(b);a.pop('preparation_seconds',None);b.pop('preparation_seconds',None);assert a==b
                physical=directory/'recovery_physical_calls.jsonl'
                lines=physical.read_text('utf-8').splitlines() if physical.exists() else []
                assert len(lines)==2*max(0,paid-oldrow['paid_labels'])
                chain=dict(prior_archive=oldrow['archive'],prior_paid_labels=oldrow['paid_labels'],
                           newly_paid_labels=max(0,paid-oldrow['paid_labels']),prior_prefix_equal=True,
                           physical_log_sha256=digest(physical) if physical.exists() else None)
            target=DEST/'partial_runs'/source/directory.name
            target.parent.mkdir(parents=True,exist_ok=True)
            source_resolved=directory.resolve();target_resolved=target.resolve()
            assert source_resolved.is_relative_to(ROOT.resolve()) and target_resolved.is_relative_to(DEST.resolve())
            files={p.relative_to(directory).as_posix():digest(p) for p in directory.rglob('*') if p.is_file()}
            if source_resolved != target_resolved:
                assert not target.exists();shutil.move(str(source_resolved),str(target_resolved))
            assert all(digest(target/name)==value for name,value in files.items())
            rows.append(dict(source=source,runid=directory.name,paid_labels=paid,pending_pre=0,
                             archive=target.relative_to(ROOT).as_posix(),file_sha256=files,recovery_chain=chain))
    assert len(rows)==8 and sum(r['paid_labels'] for r in rows)==2014
    states=DEST/'old_states';states.mkdir(exist_ok=True)
    for name in ['turbo_reference_v1','gp_ei_reference_v1','reference_completion_v1','application_completion_v1','evidence_export_v1']:
        folder=ROOT/'results'/name;target=states/name;target.mkdir(exist_ok=True)
        for field in ['status.json','failures.json']:
            if (folder/field).exists():shutil.copy2(folder/field,target/field)
    source_hashes={name:digest(ROOT/name) for name in SOURCES}
    freeze=DEST/'source_freeze'
    for name in SOURCES:
        target=freeze/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
    result=dict(interruption_date='2026-09-19',partial_runs=rows,
                complete_runs_before_interruption={'turbo_reference_v1':277,'gp_ei_reference_v1':71},
                old_paid_calls=sum(r['paid_labels'] for r in rows),all_pre_label_pairs_complete=True,
                no_pending_physical_return=True,unchanged_budgets_and_scope=True,selective_outcome_reruns=False,
                recovery_sources=source_hashes)
    (DEST/'recovery_manifest.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['complete_runs_before_interruption','old_paid_calls','all_pre_label_pairs_complete']},indent=2))


if __name__=='__main__':main()
