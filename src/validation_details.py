"""Secondary descriptive validation outputs, only after full integrity audit."""
import os
for key in ['OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ[key] = '1'
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'results/mechanism_validation_analysis_v1'
OUT = ROOT/'results/mechanism_validation_report_v1'


def structure(fid):
    for limit, label in [(5, 'Separable'), (9, 'Low/moderate conditioning'),
                         (14, 'Ill-conditioned unimodal'), (19, 'Structured multimodal'),
                         (24, 'Weakly structured multimodal')]:
        if fid <= limit: return label
    raise ValueError(fid)


def main():
    audit = json.loads((DATA/'full_integrity_audit.json').read_text('utf-8'))
    assert audit['runs'] == 3888 and audit['complete_cartesian_design']
    OUT.mkdir(parents=True, exist_ok=True)
    runs = pd.read_csv(DATA/'runs.csv')
    runs.groupby(['dim', 'fid', 'method']).error.agg(median='median', q25=lambda s:s.quantile(.25),
            q75=lambda s:s.quantile(.75)).to_csv(OUT/'internal_raw_error_iqr.csv')
    scores = pd.read_csv(DATA/'function_scores.csv')
    scores['structure'] = scores.fid.map(structure)
    scores.groupby(['dim', 'structure', 'method']).log_relative_error.mean().to_csv(OUT/'structural_endpoint_scores.csv')
    calibration = pd.read_csv(DATA/'calibration_aggregate_functions.csv')
    selected = calibration[(calibration.group == 'actual_selected') & calibration.calibrator.isin(['T', 'ST'])]
    wide = selected.pivot(index=['dim', 'fid', 'history'], columns='calibrator',
                          values=['quantile_loss', 'margin', 'neff', 'fallback'])
    differences = pd.DataFrame({name:wide[name]['ST']-wide[name]['T']
                               for name in ['quantile_loss', 'margin', 'neff', 'fallback']})
    differences.to_csv(OUT/'localization_function_differences.csv')
    differences.groupby(['dim', 'history']).mean().to_csv(OUT/'localization_description.csv')
    curves, below_floor, exact_optimum = [], 0, 0
    fractions = np.linspace(0, 1, 101)
    for file in sorted((ROOT/'results/mechanism_validation_v1').glob('*/summary.json')):
        summary = json.loads(file.read_text('utf-8')); sig = summary['signature']
        labels = [json.loads(line)['y'] for j, line in enumerate((file.parent/'events.jsonl').read_text('utf-8').splitlines())
                  if j > 0 and j % 2 == 0]
        raw = np.maximum(np.minimum.accumulate(labels)-summary['optimum'], 0)
        # Preserve the frozen AUC convention: floor absolute error BEFORE scaling.
        curve = np.log10(np.maximum(raw, 1e-12)/summary['initial_error'])
        assert np.isclose(curve[summary['n0']-1:].mean(), summary['auc_log_relative'], atol=1e-12)
        below_floor += int(np.sum(curve[summary['n0']-1:] < -12))
        exact_optimum += int(raw[-1] == 0)
        for fraction in fractions:
            t = max(1, int(np.ceil(fraction*sig['budget'])))
            if t < summary['n0']: continue
            curves.append(dict(**{k:sig[k] for k in ['dim', 'fid', 'instance', 'rep', 'method']},
                               fraction=float(fraction), t=t, log_relative_curve=float(curve[t-1])))
    frame = pd.DataFrame(curves)
    instance = frame.groupby(['dim', 'fid', 'instance', 'method', 'fraction']).log_relative_curve.median()
    functions = instance.groupby(['dim', 'fid', 'method', 'fraction']).mean()
    aggregate = functions.groupby(['dim', 'method', 'fraction']).mean().reset_index()
    aggregate.to_csv(OUT/'convergence_curves.csv', index=False)
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.6), sharey=True)
    names = {'greedy':'Greedy', 'fixed01':'Fixed .1', 'fixed03':'Fixed .3',
             'pool_random':'Pool random', 'PEM_T':'PEM-T', 'PEM_ST':'PEM-ST'}
    colors = ['#636363', '#3182bd', '#9ecae1', '#bdbdbd', '#e6550d', '#31a354']
    for ax, dim in zip(axes, [10, 20, 40]):
        for (method, name), color in zip(names.items(), colors):
            group = aggregate[(aggregate.dim == dim) & (aggregate.method == method)]
            ax.plot(group.fraction, group.log_relative_curve, label=name, color=color)
        ax.set_title(f'D={dim}'); ax.set_xlabel('Charged budget fraction'); ax.grid(alpha=.2)
    axes[0].set_ylabel('Function-mean log-relative best-so-far')
    axes[0].legend(fontsize=7); fig.tight_layout()
    fig.savefig(OUT/'convergence_curves.png', dpi=240, bbox_inches='tight')
    fig.savefig(OUT/'convergence_curves.pdf', bbox_inches='tight'); plt.close(fig)
    (OUT/'secondary_metric_conventions.json').write_text(json.dumps(dict(
        endpoint='log10(max(E_B/E_init,1e-12))',
        frozen_auc_and_curve='log10(max(E_t,1e-12)/E_init), t=n0..B inclusive',
        curve_entries_below_minus12=below_floor, runs_ending_at_exact_optimum=exact_optimum,
        floors_differ_at_near_zero=True, no_new_significance_tests=True,
        raw_error_iqr_over_all_9_runs_per_function=True), indent=2), encoding='utf-8')
    print('Convergence, raw IQR, fixed structure groups, and local-bound descriptions generated.')


if __name__ == '__main__':
    main()
