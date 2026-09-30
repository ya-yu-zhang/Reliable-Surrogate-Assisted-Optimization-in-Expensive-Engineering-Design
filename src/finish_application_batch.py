"""Wait for the existing serial cost chain, then run the frozen application once."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
from time import perf_counter,sleep

from .run_solo_cost import process_inventory

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/application_completion_v1'


def main():
    OUT.mkdir(parents=True,exist_ok=True);path=OUT/'status.json'
    if path.exists():raise RuntimeError('Existing application completion record preserved; refuse duplicate or automatic restart')
    frozen=json.loads((ROOT/'docs/frozen_application_formal_v1/sha256.json').read_text('utf-8'))
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest for name,digest in frozen.items())
    own_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    stage='waiting_for_reference_and_cost_completion';failure=None;start=perf_counter()
    def save():
        path.write_text(json.dumps(dict(stage=stage,pid=os.getpid(),pipeline_sha256=own_hash,
            elapsed=perf_counter()-start,failure=failure),indent=2),encoding='utf-8')
    def execute(module,log):
        result=subprocess.run([str(ROOT/'.venv312/Scripts/python.exe'),'-m',module],cwd=ROOT,
            capture_output=True,text=True,encoding='utf-8',errors='replace')
        (OUT/log).write_text(result.stdout+result.stderr,encoding='utf-8')
        if result.returncode:raise RuntimeError(f'{module} exited {result.returncode}; original {log} retained')
    try:
        save()
        while True:
            prior=json.loads((ROOT/'results/reference_completion_v1/status.json').read_text('utf-8'))
            processes={p['ProcessId'] for p in process_inventory()}
            if prior['stage']=='failed' or prior['failure'] is not None:
                raise RuntimeError('Reference/cost prerequisite failed; no application labels or scientific rerun')
            if prior['stage']=='complete' and prior['pid'] not in processes:break
            if prior['pid'] not in processes:raise RuntimeError('Prerequisite process ended without completion; investigate original task')
            save();sleep(30)
        stage='formal_application_batch';save();execute('src.run_application_batch','formal_application.log')
        stage='full_raw_application_audit';save();execute('src.analyze_application','full_raw_audit.log')
        stage='complete';save()
        print('Application batch and raw audit complete. Manuscript integration and visual QA remain.',flush=True)
    except Exception as error:
        failure=dict(error=str(error));stage='failed';save();raise


if __name__=='__main__':main()
