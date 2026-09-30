"""Serial pipeline with durable stage records and independent diagnostics."""
import json
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from .diagnostics import diagnostic_one


def main():
    root = Path(__file__).resolve().parents[1]
    source = root/'results/mechanism_validation_v1'
    diag = root/'results/mechanism_validation_diagnostics_v1'
    status = root/'results/mechanism_validation_status.json'
    status.parent.mkdir(exist_ok=True)
    def record(stage):
        status.write_text(json.dumps(dict(stage=stage,pid=__import__('os').getpid()),indent=2),encoding='utf-8')
    record('algorithm_running')
    subprocess.run([sys.executable,'-m','src.experiment','--config','configs/mechanism_validation.json'],cwd=root,check=True)
    record('diagnostics_running')
    jobs = [(str(f.parent),str(diag),.3) for f in sorted(source.glob('*/summary.json'))
            if any(f.parent.name.startswith(h+'_') for h in ['greedy','fixed03','pool_random'])]
    assert len(jobs)==1944
    counts=[]
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(diagnostic_one,j) for j in jobs]
        for future in as_completed(futures):
            counts.append(future.result())
            if len(counts)%20==0 or len(counts)==len(jobs):
                print(f'Mechanism diagnostics {len(counts)}/{len(jobs)}',flush=True)
    (diag/'counts.json').write_text(json.dumps(dict(runs=len(counts),algorithm=sum(c['algorithm_evaluations'] for c in counts),
                                                   diagnostic=sum(c['diagnostic_evaluations'] for c in counts)),indent=2),encoding='utf-8')
    record('analysis_running')
    subprocess.run([sys.executable,'-m','src.validate_mechanisms','--source',str(source),'--diagnostics',str(diag),
                    '--out','results/mechanism_validation_analysis_v1'],cwd=root,check=True)
    record('complete')


if __name__=='__main__':
    main()
