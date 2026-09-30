"""Frozen full-budget application batch, four fresh processes, one GP-EI slot."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
from queue import Empty, Queue
import random
import subprocess
from threading import Event, Lock
from time import perf_counter

from .run_solo_cost import process_inventory

ROOT=Path(__file__).resolve().parents[1]
CONFIG='configs/application_formal.json'


def prerequisite():
    path=ROOT/'results/reference_completion_v1/status.json'
    status=json.loads(path.read_text('utf-8'))
    assert status['stage']=='complete' and status['failure'] is None
    processes=process_inventory()
    assert status['pid'] not in {p['ProcessId'] for p in processes}, 'Reference/cost pipeline has not exited'
    forbidden=['src.run_gp_batch','src.gp_references','src.run_solo_cost','src.solo_cost',
               'src.run_application_batch','src.application_experiment','src.mechanism_pipeline',
               'src.experiment','src.diagnostics','src.basic_references','src.application_precheck']
    assert not any(p['ProcessId']!=os.getpid() and any('-m '+m in (p['CommandLine'] or '')
                   for m in forbidden) for p in processes), 'Scientific batch already active'
    audit=json.loads((ROOT/'results/solo_cost_analysis_v1/integrity_audit.json').read_text('utf-8'))
    assert audit['runs']==54 and audit['complete_design'] and audit['source_hashes_verified']
    return status


def main():
    prior=prerequisite()
    config=json.loads((ROOT/CONFIG).read_text('utf-8'))
    frozen=json.loads((ROOT/'docs/frozen_application_formal_v1/sha256.json').read_text('utf-8'))
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest for name,digest in frozen.items())
    out=ROOT/config['out'];out.mkdir(parents=True,exist_ok=True)
    manifest=dict(config=config,frozen_sources=frozen,prerequisite_completed=prior,
                  total_worker_limit=4,gp_ei_worker_limit=1)
    file=out/'manifest.json'
    if file.exists():
        previous=json.loads(file.read_text('utf-8'))
        assert previous['config']==config and previous['frozen_sources']==frozen
        manifest=previous
    file.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    jobs=[(d,r,m) for d in config['datasets'] for r in range(config['repeats']) for m in config['methods']]
    random.Random(config['order_seed']).shuffle(jobs)
    queues=[Queue(),Queue()]
    for job in jobs:queues[int(job[2]!='gp_ei')].put(job)
    stop=Event();lock=Lock();completed=0;failures=[];start=perf_counter()
    def save(stage):
        (out/'status.json').write_text(json.dumps(dict(stage=stage,pid=os.getpid(),completed=completed,
            expected=len(jobs),failed=len(failures),elapsed=perf_counter()-start),indent=2),encoding='utf-8')
        (out/'failures.json').write_text(json.dumps(failures,indent=2),encoding='utf-8')
    save('running')
    def work(queue):
        nonlocal completed
        while not stop.is_set():
            try:dataset,rep,method=queue.get_nowait()
            except Empty:return
            runid=f'{method}_{dataset}_r{rep:02}_b{config["budgets"][dataset]}'
            try:
                result=subprocess.run([str(ROOT/'.venv-app/Scripts/python.exe'),'-m','src.application_experiment',
                    '--config',CONFIG,'--dataset',dataset,'--rep',str(rep),'--method',method],cwd=ROOT,
                    capture_output=True,text=True,encoding='utf-8',errors='replace')
                (out/(runid+'.log')).write_text(result.stdout+result.stderr,encoding='utf-8')
                if result.returncode:raise RuntimeError(f'Exit {result.returncode}; retained {runid}.log')
                summary=json.loads((out/runid/'summary.json').read_text('utf-8'))
                assert summary['algorithm_evaluations']==config['budgets'][dataset] and summary['test_method_calls']==1
                with lock:
                    completed+=1;save('running')
                    print(f'{completed}/{len(jobs)} complete; failed={len(failures)}',flush=True)
            except Exception as error:
                with lock:
                    failures.append(dict(dataset=dataset,rep=rep,method=method,error=str(error)))
                    stop.set();save('stopping_after_failure')
            finally:queue.task_done()
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures=[executor.submit(work,queues[0])]+[executor.submit(work,queues[1]) for _ in range(3)]
        for future in futures:future.result()
    save('complete' if completed==len(jobs) and not failures else 'failed')
    if failures or completed!=len(jobs):raise RuntimeError('Application batch stopped; no automatic scientific rerun')


if __name__=='__main__':main()
