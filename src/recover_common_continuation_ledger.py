"""Explicit cache-aware replay; no science parameter, seed or threshold changes."""
import hashlib,json,shutil
from pathlib import Path
import numpy as np
from . import engineering_optimization_common_continuation as experiment

def main():
    cfg=json.loads(experiment.CONFIG.read_text()); out=experiment.ROOT/cfg['out']
    archive=experiment.ROOT/'results/engineering_optimization_common_continuation_recovery'
    if archive.exists(): raise FileExistsError('Recovery already attempted')
    archive.mkdir()
    for name in ['events.jsonl','run_status.json','summaries']:
        source=out/name; destination=archive/name
        if source.is_dir(): shutil.copytree(source,destination)
        else: shutil.copy2(source,destination)
    original_status=json.loads((archive/'run_status.json').read_text())
    b=(archive/'events.jsonl').read_bytes()
    assert hashlib.sha256(b).hexdigest()!=original_status['journal_sha256']
    original_cache=experiment.diagnostic_cache; cache=original_cache(); pending=None; pairs=0
    for line in b.splitlines():
        row=json.loads(line)
        if row['event']=='pre': pending=row
        elif row['event']=='label':
            assert pending and (pending['state'],pending['branch'],pending['step'])==(row['state'],row['branch'],row['step'])
            key=np.asarray(pending['x'],dtype='<f8').tobytes().hex()
            if key in cache: assert cache[key]==row['y']
            cache[key]=row['y']; pending=None; pairs+=1
    experiment.diagnostic_cache=lambda:dict(cache)
    (out/'events.jsonl').rename(archive/'moved_original_events.jsonl')
    experiment.run()
    status=json.loads((out/'run_status.json').read_text())
    raw=(out/'events.jsonl').read_bytes(); assert hashlib.sha256(raw).hexdigest()==status['journal_sha256']
    matches=0
    fields=['state','method','rep','initial_best','decision_classes','decisions','control_curves','retrospective_prediction_diagnostics']
    for path in sorted((out/'summaries').glob('*.json')):
        new=json.loads(path.read_text()); old=json.loads((archive/'summaries'/path.name).read_text())
        for field in fields: assert new[field]==old[field],(path.name,field)
        matches+=1
    assert matches==30
    total=original_status['new_fe_attempts']+status['new_fe_attempts']; assert total<=cfg['max_new_fe_attempts']
    report={'original_attempts':original_status['new_fe_attempts'],'recovery_attempts':status['new_fe_attempts'],
            'total_new_fe_attempts':total,'science_summaries_exactly_reproduced':matches,
            'complete_original_pairs_reused':pairs,'extra_independent_samples':0,
            'original_expected_journal_sha256':original_status['journal_sha256'],
            'damaged_journal_sha256':hashlib.sha256(b).hexdigest(),'retained_journal_sha256':status['journal_sha256'],
            'original_timing_bytes_recovered':False,'wrapper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    experiment.write(out/'recovery_accounting.json',report)
    print(json.dumps(report))
if __name__=='__main__': main()
