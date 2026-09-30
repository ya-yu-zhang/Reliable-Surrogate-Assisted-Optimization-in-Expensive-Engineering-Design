"""Serial fresh-process resource checks; preserve every scientific failure."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]


def main():
    config = json.loads((ROOT/'configs/application_precheck.json').read_text('utf-8'))
    frozen = json.loads((ROOT/'docs/frozen_application_precheck_v1/sha256.json').read_text('utf-8'))
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest for name,digest in frozen.items())
    out = ROOT/config['out'];out.mkdir(parents=True,exist_ok=True)
    manifest = dict(config=config,frozen_sources=frozen)
    file = out/'manifest.json'
    if file.exists(): assert json.loads(file.read_text('utf-8'))==manifest
    file.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    failures = []; completed = 0; tick = perf_counter()
    def save(stage):
        (out/'status.json').write_text(json.dumps(dict(stage=stage,pid=os.getpid(),completed=completed,
            expected=3,failed=len(failures),elapsed=perf_counter()-tick),indent=2),encoding='utf-8')
    save('running')
    try:
        for dataset in config['datasets']:
            result = subprocess.run([str(ROOT/'.venv-app/Scripts/python.exe'),'-m','src.application_precheck',
                '--dataset',dataset],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
            (out/(dataset+'.log')).write_text(result.stdout+result.stderr,encoding='utf-8')
            if result.returncode:
                failures.append(dict(dataset=dataset,exit_code=result.returncode,log=dataset+'.log'))
                raise RuntimeError(dataset+' resource check failed; original log retained')
            summary = json.loads((out/dataset/'summary.json').read_text('utf-8'))
            assert summary['objective_calls']==6 and summary['deterministic_repeated_point']
            completed += 1;save('running')
            print(f'{completed}/3 resource checks complete',flush=True)
    finally:
        (out/'failures.json').write_text(json.dumps(failures,indent=2),encoding='utf-8')
        save('complete' if completed==3 and not failures else 'failed')


if __name__=='__main__':main()
