"""Serial cost collection; refuse overlap with live scientific batches."""
import argparse
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys
from time import perf_counter, sleep

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ['docs/独占成本预先协议.md', 'configs/solo_cost.json', 'src/solo_cost.py',
           'src/run_solo_cost.py', 'src/analyze_solo_cost.py', 'src/core.py', 'src/experiment.py', 'src/gp_references.py',
           'docs/environment-lock.txt', 'docs/baselines-environment-lock.txt']


def process_inventory():
    shell = Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
    command = 'Get-CimInstance Win32_Process | Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress'
    result = subprocess.run([str(shell), '-NoProfile', '-NonInteractive', '-Command', command],
                            capture_output=True, text=True, encoding='utf-8', errors='replace',
                            creationflags=subprocess.CREATE_NO_WINDOW, check=True)
    entries = json.loads(result.stdout)
    if isinstance(entries, dict): entries = [entries]
    return entries


def refuse_overlap():
    modules = ['src.run_gp_batch', 'src.gp_references', 'src.gp_precheck_pipeline',
               'src.mechanism_pipeline', 'src.experiment', 'src.diagnostics', 'src.basic_references',
               'src.run_solo_cost', 'src.solo_cost']
    active = [p for p in process_inventory() if p['ProcessId'] != os.getpid()
              and any('-m '+module in (p['CommandLine'] or '') for module in modules)]
    if active:
        raise RuntimeError('Scientific processes still active; refusing overlap: '+
                           ','.join(str(p['ProcessId']) for p in active))


def background_cpu():
    def snapshot():
        idle, kernel, user = ctypes.c_ulonglong(), ctypes.c_ulonglong(), ctypes.c_ulonglong()
        if not ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)):
            raise OSError('Unable to measure system CPU')
        return idle.value, kernel.value+user.value
    idle0, total0 = snapshot(); sleep(2); idle1, total1 = snapshot()
    if total1 <= total0: raise RuntimeError('Invalid system CPU sample')
    return max(0., 100*(1-(idle1-idle0)/(total1-total0)))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--config', default='configs/solo_cost.json')
    args = ap.parse_args(); refuse_overlap()
    config = json.loads((ROOT/args.config).read_text('utf-8'))
    assert config == json.loads((ROOT/'configs/solo_cost.json').read_text('utf-8'))
    fingerprints = {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCES}
    for path in sorted((ROOT/'literature/source-code/TuRBO/turbo').glob('*.py')):
        fingerprints[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    frozen = json.loads((ROOT/'docs/frozen_solo_cost_v1/sha256.json').read_text('utf-8'))
    assert fingerprints == frozen, 'Cost measurement source differs from frozen protocol'
    out = ROOT/config['out']; out.mkdir(parents=True, exist_ok=True)
    manifest = dict(config=config, fingerprints=fingerprints, logical_cpu_count=os.cpu_count(),
                    hardware=json.loads((ROOT/'docs/hardware.json').read_text('utf-8')))
    path = out/'manifest.json'
    if path.exists(): assert json.loads(path.read_text('utf-8')) == manifest
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    jobs = [(f,d,i,r,m) for f in config['functions'] for d in config['dimensions']
            for i in config['instances'] for r in range(config['repeats']) for m in config['methods']]
    random.Random(config['order_seed']).shuffle(jobs)
    records = []; failure = None; start = perf_counter()
    try:
        for f,d,i,r,m in jobs:
            budget = config['budget_multiplier']*d
            runid = f'{m}_f{f:02}_d{d}_i{i}_r{r}_b{budget}'
            measurement = out/runid/'measurement.json'
            if measurement.exists():
                record = json.loads(measurement.read_text('utf-8'))
                assert record['fingerprints'] == fingerprints
                records.append(record); continue
            refuse_overlap(); cpu = background_cpu(); refuse_overlap()
            if cpu > config['max_background_cpu_percent']:
                raise RuntimeError(f'Background CPU {cpu:.2f}% exceeds frozen threshold')
            directory = out/runid
            if (directory/'summary.json').exists():
                raise RuntimeError('Incomplete timing with completed science: preserve and use a new output protocol')
            environment = '.venv-baselines' if m in ['gp_ei','turbo_1'] else '.venv312'
            command = [str(ROOT/environment/'Scripts/python.exe'), '-m', 'src.solo_cost',
                       '--fid', str(f), '--dim', str(d), '--instance', str(i), '--rep', str(r),
                       '--method', m, '--budget', str(budget), '--out', str(out)]
            began = datetime.now(timezone.utc).isoformat(); tick = perf_counter()
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                                    encoding='utf-8', errors='replace')
            e2e = perf_counter()-tick
            (out/(runid+'.log')).write_text(result.stdout+result.stderr, encoding='utf-8')
            if result.returncode: raise RuntimeError(f'{runid} failed; see retained log')
            cost = json.loads((directory/'cost.json').read_text('utf-8'))
            summary = json.loads((directory/'summary.json').read_text('utf-8'))
            assert summary['algorithm_evaluations'] == budget and e2e >= cost['wrapper_execution_seconds']
            assert cost['summary_sha256'] == hashlib.sha256((directory/'summary.json').read_bytes()).hexdigest()
            record = dict(runid=runid, fid=f, dim=d, instance=i, rep=r, method=m, budget=budget,
                          started_utc=began, pre_run_background_cpu_percent=cpu,
                          end_to_end_seconds=e2e, fingerprints=fingerprints, **{k:v for k,v in cost.items() if k != 'runid'})
            measurement.write_text(json.dumps(record, indent=2), encoding='utf-8'); records.append(record)
            print(f'{len(records)}/{len(jobs)} independent serial measurements', flush=True)
    except Exception as error:
        failure = dict(error=str(error), completed=len(records)); raise
    finally:
        (out/'status.json').write_text(json.dumps(dict(stage='failed' if failure else 'complete',
            pid=os.getpid(), completed=len(records), expected=len(jobs), elapsed=perf_counter()-start,
            failure=failure), indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
