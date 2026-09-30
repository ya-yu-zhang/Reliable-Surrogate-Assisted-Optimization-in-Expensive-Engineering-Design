"""Independent 5D/10D/15D runs: four workers, at most one GP-EI."""
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,os,random,subprocess
from pathlib import Path
from queue import Empty,Queue
from threading import Event,Lock
from time import perf_counter
from .run_solo_cost import process_inventory

ROOT=Path(__file__).resolve().parents[1];CONFIG='configs/budget_performance_sensitivity.json'


def prerequisite():
    prior=json.loads((ROOT/'results/sensitivity_evidence_export_v1/status.json').read_text('utf-8'))
    alive={p['ProcessId'] for p in process_inventory()}
    assert prior['stage'] in ['compiled_pending_visual_review','complete'] and prior['failure'] is None and prior['pid'] not in alive
    modules=['src.run_budget_performance_sensitivity','src.budget_sensitivity_worker','src.gp_references','src.experiment',
             'src.run_model_sensitivity','src.model_sensitivity_experiment','src.run_application_high_formal','src.run_solo_cost','src.solo_cost']
    assert not any(p['ProcessId'] not in [os.getpid(),os.getppid()] and any('-m '+m in (p['CommandLine'] or '')
        for m in modules) for p in process_inventory())


def main():
    prerequisite();config=json.loads((ROOT/CONFIG).read_text('utf-8'))
    frozen=json.loads((ROOT/config['freeze_manifest']).read_text('utf-8'))
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==v for n,v in frozen.items())
    out=ROOT/config['out'];out.mkdir(parents=True,exist_ok=True)
    manifest=dict(config=config,frozen_sources=frozen,total_worker_limit=4,gp_ei_worker_limit=1)
    path=out/'manifest.json'
    if path.exists():assert json.loads(path.read_text('utf-8'))==manifest
    else:path.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    jobs=[(m,f,d,i,r,b) for m in config['methods'] for f in config['functions'] for d in config['dimensions']
          for i in config['instances'] for r in range(3) for b in config['budget_multipliers']]
    assert len(jobs)==2700;random.Random(config['order_seed']).shuffle(jobs);queues=[Queue(),Queue()]
    for job in jobs:queues[int(job[0]!='gp_ei')].put(job)
    stop=Event();lock=Lock();completed=0;failures=[];start=perf_counter()
    def save(stage):
        (out/'status.json').write_text(json.dumps(dict(stage=stage,pid=os.getpid(),completed=completed,expected=2700,
            failed=len(failures),elapsed=perf_counter()-start),indent=2),encoding='utf-8')
        (out/'failures.json').write_text(json.dumps(failures,indent=2),encoding='utf-8')
    def work(queue):
        nonlocal completed
        while not stop.is_set():
            try:method,fid,dim,instance,rep,multiplier=queue.get_nowait()
            except Empty:return
            runid=f'{method}_f{fid:02}_d{dim}_i{instance}_r{rep}_b{multiplier*dim}'
            directory=out/f'budget_{multiplier}D'/method/runid
            try:
                if directory.exists() and not (directory/'summary.json').exists():raise RuntimeError('Incomplete directory retained')
                python=ROOT/('.venv-baselines/Scripts/python.exe' if method in ['gp_ei','turbo_1'] else '.venv312/Scripts/python.exe')
                result=subprocess.run([str(python),'-m','src.budget_sensitivity_worker','--method',method,'--fid',str(fid),
                    '--dim',str(dim),'--instance',str(instance),'--rep',str(rep),'--multiplier',str(multiplier)],
                    cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
                log=out/f'{multiplier}D_{runid}.log'
                if log.exists():log=out/f'{multiplier}D_{runid}.attempt-{os.getpid()}.log'
                with log.open('x',encoding='utf-8') as stream:stream.write(result.stdout+result.stderr)
                if result.returncode:raise RuntimeError(f'exit {result.returncode}; retained {log.name}')
                summary=json.loads((directory/'summary.json').read_text('utf-8'));assert summary['algorithm_evaluations']==multiplier*dim
                with lock:completed+=1;save('running');print(f'{completed}/2700 complete',flush=True)
            except Exception as error:
                with lock:failures.append(dict(method=method,fid=fid,dim=dim,instance=instance,rep=rep,
                    multiplier=multiplier,error_type=type(error).__name__,error=str(error)));stop.set();save('stopping_after_failure')
            finally:queue.task_done()
    save('running')
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(work,queues[0])]+[pool.submit(work,queues[1]) for _ in range(3)]
        for future in futures:future.result()
    save('complete' if completed==2700 and not failures else 'failed')
    if failures or completed!=2700:raise RuntimeError('Budget sensitivity stopped; no automatic rerun')


if __name__=='__main__':main()
