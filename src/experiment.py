"""Execution and immutable pre-evaluation event journal, separate from core."""
import os
# Avoid 16 BLAS threads in EACH worker; set before numpy/scipy imports.
for _key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[_key] = '1'
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path
from time import perf_counter
import hashlib
import io
import json
import platform
import traceback
import zipfile
import numpy as np
import ioh
from scipy.stats import qmc
from .core import (Settings, GaussianRBF, init_design, make_candidates, bounds,
                   management, choose, METHODS, seed_stream)

ROOT = Path(__file__).resolve().parents[1]


def code_hash():
    h = hashlib.sha256()
    for file in sorted((ROOT/'src').glob('*.py')):
        if file.name in {'core.py', 'experiment.py'}:
            h.update(file.name.encode()); h.update(file.read_bytes())
    return h.hexdigest()


def problem(fid, dim, instance):
    return ioh.get_problem(fid, instance=instance, dimension=dim, problem_class=ioh.ProblemClass.BBOB)


def json_line(file, item):
    file.write(json.dumps(item, ensure_ascii=False, allow_nan=False) + '\n')
    file.flush()


def write_array(archive, name, array):
    buffer = io.BytesIO()
    np.save(buffer, array, allow_pickle=False)
    archive.writestr(name+'.npy', buffer.getvalue())


