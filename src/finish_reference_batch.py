"""Continue current authorized batch dependencies without restarting optimizers."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
from time import perf_counter, sleep

from .run_solo_cost import process_inventory

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT/'.venv312/Scripts/python.exe'
OUT = ROOT/'results/reference_completion_v1'
TASKS = [('turbo_reference_v1','turbo_reference_analysis_v1'),
         ('gp_ei_reference_v1','gp_ei_reference_analysis_v1')]


def execute(module, arguments, log):
    result = subprocess.run([str(CORE),'-m',module,*arguments],cwd=ROOT,capture_output=True,
                            text=True,encoding='utf-8',errors='replace')
    (OUT/log).write_text(result.stdout+result.stderr,encoding='utf-8')
    if result.returncode:
        raise RuntimeError(f'{module} exited {result.returncode}; see {log}')


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    start = perf_counter(); completed = set(); stage = 'waiting_for_formal_batches'; failure = None
    own_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    path = OUT/'status.json'
    if path.exists():
        previous = json.loads(path.read_text('utf-8'))
        if previous['stage'] != 'complete' and previous['pid'] in {p['ProcessId'] for p in process_inventory()}:
            raise RuntimeError('Completion pipeline already live; refusing duplicate')
        assert previous['pipeline_sha256'] == own_hash
    def save():
        path.write_text(json.dumps(dict(stage=stage,pid=os.getpid(),pipeline_sha256=own_hash,
            external_audits_completed=sorted(completed),elapsed=perf_counter()-start,failure=failure),indent=2),encoding='utf-8')
    try:
        while len(completed) < len(TASKS):
            processes = {p['ProcessId'] for p in process_inventory()}
            for source,destination in TASKS:
                if source in completed: continue
                status = json.loads((ROOT/'results'/source/'status.json').read_text('utf-8'))
                if status['stage'] == 'failed' or status['failed']:
                    raise RuntimeError(f'{source} has scientific failures; no automatic rerun')
                if status['stage'] == 'complete' and status['pid'] not in processes:
                    assert status['completed'] == status['expected'] == 648
                    stage = 'auditing_'+source; save()
                    execute('src.analyze_gp_references',['--source','results/'+source,'--out','results/'+destination],source+'_audit.log')
                    completed.add(source); print(source+' full raw-journal audit complete',flush=True)
                    stage = 'waiting_for_formal_batches'; save()
                elif status['pid'] not in processes:
                    raise RuntimeError(f'{source} process ended without complete stage; inspect original session')
            if len(completed) < len(TASKS):
                save(); sleep(30)
        stage = 'serial_cost_measurement'; save()
        execute('src.run_solo_cost',[], 'solo_cost_measurement.log')
        stage = 'serial_cost_audit'; save()
        execute('src.analyze_solo_cost',[], 'solo_cost_audit.log')
        stage = 'complete'; save()
        print('Both formal reference audits and serial cost audit complete; manuscript integration and visual QA remain.',flush=True)
    except Exception as error:
        failure = {'error':str(error)}; stage = 'failed'; save(); raise


if __name__ == '__main__':
    main()
