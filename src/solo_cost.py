"""Fresh-process timing around unchanged scientific implementations."""
import os
for key in ['OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ[key] = '1'
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import platform
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]


def memory_peak():
    class Counters(ctypes.Structure):
        _fields_ = [('cb', ctypes.c_uint32), ('PageFaultCount', ctypes.c_uint32)] + [
            (name, ctypes.c_size_t) for name in ['PeakWorkingSetSize', 'WorkingSetSize',
             'QuotaPeakPagedPoolUsage', 'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage',
             'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage']]
    counter = Counters(); counter.cb = ctypes.sizeof(counter)
    handle = ctypes.windll.kernel32.GetCurrentProcess; handle.restype = ctypes.c_void_p
    info = ctypes.windll.psapi.GetProcessMemoryInfo
    info.argtypes = [ctypes.c_void_p, ctypes.POINTER(Counters), ctypes.c_uint32]
    if not info(handle(), ctypes.byref(counter), counter.cb):
        raise OSError('Unable to measure process memory')
    return int(counter.PeakWorkingSetSize)


def main():
    ap = argparse.ArgumentParser()
    for key in ['fid', 'dim', 'instance', 'rep', 'budget']:
        ap.add_argument('--'+key, type=int, required=True)
    ap.add_argument('--method', required=True); ap.add_argument('--out', required=True)
    args = ap.parse_args()
    runid = f'{args.method}_f{args.fid:02}_d{args.dim}_i{args.instance}_r{args.rep}_b{args.budget}'
    directory = Path(args.out)/runid
    if (directory/'summary.json').exists():
        raise RuntimeError('Cached scientific result cannot be measured as a fresh run')
    if args.method in ['gp_ei', 'turbo_1']:
        from .gp_references import run_one
        start = perf_counter()
        summary = run_one(args.fid, args.dim, args.instance, args.rep, args.method,
                          args.budget, args.out)
    else:
        from . import experiment
        run_one = experiment.run_one
        original_write = experiment.json_line
        preparations = []; last_label_end = perf_counter()
        def observe_write(journal, item):
            nonlocal last_label_end
            if item['event'] == 'pre':
                preparations.append(perf_counter()-last_label_end)
            original_write(journal, item)
            if item['event'] == 'label':
                last_label_end = perf_counter()
        experiment.json_line = observe_write
        start = perf_counter()
        try:
            summary = run_one((args.fid, args.dim, args.instance, args.rep, args.method,
                               args.budget, args.out, 'checkpoints'))
        finally:
            experiment.json_line = original_write
    assert summary['algorithm_evaluations'] == args.budget
    cost = dict(runid=runid, wrapper_execution_seconds=perf_counter()-start,
                process_peak_working_set_bytes=memory_peak(), python=platform.python_version(),
                wrapper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                summary_sha256=hashlib.sha256((directory/'summary.json').read_bytes()).hexdigest())
    if args.method not in ['gp_ei', 'turbo_1']:
        assert len(preparations) == args.budget
        cost['preparation_seconds'] = preparations
        cost['post_initialization_index'] = summary['n0']
    else:
        cost['preparation_seconds'] = summary['preparation_seconds']
        cost['post_initialization_index'] = 2*args.dim
    (directory/'cost.json').write_text(json.dumps(cost, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
