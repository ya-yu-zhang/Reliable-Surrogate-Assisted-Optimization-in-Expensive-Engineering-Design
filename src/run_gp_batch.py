"""One fresh process per external GP run, durable complete/failed stages."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter

ROOT=Path(__file__).resolve().parents[1]


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',required=True);args=ap.parse_args()
    config=json.loads(Path(args.config).read_text('utf-8'))
    out=ROOT/config['out'];out.mkdir(parents=True,exist_ok=True)
    fingerprints={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in
                  ['src/gp_references.py','src/run_gp_batch.py','docs/baselines-environment-lock.txt']}
    for path in sorted((ROOT/'literature/source-code/TuRBO/turbo').glob('*.py')):
        fingerprints[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
    manifest=dict(config=config,fingerprints=fingerprints)
    file=out/'manifest.json'
    if file.exists():assert json.loads(file.read_text('utf-8'))==manifest
    file.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    jobs=[(f,d,i,r,m) for f in config['functions'] for d in config['dimensions'] for i in config['instances']
          for r in range(config['repeats']) for m in config['methods']]
    pid=__import__('os').getpid();start=perf_counter()
    def status(stage,count,failed):
        (out/'status.json').write_text(json.dumps(dict(stage=stage,pid=pid,completed=count,expected=len(jobs),
                                                     failed=len(failed),elapsed=perf_counter()-start),indent=2),encoding='utf-8')
    def execute(job):
        f,d,i,r,m=job
        runid=f'{m}_f{f:02}_d{d}_i{i}_r{r}_b{10*d}'
        # gp_references verifies existing signatures before skipping a completed run.
        command=[sys.executable,'-m','src.gp_references','--method',m,'--fid',str(f),'--dim',str(d),
                 '--instance',str(i),'--rep',str(r),'--out',str(out)]
        result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
        (out/f'{runid}.log').write_text(result.stdout+result.stderr,encoding='utf-8')
        if result.returncode:
            return dict(job=job,exit_code=result.returncode,log=f'{runid}.log')
        summary=json.loads((out/runid/'summary.json').read_text('utf-8'))
        assert summary['algorithm_evaluations']==10*d
        return None
    failed=[];count=0;status('running',0,failed)
    print(f'{len(jobs)} GP reference runs; {config["workers"]} independent processes',flush=True)
    with ThreadPoolExecutor(max_workers=config['workers']) as executor:
        futures={executor.submit(execute,job):job for job in jobs}
        for future in as_completed(futures):
            count+=1
            try:
                error=future.result()
                if error:failed.append(error)
            except Exception as error:failed.append(dict(job=futures[future],error=str(error)))
            status('running',count,failed)
            if count%10==0 or count==len(jobs):print(f'{count}/{len(jobs)}; failed={len(failed)}; seconds={perf_counter()-start:.1f}',flush=True)
    (out/'failures.json').write_text(json.dumps(failed,indent=2),encoding='utf-8')
    status('failed' if failed else 'complete',count,failed)
    if failed:raise SystemExit(1)


if __name__=='__main__':main()
