"""Recover four paid prefixes, then resume and audit the frozen 160-run design."""
from concurrent.futures import ThreadPoolExecutor
import json,subprocess,sys
from pathlib import Path
from time import perf_counter
ROOT=Path(__file__).resolve().parents[1]; STATE=ROOT/'results/high_extension_completion_v1'
JOBS=[(10,'gp_ei'),(2,'turbo_1'),(3,'turbo_1'),(10,'turbo_1')]
def call(args,log):
    r=subprocess.run([str(ROOT/'.venv-app/Scripts/python.exe'),*args],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
    (STATE/log).write_text(r.stdout+r.stderr,encoding='utf-8'); assert r.returncode==0,(log,r.returncode); return r
def save(stage,start,**extra):
    (STATE/'status.json').write_text(json.dumps({'stage':stage,'pid':__import__('os').getpid(),'elapsed':perf_counter()-start,**extra},indent=2),encoding='utf-8')
def main():
    STATE.mkdir();start=perf_counter();save('recovering_four_paid_prefixes',start,recovered=0)
    archive='results/application_high_interruption_20260922_v1/partial_runs'
    def one(job):
        rep,method=job;runid=f'{method}_synt_high_r{rep:02}_b1000'
        return call(['-m','src.recover_interrupted_high_run','--rep',str(rep),'--method',method,'--archive',f'{archive}/{runid}'],runid+'.recovery.log')
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(one,j) for j in JOBS]
        for i,f in enumerate(futures,1):f.result();save('recovering_four_paid_prefixes',start,recovered=i)
    call(['-m','src.audit_high_formal_recovery'],'recovery_audit.log');save('resuming_formal_160_runs',start,recovered=4)
    call(['-m','src.run_application_high_formal'],'formal.log');save('auditing_formal_160_runs',start,recovered=4)
    call(['-m','src.analyze_application_high_formal_safe'],'formal_audit.log');save('complete',start,recovered=4,formal_runs=160)
if __name__=='__main__':main()
