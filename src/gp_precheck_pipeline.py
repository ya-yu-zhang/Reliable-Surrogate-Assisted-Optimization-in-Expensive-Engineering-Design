"""Resource-only pilot summaries; every job has its own OS process."""
import csv
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import subprocess
import sys


def main():
    root=Path(__file__).resolve().parents[1]
    out=root/'results/gp_resource_precheck_v1';out.mkdir(parents=True,exist_ok=True)
    python=root/'.venv-baselines/Scripts/python.exe'
    jobs=[(method,dim) for method in ['gp_ei','turbo_1'] for dim in [10,20,40]]
    (out/'status.json').write_text(json.dumps(dict(stage='running',pid=__import__('os').getpid(),jobs=jobs),indent=2),encoding='utf-8')
    def execute(job):
        method,dim=job
        command=[str(python),'-m','src.gp_references','--method',method,'--dim',str(dim),'--instance','4','--out',str(out)]
        result=subprocess.run(command,cwd=root,capture_output=True,text=True,encoding='utf-8',errors='replace')
        (out/f'{method}_d{dim}.log').write_text(result.stdout+result.stderr,encoding='utf-8')
        assert result.returncode==0,(method,dim,result.stderr)
        # Read resource fields only; do not use final objective values to select scope.
        file=out/f'{method}_f01_d{dim}_i4_r0_b{10*dim}'/'summary.json'
        summary=json.loads(file.read_text('utf-8'))
        prepare=summary['preparation_seconds'][2*dim:]
        return dict(method=method,dim=dim,budget=10*dim,elapsed=summary['elapsed'],
                    peak_working_set_bytes=summary['process_peak_working_set_bytes'],
                    mean_post_initialization_preparation=sum(prepare)/len(prepare),
                    algorithm_evaluations=summary['algorithm_evaluations'])
    records=[];failed=[]
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures={executor.submit(execute,job):job for job in jobs}
        for future in as_completed(futures):
            try:
                record=future.result();records.append(record)
                print(json.dumps(record),flush=True)
            except Exception as error:
                failed.append(dict(job=futures[future],error=str(error)))
    (out/'failures.json').write_text(json.dumps(failed,indent=2),encoding='utf-8')
    if records:
        with (out/'resources.csv').open('w',newline='',encoding='utf-8') as file:
            writer=csv.DictWriter(file,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
    (out/'status.json').write_text(json.dumps(dict(stage='failed' if failed else 'complete',completed=len(records),failed=len(failed)),indent=2),encoding='utf-8')
    if failed:raise SystemExit(1)


if __name__=='__main__':main()
