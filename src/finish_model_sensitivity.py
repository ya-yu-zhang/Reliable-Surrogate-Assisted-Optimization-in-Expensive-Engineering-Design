"""One dependency chain for the frozen 450-run model sensitivity and raw audit."""
import hashlib,json,os,subprocess
from pathlib import Path
from time import perf_counter,sleep
from .run_solo_cost import process_inventory

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/model_sensitivity_completion_v1'


def main():
    assert not OUT.exists(),'Sensitivity completion record exists; refuse duplicate restart'
    frozen=json.loads((ROOT/'docs/frozen_model_sensitivity_v1/sha256.json').read_text('utf-8'))
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==v for n,v in frozen.items())
    OUT.mkdir(parents=True);stage='waiting_for_high_evidence_export';failure=None;start=perf_counter()
    def save():
        (OUT/'status.json').write_text(json.dumps(dict(stage=stage,pid=os.getpid(),elapsed=perf_counter()-start,
            failure=failure,runs=json.loads((ROOT/'results/model_sensitivity_analysis_v1/audit.json').read_text())['runs'] if (ROOT/'results/model_sensitivity_analysis_v1/audit.json').exists() else 0),indent=2),encoding='utf-8')
    def execute(module,log):
        result=subprocess.run([str(ROOT/'.venv312/Scripts/python.exe'),'-m',module],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
        (OUT/log).write_text(result.stdout+result.stderr,encoding='utf-8')
        if result.returncode:raise RuntimeError(f'{module} exited {result.returncode}; retained {log}')
    try:
        save()
        while True:
            prior=json.loads((ROOT/'results/high_evidence_export_v1/status.json').read_text('utf-8'))
            alive={p['ProcessId'] for p in process_inventory()}
            if prior['stage']=='failed' or prior['failure'] is not None:raise RuntimeError('High evidence prerequisite failed')
            if prior['stage'] in ['compiled_pending_visual_review','complete'] and prior['pid'] not in alive:break
            if prior['pid'] not in alive:raise RuntimeError('High evidence parent ended before compilation')
            save();sleep(30)
        assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==v for n,v in frozen.items())
        stage='formal_450_runs';save();execute('src.run_model_sensitivity','runs.log')
        stage='full_raw_audit';save();execute('src.analyze_model_sensitivity','audit.log')
        stage='complete';save();print('Model sensitivity and full raw audit complete.',flush=True)
    except Exception as error:
        failure=dict(error_type=type(error).__name__,error=str(error));stage='failed';save();raise


if __name__=='__main__':main()
