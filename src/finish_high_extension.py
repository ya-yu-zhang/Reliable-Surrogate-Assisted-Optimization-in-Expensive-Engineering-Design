"""One authorized dependency chain for high resource checks and 160 formal runs."""
import hashlib,json,os,subprocess
from pathlib import Path
from time import perf_counter,sleep
from .run_solo_cost import process_inventory

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/high_extension_completion_v1'


def main():
    assert not OUT.exists(),'High extension completion record exists; refuse duplicate restart'
    execution=json.loads((ROOT/'docs/frozen_high_evidence_export_v1/sha256.json').read_text('utf-8'))
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==v for n,v in execution.items())
    frozen=json.loads((ROOT/'docs/frozen_application_high_formal_v1/sha256.json').read_text('utf-8'))
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==v for n,v in frozen.items())
    OUT.mkdir(parents=True);start=perf_counter();stage='waiting_for_primary_evidence_export';failure=None
    def save():
        (OUT/'status.json').write_text(json.dumps(dict(stage=stage,pid=os.getpid(),elapsed=perf_counter()-start,
            failure=failure,resource_point_calls=6 if (ROOT/'results/application_high_precheck_analysis_v1/audit.json').exists() else 0,
            full_method_resource_runs=json.loads((ROOT/'results/application_high_method_resource_analysis_v1/audit.json').read_text())['runs'] if (ROOT/'results/application_high_method_resource_analysis_v1/audit.json').exists() else 0,
            formal_runs=json.loads((ROOT/'results/application_high_analysis_v1/audit.json').read_text())['runs'] if (ROOT/'results/application_high_analysis_v1/audit.json').exists() else 0),indent=2),encoding='utf-8')
    def execute(python,module,log):
        result=subprocess.run([str(python),'-m',module],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
        (OUT/log).write_text(result.stdout+result.stderr,encoding='utf-8')
        if result.returncode:raise RuntimeError(f'{module} exited {result.returncode}; retained {log}')
    try:
        save()
        while True:
            prior=json.loads((ROOT/'results/evidence_export_v1/status.json').read_text('utf-8'))
            alive={p['ProcessId'] for p in process_inventory()}
            if prior['stage']=='failed' or prior['failure'] is not None:raise RuntimeError('Primary evidence export failed')
            if prior['stage'] in ['compiled_pending_visual_review','complete'] and prior['pid'] not in alive:break
            if prior['pid'] not in alive:raise RuntimeError('Primary evidence exporter ended before compilation')
            save();sleep(30)
        assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==v for n,v in frozen.items())
        assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==v for n,v in execution.items())
        app=ROOT/'.venv-app/Scripts/python.exe';core=ROOT/'.venv312/Scripts/python.exe'
        stage='six_point_resource_check';save();execute(app,'src.application_high_precheck','six_point_resource.log')
        stage='six_point_resource_audit';save();execute(core,'src.analyze_application_high_precheck','six_point_audit.log')
        stage='eight_full_method_resource_runs';save();execute(app,'src.run_application_high_method_resource','method_resource.log')
        stage='full_method_resource_audit';save();execute(core,'src.analyze_application_high_method_resource','method_resource_audit.log')
        stage='formal_160_runs';save();execute(app,'src.run_application_high_formal','formal_runs.log')
        stage='formal_raw_audit';save();execute(core,'src.analyze_application_high_formal','formal_audit.log')
        stage='complete';save();print('High extension resources, 160 runs, and complete raw audit finished.',flush=True)
    except Exception as error:
        failure=dict(error_type=type(error).__name__,error=str(error));stage='failed';save();raise


if __name__=='__main__':main()