def run_one(job):
    fid, dim, instance, rep, method, budget, out, capture = job
    cfg = Settings()
    seed = 100000*dim + 1000*fid + 10*instance + rep
    runid = f'{method}_f{fid:02}_d{dim}_i{instance}_r{rep}_b{budget}'
    directory = Path(out)/runid
    directory.mkdir(parents=True, exist_ok=True)
    summary_path = directory/'summary.json'
    signature = dict(code_hash=code_hash(), fid=fid, dim=dim, instance=instance, rep=rep,
                     method=method, budget=budget, seed=seed, settings=asdict(cfg), capture=capture)
    if summary_path.exists():
        previous = json.loads(summary_path.read_text('utf-8'))
        if previous['signature'] != signature:
            raise RuntimeError(f'Stale results: {directory}; use a new output directory.')
        return previous
    objective = problem(fid, dim, instance)
    lb, ub = np.array(objective.bounds.lb), np.array(objective.bounds.ub)
    design = init_design(dim, seed)
    ntrain, n0 = dim+10, 2*dim+20
    if budget < n0:
        raise ValueError('Budget must include full initialization.')
    x, y, residuals, monitors = [], [], [], []
    stagnation = 0
    timers = dict(train=0., candidates=0., calibrate=0., choose=0., objective=0., journal=0.)
    archive = zipfile.ZipFile(directory/'candidate_pools.npz', 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=1)
    checkpoints = sorted(set([max(n0+1, int(np.ceil(budget*f))) for f in (.25,.5,.75,1)]))
    start = perf_counter()
    variant, manager, use_upper, fixed = METHODS[method]
    if method == 'T_fixed':
        # Configured fixed probability is substituted by runner after development selection.
        fixed = float(os.environ.get('PEM_FIXED_P', '0.3'))
    with (directory/'events.jsonl').open('w', encoding='utf-8') as journal:
        json_line(journal, dict(event='meta', **signature, lb=lb.tolist(), ub=ub.tolist(),
                                checkpoints=checkpoints, schema=1))
        for t in range(1, budget+1):
            best = min(y) if y else None
            pred, bound, state, pool = None, None, None, None
            pre = dict(event='pre', t=t, n_observed=len(y), best_before=best)
            if t <= ntrain:
                point = design[t-1]
                pre.update(mode='initial_train', mu=None, H=None, scale=None,
                           declared=False, monitoring_ready=False)
            else:
                xx, yy = np.array(x), np.array(y)
                t0 = perf_counter(); model = GaussianRBF(cfg).fit(xx, yy)
                timers['train'] += perf_counter()-t0
                if t <= n0:
                    point = design[t-1]
                    pool = np.array([point])
                    mode, u, random_state = 'startup', None, None
                    k = 0
                else:
                    t0 = perf_counter(); pool = make_candidates(xx, yy, seed, t, cfg)
                    timers['candidates'] += perf_counter()-t0
                t0 = perf_counter(); pred = model.predict(pool)
                bound = bounds(pred, model.scale, pool, residuals, t, variant, cfg)
                timers['calibrate'] += perf_counter()-t0
                state = management(monitors, stagnation, manager, fixed, cfg)
                if method == 'pool_random':
                    state['random_candidate'] = True
                if t > n0:
                    t0 = perf_counter()
                    k, mode, u, random_state = choose(pool, xx, pred, bound, best, model.scale,
                                                    state, seed, t, use_upper, cfg)
                    timers['choose'] += perf_counter()-t0
                    point = pool[k]
                # Declaration is a monitored event independent of the selected MODE.
                declared = bool(state['monitoring_ready'] and bound['support'][k]
                                and bound['H'][k] < best-cfg.tau_factor*model.scale)
                pre.update(mu=float(pred[k]), H=float(bound['H'][k]), scale=model.scale,
                           margin=float(bound['q'][k]), neff=float(bound['neff'][k]),
                           support=bool(bound['support'][k]), calibrator=str(bound['used'][k]),
                           variant=variant, weighted_distance=None if np.isnan(bound['weighted_distance'][k]) else float(bound['weighted_distance'][k]),
                           mode=mode, declared=declared, stagnation=stagnation,
                           train_indices=model.indices.tolist(), **state,
                           selection_index=k, mode_uniform=u, mode_rng_after=random_state,
                           candidate_stream=[seed,21,t], sobol_stream=[seed,22,t])
            pre['x_unit'] = point.tolist()
            pre['x'] = (lb+(ub-lb)*point).tolist()
            # Persist pool and pre-state BEFORE requesting the objective label.
            t0 = perf_counter()
            if pool is not None and t > n0 and (capture == 'all' or t in checkpoints):
                write_array(archive, f't{t}_points', pool)
                write_array(archive, f't{t}_mu', pred)
                write_array(archive, f't{t}_H', bound['H'])
                archive.fp.flush()
            json_line(journal, pre)
            timers['journal'] += perf_counter()-t0
            t0 = perf_counter(); value = float(objective(pre['x']))
            timers['objective'] += perf_counter()-t0
            if not np.isfinite(value):
                raise FloatingPointError(f'Nonfinite objective {runid} t={t}')
            post = dict(event='label', t=t, y=value, best_after=value if best is None else min(best,value))
            if pre['mu'] is not None:
                r = (value-pre['mu'])/pre['scale']
                failed = value > pre['H']
                false_claim = bool(pre['declared'] and value >= best-cfg.tau_factor*pre['scale'])
                if false_claim and not failed:
                    raise AssertionError('Violation of false claim subset relation.')
                post.update(residual=r, upper_failure=failed, false_claim=false_claim,
                            improvement=max(0., best-value),
                            significant_improvement=value < best-cfg.tau_factor*pre['scale'])
                residuals.append((t, point.copy(), r))
                monitors.append((float(failed), pre['margin']))
                stagnation = 0 if post['significant_improvement'] else stagnation+1
            x.append(point.copy()); y.append(value)
            json_line(journal, post)
    archive.close()
    if objective.state.evaluations != budget:
        raise AssertionError('Objective counter differs from charged budget.')
    optimum = float(objective.optimum.y)
    initial_error = max(min(y[:n0])-optimum, 1e-12)
    error = max(min(y)-optimum,0.)
    norm_curve = np.maximum(np.minimum.accumulate(y)[n0-1:]-optimum, 1e-12)/initial_error
    summary = dict(signature=signature, runid=runid, optimum=optimum, best=min(y), error=error,
                   normalized_error=error/initial_error, log_relative_error=float(np.log10(max(error/initial_error,1e-12))),
                   initial_error=initial_error, auc_log_relative=float(np.mean(np.log10(norm_curve))),
                   algorithm_evaluations=budget, diagnostic_evaluations=0,
                   elapsed=perf_counter()-start, timers=timers, n0=n0, seed=seed)
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text('utf-8'))
    out = ROOT/config['out']; out.mkdir(parents=True, exist_ok=True)
    manifest = dict(config=config, hash=code_hash(), python=platform.python_version(),
                    platform=platform.platform(), ioh=__import__('importlib.metadata', fromlist=['version']).version('ioh'),
                    settings=asdict(Settings()))
    mf = out/'manifest.json'
    if mf.exists() and json.loads(mf.read_text('utf-8')) != manifest:
        raise RuntimeError('Manifest mismatch; use a new output directory.')
    mf.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    jobs = [(f,d,i,r,m,config.get('budget_multiplier',10)*d,str(out),config.get('capture','checkpoints'))
            for f in config['functions'] for d in config['dimensions'] for i in config['instances']
            for r in range(config['repeats']) for m in config['methods']]
    count=0; errors=[]; start=perf_counter()
    print(f'{len(jobs)} runs; {config.get("workers",4)} workers; output={out}',flush=True)
    with ProcessPoolExecutor(max_workers=config.get('workers',4)) as executor:
        futures={executor.submit(run_one,j):j for j in jobs}
        for fut in as_completed(futures):
            count+=1
            try:
                fut.result()
            except Exception:
                errors.append(dict(job=futures[fut], traceback=traceback.format_exc()))
                print(errors[-1]['traceback'],flush=True)
            if count%20==0 or count==len(jobs):
                print(f'{count}/{len(jobs)}; failed={len(errors)}; seconds={perf_counter()-start:.1f}',flush=True)
    (out/'failures.json').write_text(json.dumps(errors,indent=2),encoding='utf-8')
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
