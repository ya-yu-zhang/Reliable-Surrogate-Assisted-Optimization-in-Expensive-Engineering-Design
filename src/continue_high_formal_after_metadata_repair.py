"""Audit repaired recovery metadata, continue 160 runs, and audit the full result."""
import json,subprocess,os
from pathlib import Path
from time import perf_counter
ROOT=Path(__file__).resolve().parents[1]; STATE=ROOT/'results/high_extension_completion_v1'
def call(module,log):
    r=subprocess.run([str(ROOT/'.venv-app/Scripts/python.exe'),'-m',module],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
    (STATE/log).write_text(r.stdout+r.stderr,encoding='utf-8'); assert r.returncode==0,(module,r.returncode)
def save(stage,start,**extra):
    (STATE/'status.json').write_text(json.dumps({'stage':stage,'pid':os.getpid(),'elapsed':perf_counter()-start,**extra},indent=2),encoding='utf-8')
def main():
    start=perf_counter();save('repairing_and_auditing_recovered_runs',start,recovered=4)
    call('src.repair_high_recovery_metadata','metadata_repair.log');call('src.audit_high_formal_recovery','recovery_audit.log')
    save('resuming_formal_160_runs',start,recovered=4)
    call('src.run_application_high_formal','formal.log');save('auditing_formal_160_runs',start,recovered=4)
    call('src.analyze_application_high_formal_safe','formal_audit.log');save('complete',start,recovered=4,formal_runs=160)
if __name__=='__main__':main()
