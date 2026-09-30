"""Four fresh workers for the frozen 450-run model sensitivity design."""
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,os,random,subprocess
from pathlib import Path
from queue import Empty,Queue
from threading import Event,Lock
from time import perf_counter
from .run_solo_cost import process_inventory

ROOT=Path(__file__).resolve().parents[1];CONFIG='configs/model_sensitivity.json'


def prerequisite():
    prior=json.loads((ROOT/'results/high_evidence_export_v1/status.json').read_text('utf-8'))
    alive={p['ProcessId'] for p in process_inventory()}
    assert prior['stage'] in ['compiled_pending_visual_review','complete'] and prior['failure'] is None
    assert prior['pid'] not in alive
    forbidden=['src.run_model_sensitivity','src.model_sensitivity_experiment','src.run_application_high_formal',
               'src.application_high_experiment','src.run_application_high_method_resource','src.application_high_method_resource',
               'src.run_solo_cost','src.solo_cost','src.gp_references']
    assert not any(p['ProcessId'] not in [os.getpid(),os.getppid()] and any('-m '+m in (p['CommandLine'] or '')
        for m in forbidden) for p in process_inventory())


def main():
    prerequisite();config=json.loads((ROOT/CONFIG).read_text('utf-8'))
    frozen=json.loads((ROOT/config['freeze_manifest']).read_text('utf-8'))
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==v for n,v in frozen.items())
    out=ROOT/config['out'];out.mkdir(parents=True,exist_ok=True)
    manifest=dict(config=config,frozen_sources=frozen,workers=4)
    path=out/'manifest.json'
    if path.exists():assert json.loads(path.read_text('utf-8'))==manifest
    else:path.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    jobs=[(v,f,d,i,r) for v in config['variants'] for f in config['functions'] for d in config['dimensions']
          for i in config['instances'] for r in range(config['repeats'])]
    assert len(jobs)==450;random.Random(config['order_seed']).shuffle(jobs);queue=Queue()
    for job in jobs:queue.put(job)
    stop=Event();lock=Lock();completed=0;failures=[];start=perf_counter()
    def save(stage):
        (out/'status.json').write_text(json.dumps(dict(stage=stage,pid=os.getpid(),completed=completed,expected=450,
            failed=len(failures),elapsed=perf_counter()-start),indent=2),encoding='utf-8')
        (out/'failures.json').write_text(json.dumps(failures,indent=2),encoding='utf-8')
    def work():
        nonlocal completed
        while not stop.is_set():
            try:v,f,d,i,r=queue.get_nowait()
            except Empty:return
            runid=f'PEM_T_f{f:02}_d{d}_i{i}_r{r}_b{10*d}';directory=out/v/runid
            try:
                if directory.exists() and not (directory/'summary.json').exists():raise RuntimeError('Incomplete directory retained')
                result=subprocess.run([str(ROOT/'.venv312/Scripts/python.exe'),'-m','src.model_sensitivity_experiment',
                    '--variant',v,'--fid',str(f),'--dim',str(d),'--instance',str(i),'--rep',str(r)],cwd=ROOT,
                    capture_output=True,text=True,encoding='utf-8',errors='replace')
                log=out/f'{v}_{runid}.log'
                if log.exists():log=out/f'{v}_{runid}.attempt-{os.getpid()}.log'
                with log.open('x',encoding='utf-8') as stream:stream.write(result.stdout+result.stderr)
                if result.returncode:raise RuntimeError(f'exit {result.returncode}; {log.name}')
                summary=json.loads((directory/'summary.json').read_text('utf-8'));assert summary['algorithm_evaluations']==10*d
                with lock:completed+=1;save('running');print(f'{completed}/450 complete',flush=True)
            except Exception as error:
                with lock:failures.append(dict(variant=v,fid=f,dim=d,instance=i,rep=r,error_type=type(error).__name__,error=str(error)));stop.set();save('stopping_after_failure')
            finally:queue.task_done()
    save('running')
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(work) for _ in range(4)]
        for future in futures:future.result()
    save('complete' if completed==450 and not failures else 'failed')
    if failures or completed!=450:raise RuntimeError('Sensitivity stopped; no automatic rerun')


if __name__=='__main__':main()
