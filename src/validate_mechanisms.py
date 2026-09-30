"""Pre-specified independent mechanism validation; no parameter selection."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon
from .analyze import holm, function_scores
from .diagnostics import load_events

HISTORIES = ['fixed03', 'greedy', 'pool_random']


def summarize_components(frame, columns, weights, dim, repeats=4000):
    """Median EACH component within instance before making the contrast."""
    data = frame[frame.dim == dim]
    assert not data[columns].isna().any().any()
    instance = data.groupby(['fid', 'instance'])[columns].median()
    functions = instance.groupby('fid').mean()
    differences = functions.to_numpy() @ np.asarray(weights)
    fids = functions.index.tolist()
    arrays = {f: {i: g[columns].to_numpy() for i, g in data[data.fid == f].groupby('instance')}
              for f in fids}
    rng = np.random.default_rng(921701 + dim)
    estimates = []
    for _ in range(repeats):
        values = []
        for f in rng.choice(fids, len(fids), replace=True):
            instances = arrays[f]
            iv = []
            for i in rng.choice(list(instances), len(instances), replace=True):
                rr = instances[i]
                selected = rr[rng.integers(len(rr), size=len(rr))]
                iv.append(np.median(selected, axis=0) @ weights)
            values.append(np.mean(iv))
        estimates.append(np.mean(values))
    p = 1.0 if np.all(differences == 0) else float(wilcoxon(differences, zero_method='wilcox').pvalue)
    ci = np.quantile(estimates, [.025, .975])
    result = dict(dim=dim, estimate=float(np.mean(differences)), ci_low=float(ci[0]), ci_high=float(ci[1]),
                  p=p, positive=int(np.sum(differences > 0)), negative=int(np.sum(differences < 0)),
                  zero=int(np.sum(differences == 0)), functions=len(fids))
    return result, pd.DataFrame(dict(dim=dim, fid=fids, contrast=differences))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', required=True)
    ap.add_argument('--diagnostics', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    source, diag, out = map(Path, [args.source, args.diagnostics, args.out])
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((source/'manifest.json').read_text('utf-8'))
    config = manifest['config']
    expected = len(config['functions'])*len(config['dimensions'])*len(config['instances'])*config['repeats']*len(config['methods'])
    files = sorted(source.glob('*/summary.json'))
    assert len(files) == expected == 3888
    assert not json.loads((source/'failures.json').read_text('utf-8'))
    runs, metrics, initialization = [], [], {}
    charged = 0
    for file in files:
        summary = json.loads(file.read_text('utf-8'))
        sig = summary['signature']
        assert sig['code_hash'] == manifest['hash']
        meta, pre, labels = load_events(file.parent)
        assert len(pre) == sig['budget'] == summary['algorithm_evaluations']
        charged += len(pre)
        key = tuple(sig[k] for k in ['fid', 'dim', 'instance', 'rep'])
        init = [(a['x_unit'], b['y'], a['mu']) for a, b in zip(pre, labels)][:summary['n0']]
        if key in initialization:
            assert init == initialization[key]
        else:
            initialization[key] = init
        base = {k:sig[k] for k in ['fid', 'dim', 'instance', 'rep', 'method']}
        runs.append(dict(**base, **{k:summary[k] for k in ['error', 'initial_error', 'log_relative_error', 'elapsed', 'auc_log_relative']}))
        pairs = [(a,b) for a,b in zip(pre,labels) if a['t'] > summary['n0']]
        claims = sum(a['declared'] for a,b in pairs)
        false = sum(b['false_claim'] for a,b in pairs)
        assert all(not b['false_claim'] or b['upper_failure'] for a,b in pairs)
        metrics.append(dict(**base, claims=claims, false_claims=false, fdp=false/claims if claims else np.nan,
                            explore_frequency=np.mean([a['mode']=='explore' for a,b in pairs]),
                            upper_failure=np.mean([b['upper_failure'] for a,b in pairs]),
                            margin=np.mean([a['margin'] for a,b in pairs])))
    runframe, metricframe = pd.DataFrame(runs), pd.DataFrame(metrics)
    runframe.to_csv(out/'runs.csv', index=False)
    metricframe.to_csv(out/'closed_loop_metrics.csv', index=False)
    scores = function_scores(runframe)
    scores.to_csv(out/'function_scores.csv', index=False)
    scores.groupby(['dim','method']).log_relative_error.mean().to_csv(out/'endpoint_scores.csv')
    cframes, dframes = [], []
    counts, diagnostic_labels = 0, 0
    for file in sorted(diag.glob('*/count.json')):
        if not any(file.parent.name.startswith(h+'_') for h in HISTORIES):
            continue
        count = json.loads(file.read_text('utf-8'))
        directory = source/file.parent.name
        assert hashlib.sha256((directory/'events.jsonl').read_bytes()).hexdigest() == count['manifest']['source_hash']
        assert count['manifest']['fixed'] == .3
        assert count['states'] == 4 and count['diagnostic_evaluations'] == 1024
        counts += 1
        diagnostic_labels += count['diagnostic_evaluations']
        cframes.append(pd.read_csv(file.parent/'calibration.csv'))
        dframes.append(pd.read_csv(file.parent/'decisions.csv'))
    assert counts == expected//2 == 1944
    calibration, decisions = pd.concat(cframes,ignore_index=True), pd.concat(dframes,ignore_index=True)
    calibration.to_csv(out/'calibration_states.csv', index=False)
    decisions.to_csv(out/'decision_states.csv', index=False)
    ix = ['dim','fid','instance','rep']
    # State mean -> run median per instance -> instance mean -> function mean.
    crun = calibration.groupby(ix+['history','calibrator','group'],as_index=False)[['failure_rate','quantile_loss','margin','neff','fallback']].mean()
    drun = decisions.groupby(ix+['history','calibrator','strategy'],as_index=False)[['normalized_improvement','opportunity_loss']].mean()
    for name, frame, groups, values in [
        ('calibration_aggregate',crun,['history','calibrator','group'],['failure_rate','quantile_loss','margin','neff','fallback']),
        ('single_step_aggregate',drun,['history','calibrator','strategy'],['normalized_improvement','opportunity_loss'])]:
        instance = frame.groupby(['dim','fid','instance']+groups)[values].median()
        function = instance.groupby(['dim','fid']+groups).mean()
        function.to_csv(out/f'{name}_functions.csv')
        function.groupby(['dim']+groups).mean().to_csv(out/f'{name}.csv')
    rare = calibration[calibration.group=='pool_declared'].copy()
    rare['nonempty'] = rare.n > 0
    rare = rare.groupby(['dim','history','calibrator']).agg(states=('n','size'), nonempty_states=('nonempty','sum'),
                                                         candidates=('n','sum'), failures=('failures','sum'))
    rare['pooled_failure'] = rare.failures/rare.candidates.replace(0,np.nan)
    rare.to_csv(out/'sparse_declarations.csv')
    endpoint = runframe.pivot(index=ix,columns='method',values='log_relative_error').reset_index()
    c = crun[(crun.calibrator=='T') & crun.group.isin(['actual_selected','pool'])]
    cw = c.pivot(index=ix,columns=['history','group'],values='failure_rate')
    cw.columns = ['__'.join(v) for v in cw.columns]
    cw = cw.reset_index()
    d = drun[(drun.calibrator=='T') & drun.strategy.isin(['feedback','mean'])]
    dw = d.pivot(index=ix,columns=['history','strategy'],values='normalized_improvement')
    dw.columns = ['__'.join(v) for v in dw.columns]
    dw = dw.reset_index()
    contrasts = [
        ('P1_history_interaction',cw,['fixed03__actual_selected','fixed03__pool','greedy__actual_selected','greedy__pool'],[1,-1,-1,1]),
        ('P2_endpoint_PEM_T_minus_fixed01',endpoint,['PEM_T','fixed01'],[1,-1]),
        ('P2_step_feedback_minus_mean',dw,[h+'__'+s for h in HISTORIES for s in ['feedback','mean']],[1/3,-1/3]*3)]
    results, functions = [], []
    for name, frame, columns, weights in contrasts:
        for dim in config['dimensions']:
            result, ff = summarize_components(frame, columns, np.asarray(weights), dim)
            result['comparison'] = name
            ff['comparison'] = name
            results.append(result)
            functions.append(ff)
    statistics = pd.DataFrame(results)
    statistics['holm_p'] = holm(statistics.p.to_numpy())
    statistics.to_csv(out/'prespecified_comparisons.csv', index=False)
    pd.concat(functions,ignore_index=True).to_csv(out/'prespecified_function_contrasts.csv', index=False)
    audit = dict(executed_runs=len(files), algorithm_evaluations=charged, diagnostic_histories=counts,
                 diagnostic_states=counts*4, diagnostic_evaluations=diagnostic_labels,
                 all_initializations_equal=True, source_journals_unchanged=True,
                 future_labels_in_pre=False, protocol='docs/机制验证预先协议.md',
                 validation_instances=config['instances'], development_results_not_pooled=True,
                 original_confirmation_instances_unopened=True)
    assert charged == 907200 and diagnostic_labels == 1990656
    (out/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    print(statistics.to_string(index=False))


if __name__ == '__main__':
    main()
