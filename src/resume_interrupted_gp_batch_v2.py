"""Second interruption scheduler: audit caches, route exactly archived partials, preserve logs."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter
from .run_solo_cost import process_inventory

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT/'results/interruption_20260919_v2'
PACKAGES = ['numpy','scipy','ioh','torch','gpytorch','scikit-learn']


def expected_signature(fid,dim,instance,rep,method,budget):
    from .gp_references import code_hash
    return dict(fid=fid,dim=dim,instance=instance,rep=rep,method=method,budget=budget,
                seed=100000*dim+1000*fid+10*instance+rep,code_hash=code_hash(),
                packages={p:importlib.metadata.version(p) for p in PACKAGES})


def validate_cached(path, signature):
    summary = json.loads((path/'summary.json').read_text('utf-8'))
    assert summary['signature'] == signature
    assert summary['algorithm_evaluations'] == signature['budget'] and summary['diagnostic_evaluations'] == 0
    return summary


def command_for(job,out,eligible):
    fid,dim,instance,rep,method = job; budget=10*dim
    runid=f'{method}_f{fid:02}_d{dim}_i{instance}_r{rep}_b{budget}'
    directory=out/runid
    signature=expected_signature(fid,dim,instance,rep,method,budget)
    if (directory/'summary.json').exists():
        validate_cached(directory,signature)
        return runid,None
    if directory.exists():
        raise RuntimeError(runid+': unarchived incomplete directory; refuse overwrite')
    if runid in eligible:
        row=eligible[runid]
        command=[sys.executable,'-m','src.recover_interrupted_run','--kind','gp','--archive',str(ROOT/row['archive']),
                 '--method',method,'--fid',str(fid),'--dim',str(dim),'--instance',str(instance),
                 '--rep',str(rep),'--budget',str(budget),'--out',str(out)]
    else:
        command=[sys.executable,'-m','src.gp_references','--method',method,'--fid',str(fid),'--dim',str(dim),
                 '--instance',str(instance),'--rep',str(rep),'--out',str(out)]
    return runid,command


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',required=True);args=ap.parse_args()
    manifest=json.loads((ARCHIVE/'recovery_manifest.json').read_text('utf-8'))
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest
               for name,digest in manifest['recovery_sources'].items())
    config=json.loads((ROOT/args.config).read_text('utf-8'));out=ROOT/config['out']
    source=Path(config['out']).name
    eligible={row['runid']:row for row in manifest['partial_runs'] if row['source']==source}
    assert eligible and all((ROOT/row['archive']).exists() for row in eligible.values())
    old=json.loads((out/'status.json').read_text('utf-8'))
    assert old['pid'] not in {p['ProcessId'] for p in process_inventory()}, 'Previous batch still live'
    assert not any(p['ProcessId'] not in [os.getpid(),os.getppid()] and any('-m '+m in (p['CommandLine'] or '')
        for m in ['src.resume_interrupted_gp_batch_v2','src.recover_interrupted_run','src.gp_references'])
        for p in process_inventory()), 'Another GP batch or worker is live'
    jobs=[(f,d,i,r,m) for f in config['functions'] for d in config['dimensions'] for i in config['instances']
          for r in range(config['repeats']) for m in config['methods']]
    assert len(jobs)==648
    pid=os.getpid();start=perf_counter();completed=0;failed=[]
    driver=dict(driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                interruption_archive=ARCHIVE.relative_to(ROOT).as_posix(),eligible_partial_runs=sorted(eligible),
                cached_console_logs_preserved=True,scientific_parameters_unchanged=True)
    (out/'recovery_driver_v2.json').write_text(json.dumps(driver,indent=2),encoding='utf-8')
    def save(stage):
        (out/'status.json').write_text(json.dumps(dict(stage=stage,pid=pid,completed=completed,expected=len(jobs),
            failed=len(failed),elapsed=perf_counter()-start),indent=2),encoding='utf-8')
    def execute(job):
        runid,command=command_for(job,out,eligible)
        if command is None:return None
        result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
        log=out/(runid+'.log')
        if log.exists():log=out/(runid+'.recovery-v2.log')
        with log.open('x',encoding='utf-8') as stream:stream.write(result.stdout+result.stderr)
        if result.returncode:return dict(job=job,exit_code=result.returncode,log=log.name)
        validate_cached(out/runid,expected_signature(*job,10*job[1]))
        return None
    save('running');print(f'{len(jobs)} jobs; {config["workers"]} fresh workers; cached logs preserved',flush=True)
    with ThreadPoolExecutor(max_workers=config['workers']) as pool:
        futures={pool.submit(execute,job):job for job in jobs}
        for future in as_completed(futures):
            completed+=1
            try:
                error=future.result()
                if error:failed.append(error)
            except Exception as error:failed.append(dict(job=futures[future],error_type=type(error).__name__,error=str(error)))
            save('running')
            if completed%10==0 or completed==len(jobs):print(f'{completed}/{len(jobs)}; failed={len(failed)}',flush=True)
    (out/'failures.json').write_text(json.dumps(failed,indent=2),encoding='utf-8')
    save('failed' if failed else 'complete')
    if failed:raise SystemExit(1)


if __name__=='__main__':main()
