"""Recover the second interrupted prefixes, resume the formal design, then audit it."""
from concurrent.futures import ThreadPoolExecutor
import json,subprocess,os
from pathlib import Path
from time import perf_counter
ROOT=Path(__file__).resolve().parents[1];STATE=ROOT/'results/high_extension_completion_v1'
JOBS=[(3,'gp_ei'),(4,'turbo_1'),(14,'turbo_1')]
def run(args,log):
    r=subprocess.run([str(ROOT/'.venv-app/Scripts/python.exe'),*args],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
    (STATE/log).write_text(r.stdout+r.stderr,encoding='utf-8');assert r.returncode==0,(log,r.returncode)
def save(stage,start,**extra):(STATE/'status.json').write_text(json.dumps({'stage':stage,'pid':os.getpid(),'elapsed':perf_counter()-start,**extra},indent=2),encoding='utf-8')
def main():
    STATE.mkdir();start=perf_counter();save('recovering_three_paid_prefixes_round2',start,recovered=0)
    base=(ROOT/'results/application_high_interruption_20260923_v2/partial_runs').resolve()
    def one(job):
        rep,method=job;rid=f'{method}_synt_high_r{rep:02}_b1000'
        run(['-m','src.recover_interrupted_high_run','--rep',str(rep),'--method',method,'--archive',str(base/rid)],rid+'.recovery.log')
    with ThreadPoolExecutor(max_workers=3) as pool:
        fs=[pool.submit(one,j) for j in JOBS]
        for i,f in enumerate(fs,1):f.result();save('recovering_three_paid_prefixes_round2',start,recovered=i)
    run(['-m','src.audit_high_formal_recovery_round2'],'recovery_audit_round2.log');save('resuming_formal_160_runs_round2',start,recovered=3)
    run(['-m','src.run_application_high_formal'],'formal_round2.log');save('auditing_formal_160_runs',start,recovered=3)
    run(['-m','src.analyze_application_high_formal_safe'],'formal_audit.log');save('complete',start,recovered=3,formal_runs=160)
if __name__=='__main__':main()
