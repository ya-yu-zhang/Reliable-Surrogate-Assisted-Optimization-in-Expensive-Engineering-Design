"""Archive the second external interruption at 146/160 formal runs."""
import hashlib,json,shutil
from pathlib import Path
from .run_application_high_formal import prerequisite
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/application_high_formal_v1'
ARCH=ROOT/'results/application_high_interruption_20260923_v2'
EXPECTED={'gp_ei_synt_high_r03_b1000':920,'turbo_1_synt_high_r04_b1000':650,'turbo_1_synt_high_r14_b1000':707}
def paid(path):
    rows=[json.loads(x) for x in path.read_text('utf-8').splitlines()]; assert rows[0]['event']=='meta'
    payload=rows[1:];assert len(payload)%2==0
    assert all(a['event']=='pre' and b['event']=='label' and a['t']==b['t']==i for i,(a,b) in enumerate(zip(payload[0::2],payload[1::2]),1))
    return len(payload)//2
def main():
    prerequisite();assert not ARCH.exists()
    complete=[p for p in OUT.iterdir() if p.is_dir() and (p/'summary.json').exists()]
    partial={p.name:p for p in OUT.iterdir() if p.is_dir() and not (p/'summary.json').exists()}
    assert len(complete)==146 and set(partial)==set(EXPECTED)
    assert {n:paid(p/'events.jsonl') for n,p in partial.items()}==EXPECTED
    (ARCH/'partial_runs').mkdir(parents=True)
    for n,p in partial.items():shutil.move(str(p),str(ARCH/'partial_runs'/n))
    for n in ['status.json','failures.json']:
        p=OUT/n
        if p.exists():shutil.move(str(p),str(ARCH/('old_'+n)))
    stale=ROOT/'results/high_extension_completion_v1'
    if stale.exists():shutil.move(str(stale),str(ARCH/'stale_completion_state'))
    logs=ARCH/'launcher_logs';logs.mkdir()
    for n in ['twentyfifth_high_continuation_stdout.log','twentyfifth_high_continuation_stderr.log']:
        p=ROOT/'results'/n
        if p.exists():shutil.move(str(p),str(logs/n))
    files={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in ARCH.rglob('*') if p.is_file()}
    result={'schema':'high_formal_interruption_archive_v2','complete_runs_retained':146,'partial_paid_calls':EXPECTED,
            'saved_paid_labels':sum(EXPECTED.values()),'required_new_suffix_calls':3000-sum(EXPECTED.values()),
            'dangling_unpaid_pre':0,'failures_before_interruption':0,'files':files}
    (ARCH/'archive_manifest.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
