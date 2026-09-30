"""Recover CMA with bounded state roundoff, audit, and resume the formal batch."""
from __future__ import annotations
import json,os,subprocess
from pathlib import Path
from time import perf_counter
ROOT=Path(__file__).resolve().parents[1];FORMAL=ROOT/'results/application_formal_v1';OUT=ROOT/'results/application_completion_v1';APP=ROOT/'.venv-app/Scripts/python.exe';CORE=ROOT/'.venv312/Scripts/python.exe'
def main():
    assert not OUT.exists() and sum((p/'summary.json').is_file() for p in FORMAL.iterdir() if p.is_dir())==378
    OUT.mkdir();start=perf_counter();stage='recovering_cma_state_with_bounded_roundoff';failure=None
    def save():(OUT/'status.json').write_text(json.dumps({'stage':stage,'pid':os.getpid(),'elapsed':perf_counter()-start,'failure':failure,'recovery_protocol':'application_cma_state_roundoff_v2'},indent=2),encoding='utf-8')
    def execute(exe,module,args,log):
        result=subprocess.run([str(exe),'-m',module,*args],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace');(OUT/log).write_text(result.stdout+result.stderr,encoding='utf-8')
        if result.returncode:raise RuntimeError(f'{module} failed with exit code {result.returncode}')
    try:
        save();execute(APP,'src.recover_interrupted_application_run_v3',['--dataset','DNA','--rep','8','--method','cma_es','--archive',str(ROOT/'results/application_interruption_20260922_v2/partial_runs/cma_es_DNA_r08_b500')],'cma_recovery.log')
        stage='auditing_second_interruption_recovery';save();execute(CORE,'src.audit_application_recovery_v4',[],'recovery_audit_v4.log')
        stage='resuming_formal_application_batch';save();execute(CORE,'src.application_batch_pid_reuse_entry',[],'batch.log')
        stage='full_raw_application_audit';save();execute(CORE,'src.analyze_application',[],'full_raw_audit.log');stage='complete';save()
    except Exception as exc:
        failure={'error_type':type(exc).__name__,'error':str(exc)};stage='failed';save();raise
if __name__=='__main__':main()
