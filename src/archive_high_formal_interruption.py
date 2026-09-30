"""Archive the externally interrupted high-dimensional runs without discarding paid labels."""
from __future__ import annotations
import hashlib,json,shutil
from pathlib import Path
from .run_application_high_formal import prerequisite

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/application_high_formal_v1'
ARCHIVE=ROOT/'results/application_high_interruption_20260922_v1'
EXPECTED={'gp_ei_synt_high_r10_b1000':895,'turbo_1_synt_high_r02_b1000':874,
          'turbo_1_synt_high_r03_b1000':954,'turbo_1_synt_high_r10_b1000':691}

def count_paid(path):
    rows=[json.loads(x) for x in path.read_text('utf-8').splitlines()]
    assert rows[0]['event']=='meta'; payload=rows[1:]
    assert len(payload)%2==0
    assert all(a['event']=='pre' and b['event']=='label' and a['t']==b['t']==i
               for i,(a,b) in enumerate(zip(payload[0::2],payload[1::2]),1))
    return len(payload)//2

def main():
    prerequisite()
    assert not ARCHIVE.exists()
    complete=[p for p in OUT.iterdir() if p.is_dir() and (p/'summary.json').exists()]
    partial={p.name:p for p in OUT.iterdir() if p.is_dir() and not (p/'summary.json').exists()}
    assert len(complete)==107 and set(partial)==set(EXPECTED)
    assert {n:count_paid(p/'events.jsonl') for n,p in partial.items()}==EXPECTED
    (ARCHIVE/'partial_runs').mkdir(parents=True)
    for name,path in partial.items(): shutil.move(str(path),str(ARCHIVE/'partial_runs'/name))
    for name in ['status.json','failures.json']:
        shutil.move(str(OUT/name),str(ARCHIVE/('old_'+name)))
    stale=ROOT/'results/high_extension_completion_v1'
    if stale.exists(): shutil.move(str(stale),str(ARCHIVE/'stale_completion_state'))
    logs=ARCHIVE/'launcher_logs'; logs.mkdir()
    for name in ['twentythird_high_extension_stdout.log','twentythird_high_extension_stderr.log']:
        p=ROOT/'results'/name
        if p.exists(): shutil.move(str(p),str(logs/name))
    files={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
           for p in ARCHIVE.rglob('*') if p.is_file()}
    manifest={'schema':'high_formal_interruption_archive_v1','complete_runs_retained':107,
              'partial_paid_calls':EXPECTED,'saved_paid_labels':sum(EXPECTED.values()),
              'required_new_suffix_calls':4000-sum(EXPECTED.values()),'dangling_unpaid_pre':0,
              'failures_before_interruption':0,'files':files}
    (ARCHIVE/'archive_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(manifest,indent=2))
if __name__=='__main__': main()
