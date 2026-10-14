"""Rebuild the computational figure from saved timings, without retiming or solving."""
from pathlib import Path
import csv

def rebuild(root, dest):
    (dest/"figures").mkdir(parents=True,exist_ok=True)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from collections import Counter
    with (root/'results/gp_envelope_acceleration_20261014/paired_timing.csv').open() as stream:
        rows = list(csv.DictReader(stream))
    plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False,
                         'pdf.fonttype': 42, 'ps.fonttype': 42})
    fig, axes = plt.subplots(1, 2, figsize=(7.3, 2.75), constrained_layout=True)
    colors = {'archived_common_mean': '#2563a6', 'previous_holdout': '#c76625'}
    for dataset, label in [('archived_common_mean', 'Archived mean'), ('previous_holdout', 'Previous mean')]:
        part = [r for r in rows if r['dataset'] == dataset]
        axes[0].scatter([float(r['pairwise_seconds']) for r in part], [float(r['envelope_seconds']) for r in part],
                        s=13, alpha=.65, color=colors[dataset], label=label)
    extent = max(float(r['pairwise_seconds']) for r in rows)*1.1
    axes[0].plot([0, extent], [0, extent], '--', color='.5', linewidth=.8)
    axes[0].set(xlabel='Pairwise construction (seconds)', ylabel='Exact envelope (seconds)',
                xlim=(0, extent), ylim=(0, extent))
    axes[0].legend(frameon=False, fontsize=8)
    first_domain = [r for r in rows if r['range'] == 'nonnegative']
    counts = Counter(int(r['kept']) for r in first_domain)
    axes[1].bar(list(range(2, 8)), [counts[k] for k in range(2, 8)], color='#2563a6', width=.68)
    axes[1].set(xlabel='Retained actions from each 1024-point pool', ylabel='Distinct branches', xticks=range(2, 8))
    for ax in axes:
        ax.grid(axis='y', alpha=.16); ax.set_axisbelow(True)
    fig.savefig(dest/'figures/gp_certified_envelope_comparison.pdf', metadata={'CreationDate': None, 'ModDate': None})
    plt.close(fig)

if __name__ == "__main__":
    rebuild(Path(__file__).resolve().parents[1], Path(__file__).resolve().parents[1]/"paper/engineering_optimization")
