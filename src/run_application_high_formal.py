"""Frozen 160-run high extension: four processes, one GP-EI slot."""
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,os,random,subprocess
from pathlib import Path
from queue import Empty,Queue
from threading import Event,Lock
from time import perf_counter
from .run_solo_cost import process_inventory

ROOT=Path(__file__).resolve().parents[1];CONFIG='configs/application_high_formal.json'


def prerequisite():
    source=ROOT/'results/application_high_method_resource_analysis_v1'
    audit=json.loads((source/'audit.json').read_text('utf-8'))
    assert audit['complete_design'] and audit['source_hashes_verified'] and audit['runs']==8
    assert audit['algorithm_evaluations']==8000 and audit['test_method_calls']==0
    for name,value in json.loads((source/'source_hashes.json').read_text('utf-8')).items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==value
    processes=process_inventory()
    forbidden=['src.run_application_high_method_resource','src.application_high_method_resource',
               'src.run_application_high_formal','src.application_high_experiment','src.run_application_batch',
               'src.application_experiment','src.run_solo_cost','src.solo_cost','src.gp_references']
    assert not any(p['ProcessId'] not in [os.getpid(),os.getppid()] and any('-m '+m in (p['CommandLine'] or '')
        for m in forbidden) for p in processes),'Scientific process still active'


def main():
    prerequisite();config=json.loads((ROOT/CONFIG).read_text('utf-8'))
    frozen=json.loads((ROOT/config['freeze_manifest']).read_text('utf-8'))
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==v for n,v in frozen.items())
    out=ROOT/config['out'];out.mkdir(parents=True,exist_ok=True)
    manifest=dict(config=config,frozen_sources=frozen,total_worker_limit=4,gp_ei_worker_limit=1)
    path=out/'manifest.json'
    if path.exists():assert json.loads(path.read_text('utf-8'))==manifest
    else:path.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    jobs=[(r,m) for r in range(config['repeats']) for m in config['methods']]
    assert len(jobs)==160;random.Random(config['order_seed']).shuffle(jobs)
    queues=[Queue(),Queue()]
    for job in jobs:queues[int(job[1]!='gp_ei')].put(job)
    stop=Event();lock=Lock();completed=0;failures=[];start=perf_counter()
    def save(stage):
        (out/'status.json').write_text(json.dumps(dict(stage=stage,pid=os.getpid(),completed=completed,
            expected=160,failed=len(failures),elapsed=perf_counter()-start),indent=2),encoding='utf-8')
        (out/'failures.json').write_text(json.dumps(failures,indent=2),encoding='utf-8')
    def work(queue):
        nonlocal completed
        while not stop.is_set():
            try:rep,method=queue.get_nowait()
            except Empty:return
            runid=f'{method}_synt_high_r{rep:02}_b1000'
            try:
                result=subprocess.run([str(ROOT/'.venv-app/Scripts/python.exe'),'-m','src.application_high_experiment',
                    '--rep',str(rep),'--method',method],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
                log=out/(runid+'.log')
                if log.exists():log=out/(runid+f'.attempt-{os.getpid()}.log')
                with log.open('x',encoding='utf-8') as stream:stream.write(result.stdout+result.stderr)
                if result.returncode:raise RuntimeError(f'exit {result.returncode}; retained {log.name}')
                summary=json.loads((out/runid/'summary.json').read_text('utf-8'))
                assert summary['algorithm_evaluations']==1000 and summary['test_method_calls']==1
                with lock:completed+=1;save('running');print(f'{completed}/160 complete',flush=True)
            except Exception as error:
                with lock:failures.append(dict(rep=rep,method=method,error_type=type(error).__name__,error=str(error)));stop.set();save('stopping_after_failure')
            finally:queue.task_done()
    save('running')
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(work,queues[0])]+[pool.submit(work,queues[1]) for _ in range(3)]
        for future in futures:future.result()
    save('complete' if completed==160 and not failures else 'failed')
    if failures or completed!=160:raise RuntimeError('High extension stopped; no automatic rerun')


if __name__=='__main__':main()
