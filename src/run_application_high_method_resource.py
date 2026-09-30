"""Serial fresh-process resource design; never overwrite cached console records."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
from time import perf_counter
from .application_high_precheck import prerequisite
from .application_journal_audit import audit_journal
from .run_solo_cost import process_inventory

ROOT = Path(__file__).resolve().parents[1]
CONFIG = 'configs/application_high_method_resource.json'


def main():
    prerequisite()
    for p in process_inventory():
        if p['ProcessId'] not in [os.getpid(), os.getppid()]:
            assert not any('-m '+m in (p['CommandLine'] or '') for m in
                           ['src.run_application_high_method_resource','src.application_high_method_resource']), 'Resource design already active'
    config = json.loads((ROOT / CONFIG).read_text('utf-8'))
    frozen = json.loads((ROOT / config['freeze_manifest']).read_text('utf-8'))
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == value for name,value in frozen.items())
    phase_one = json.loads((ROOT/'results/application_high_precheck_analysis_v1/audit.json').read_text('utf-8'))
    assert phase_one['complete_resource_point_design'] and phase_one['source_hashes_verified']
    out = ROOT/config['out']; out.mkdir(parents=True,exist_ok=True)
    manifest = dict(config=config,frozen_sources=frozen,worker_limit=1,resource_only=True)
    file = out/'manifest.json'
    if file.exists():
        assert json.loads(file.read_text('utf-8')) == manifest
    else:
        file.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    completed = 0; failure = None; start = perf_counter()
    def save(stage):
        (out/'status.json').write_text(json.dumps(dict(stage=stage,pid=os.getpid(),completed=completed,
            expected=8,failed=int(failure is not None),failure=failure,elapsed=perf_counter()-start),indent=2),encoding='utf-8')
    try:
        save('running')
        for method in config['methods']:
            directory = out/method
            if not (directory/'summary.json').exists():
                result = subprocess.run([str(ROOT/'.venv-app/Scripts/python.exe'),'-m',
                    'src.application_high_method_resource','--method',method],cwd=ROOT,capture_output=True,
                    text=True,encoding='utf-8',errors='replace')
                log = out/(method+'.log')
                # An incomplete run must not destroy the previous diagnostic console record.
                if log.exists():
                    log = out/(method+f'.attempt-{os.getpid()}.log')
                with log.open('x',encoding='utf-8') as stream:
                    stream.write(result.stdout+result.stderr)
                if result.returncode:
                    raise RuntimeError(f'{method}: exit {result.returncode}; retained {log.name}')
            summary = json.loads((directory/'summary.json').read_text('utf-8'))
            sig = summary['signature']
            assert sig['frozen_sources'] == frozen and sig['budget'] == 1000 and sig['dim'] == 300
            assert sig['data_seed'] == 90043 and sig['rep'] == 0 and sig['method'] == method
            assert sig['seed'] == 100000*300+1000*4+10*90043
            assert summary['test_method_calls'] == 0 and not summary['formal_application_result']
            audit_journal(directory,summary)
            completed += 1; save('running')
            print(f'{completed}/8 resource runs structurally audited',flush=True)
        save('complete')
    except Exception as error:
        failure = dict(error_type=type(error).__name__,error=str(error)); save('failed'); raise


if __name__ == '__main__':
    main()
