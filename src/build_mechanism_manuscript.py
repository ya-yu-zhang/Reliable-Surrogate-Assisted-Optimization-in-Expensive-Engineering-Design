"""Integrate independently audited evidence into a separate English work draft."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from .build_english_paper import table as basic_table

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'results/mechanism_validation_analysis_v1'
REPORT = ROOT/'results/mechanism_validation_report_v1'


def pvalue(value):
    return f'{value:.2e}' if 0 < value < .0001 else f'{value:.5f}'


def table(frame):
    formatted = frame.copy()
    for name in formatted.columns:
        if str(name).lower().endswith(' p'):
            formatted[name] = formatted[name].map(lambda v:f'{v:.2e}' if 0 < v < .0001 else f'{v:.5f}')
    return basic_table(formatted)


def main():
    audit = json.loads((DATA/'full_integrity_audit.json').read_text('utf-8'))
    assert audit['runs'] == 3888 and audit['diagnostic_evaluations'] == 1990656
    stats = pd.read_csv(DATA/'prespecified_comparisons.csv')
    assert len(stats) == 9 and (stats.functions == 24).all()
    endpoint = stats[stats.comparison == 'P2_endpoint_PEM_T_minus_fixed01'].sort_values('dim')
    descriptions = []
    for row in endpoint.to_dict('records'):
        descriptions.append(f"D={row['dim']}: log difference {row['estimate']:.4f}, "
                            f"geometric error ratio {10**row['estimate']:.3f}, "
                            f"95% bootstrap interval [{row['ci_low']:.4f}, {row['ci_high']:.4f}], "
                            f"Holm p={pvalue(row['holm_p'])}")
    primary = stats[['dim', 'comparison', 'estimate', 'ci_low', 'ci_high', 'positive', 'negative', 'holm_p']].copy()
    primary.comparison = primary.comparison.map({'P1_history_interaction':'History interaction',
        'P2_endpoint_PEM_T_minus_fixed01':'Endpoint T minus .1',
        'P2_step_feedback_minus_mean':'Immediate feedback minus mean'})
    primary.columns = ['D', 'Contrast', 'Estimate', 'CI lower', 'CI upper', 'Positive', 'Negative', 'Holm p']
    selection = pd.read_csv(DATA/'calibration_aggregate.csv')
    selection = selection[(selection.calibrator == 'T') & selection.group.isin(['pool', 'actual_selected'])]
    selection = selection.pivot(index=['dim', 'history'], columns='group', values='failure_rate').reset_index()
    selection = selection[['dim', 'history', 'pool', 'actual_selected']]
    selection.columns = ['D', 'History', 'Pool failure', 'Selected failure']
    closed = pd.read_csv(REPORT/'closed_loop_decision_summary.csv')
    closed = closed[closed.method.isin(['fixed01', 'PEM_T', 'PEM_ST'])]
    closed = closed[['dim', 'method', 'exploration', 'failure', 'claims', 'false', 'fdp']]
    closed.columns = ['D', 'Method', 'Exploration', 'Failure', 'Claims', 'False', 'Pooled FDP']
    declaration_note = '; '.join(f"D={int(r['D'])}: {int(r['Claims'])} declarations, "
                                f"{int(r['False'])} false, pooled FDP {r['Pooled FDP']:.1%}"
                                for r in closed[closed.Method=='PEM_T'].to_dict('records'))
    localized = pd.read_csv(REPORT/'localization_description.csv')
    assert len(localized)==9 and (localized.quantile_loss<0).all()
    support = pd.read_csv(REPORT/'support_by_checkpoint.csv')
    support = support.groupby(['dim', 'calibrator'])[['neff', 'fallback']].mean().reset_index()
    support.columns = ['D', 'Calibrator', 'State mean ESS', 'State mean fallback']
    combined = pd.read_csv(REPORT/'combined_internal_basic_reference_function_scores.csv')
    background = combined.groupby(['dim', 'method']).log_relative_error.mean().unstack().reset_index()
    background = background[['dim', 'fixed01', 'PEM_T', 'PEM_ST', 'sobol', 'cma_es']]
    background.columns = ['D', 'Fixed .1', 'PEM-T', 'PEM-ST', 'Sobol', 'CMA-ES']
    p1 = stats[stats.comparison == 'P1_history_interaction']
    step = stats[stats.comparison == 'P2_step_feedback_minus_mean']
    p1_statement = '; '.join(f"D={int(r.dim)}: {r.estimate:+.4f} (Holm p={r.holm_p:.5f})" for r in p1.itertuples())
    step_statement = '; '.join(f"D={int(r.dim)}: {r.estimate:+.4f} (Holm p={r.holm_p:.5f})" for r in step.itertuples())
    validation = f'''# 8 Independent mechanism validation

## 8.1 Protocol and integrity

After the development gate failed, we froze a separate mechanism protocol before generating any labels on its instances. The algorithms, model, candidates, residual weights, support threshold, and feedback coefficients are unchanged. All 24 BBOB functions, dimensions 10/20/40, instances 11–13, and three repeats are included. Six internal configurations yield 3,888 runs and 907,200 paid evaluations. Three preselected history strategies yield 1,944 histories, 7,776 frozen states, and 1,990,656 additional diagnostic labels. Original instances 6–10 remain reserved. Development and validation estimates are never pooled.

The independent audit checks the complete Cartesian design, seeds, unchanged frozen sources, paid prefixes, original signed residuals, training indices that precede each prediction, selected-point/pool agreement, and separate diagnostic archives. There are {audit['exact_duplicate_calls']} exact repeated internal calls. Training truncation is actually used in {audit['fits_with_training_truncation']} fitted prediction rounds; this is not evidence of general high-dimensional effectiveness. G/T upper-versus-mean diagnostic index disagreements number {len(audit['diagnostic_G_T_ordering_disagreements'])}. The mathematical equivalence below concerns exact real arithmetic, with finite-precision outcomes audited separately.

Three comparisons in each dimension form one nine-test Holm family: the history interaction in selected-minus-pool failures; the PEM-T minus fixed .1 endpoint; and the T-feedback minus mean immediate improvement, with three histories equally weighted. Common-state components are averaged over four states per run, then each component's three-run median is taken before the contrast, followed by instance and function averages. The 4,000-resample paired hierarchical intervals are not multiplicity-adjusted. Function resampling summarizes heterogeneity over this suite; it does not establish a population model for every black-box task.

Table: All nine prespecified comparisons. Endpoint negative favors PEM-T; immediate improvement positive favors feedback. History interaction has no inherent favorable sign.

{table(primary)}

## 8.2 Endpoint and common-state decision effects

The endpoint estimates are {'; '.join(descriptions)}. These ratios summarize equally weighted function-level relative errors and are not ratios shared by every run. Individual-function directions are fully retained in the figure; no function is omitted after observing its result. Immediate feedback-minus-mean effects are {step_statement}. These common-state gains concern the next evaluation only and do not identify a long-run causal pathway.

![All 24 endpoint contrasts in each dimension. Positive means larger PEM-T errors.](../results/mechanism_validation_report_v1/endpoint_function_effects.png)

![Best-so-far curves after common initialization, with each instance's run median followed by equal instance/function averages. All plotted evaluations are charged.](../results/mechanism_validation_report_v1/convergence_curves.png)

The frozen secondary AUC floors absolute error at $10^{{-12}}$ before division by the initial error; the primary endpoint floors the relative ratio afterward. The curves preserve the former convention and are not numerically forced to match the primary endpoint at near-zero errors. The conventions and affected counts are disclosed in the secondary-metric file. No new significance test is added for AUC or curve inspection.

## 8.3 History, declarations, and effective support

The history-interaction estimates are {p1_statement}. This is the fixed .3 selected-minus-pool difference minus the greedy corresponding difference. Across policies, identical seeds do not imply identical candidate pools. These differences describe the coupled history/policy system rather than a fixed-pool causal effect.

Table: Temporal pool and actually selected failure fractions, under the prespecified state/run/instance/function aggregation.

{table(selection)}

![Selected-minus-pool failures by preselected history. A reversal is retained rather than interpreted as universal selection deterioration.](../results/mechanism_validation_report_v1/history_object_differences.png)

Table: Exploration, failures, and declaration denominators in independent closed-loop runs. FDP is pooled false/claims; no-claim FDP is NA.

{table(closed)}

For PEM-T, {declaration_note}. An approximately .1 overall failure fraction does not imply an approximately .1 false-declaration fraction. These small declaration denominators do not establish stable per-declaration probabilities. ST lowers the descriptive selected-point quantile loss in all nine dimension/history cells, yet its closed-loop endpoint remains worse than fixed .1 in every dimension. These are separate diagnostic and trajectory comparisons, not an identified causal relationship.

Table: Descriptive state-mean support across the three preselected history policies and four checkpoints.

{table(support)}

![T/ST effective support at the four actual checkpoint orders. The threshold is an engineering guard and does not guarantee coverage.](../results/mechanism_validation_report_v1/effective_support.png)

The first diagnostic checkpoints are 41/100, 61/200, and 101/400. Sparse declared-pool subsets disclose nonempty states, candidate counts, and failures separately. Localized quantile-loss, margin, ESS, and fallback differences and the five fixed BBOB structure groups are available in full secondary tables; no favorable subgroup becomes a new main result.

## 8.4 External background references

Sobol and pycma CMA-ES retain their own search mechanisms and initialization. Their 1,296 runs and 302,400 paid evaluations passed separate journal audits. For descriptive common-scale comparison only, each external run's final error is divided by the matching internal common-initialization error, and medians are taken after this run-level normalization. The external optimizers never receive those internal labels. This supports budget-matched background comparison, not a same-history causal comparison or reproduction of published SAEA competitors.

Table: Descriptive background endpoint scores over all 24 functions. Lower is better; no additional test family is introduced.

{table(background)}

GP-EI and author TuRBO use separate frozen protocols and strict pre-call budget guards. Their complete outcomes are not included until all runs and audits finish. Author-code restart counterexamples are control-flow checks, not performance observations. Resource precheck instances are excluded from every benchmark table.

'''
    text = (ROOT/'paper/english_development_manuscript.md').read_text('utf-8')
    text = text.replace('subtitle: Development study and mechanism audit — working manuscript',
                        'subtitle: Development and independent mechanism evidence — working manuscript')
    text = text.replace('**Ordering equivalence.** If support', '**Ordering equivalence in exact real arithmetic.** If support')
    text = text.replace('# 8 Discussion', validation+'# 9 Discussion', 1).replace('# 9 Conclusion', '# 10 Conclusion', 1)
    start = 'An independently frozen mechanism validation on all 24 BBOB functions'
    before, separator, remainder = text.partition(start)
    assert separator
    _, marker, after = remainder.partition('\n\n# 10 Conclusion')
    assert marker
    text = before+'''The independent mechanism validation is complete and reported separately from development. The original optimization-improvement gate remains failed, regardless of directions on these new instances. Sobol/CMA-ES background evidence is descriptive; complete GP-EI/TuRBO, competitive SAEA, exclusive resource, and application evidence remain unfinished. Formal external comparisons cannot be inferred from partial live batches. These gaps limit submission readiness.

The real-arithmetic ordering result does not promise identical float64 tie outcomes for arbitrary magnitudes. For example, adding $10^{16}$ to means [1,0] collapses their computed difference and changes the first-index minimizer. This numerical teaching example is not a benchmark result. Observed trajectory identities and the independent diagnostic index audit provide empirical implementation evidence for their respective tested scopes.
'''+marker+after
    text = text.replace('Independent validation and complete competitive/application evidence are still required; this is a working development manuscript.',
                        'Independent mechanism validation now bounds the empirical findings across the full suite and a third dimension. Complete competitive/application evidence is still required; this remains a working manuscript.')
    text = text.replace('a explicitly post-hoc', 'an explicitly post-hoc')
    extra_abstract = ('\n\nA separately frozen validation executes 3,888 internal runs on all 24 functions, '
        'dimensions 10/20/40, and instances 11–13, plus 1,990,656 isolated diagnostic labels. '
        'Its endpoint effects are '+ '; '.join(descriptions)+
        '. All nine prespecified contrasts are reported, with no reversal of the original development gate.')
    text = text.replace('\n\nKeywords:', extra_abstract+'\n\nKeywords:', 1)
    # Keep the development abstract in its historical file; this draft's abstract
    # must communicate independent evidence without listing all intervals twice.
    compact_effects = '; '.join(f"D={int(r.dim)}: ratio {10**r.estimate:.3f}, Holm p={pvalue(r.holm_p)}"
                               for r in endpoint.itertuples())
    abstract = f'''# Abstract

We examine whether one-sided monitoring of evaluated candidates improves objective-evaluation allocation in surrogate-assisted black-box optimization. A candidate-independent additive correction preserves predicted-mean ordering in exact real arithmetic under the specified support and selection rules; floating-point outcomes are audited separately. The main temporal prototype can therefore change decisions through feedback exploration rather than a new ranking. We isolate common-history calibration, common-state immediate utility, and independent closed-loop optimization, with every diagnostic label excluded from optimizer inputs.

The prototype fails its development optimization-benefit gate over eight BBOB functions and dimensions 10/20. We then freeze an unchanged mechanism validation over all 24 functions, dimensions 10/20/40, instances 11–13, and three repeats. It completes 3,888 internal runs, 907,200 paid evaluations, and 1,990,656 additional diagnostic labels. Relative to the development-selected fixed .1 exploration control, independent endpoint effects are {compact_effects}. Nine prespecified contrasts use one Holm family; unadjusted hierarchical intervals and every function direction are disclosed. History-policy differences, immediate gains, improvement-declaration denominators, localized-bound support, and final error are reported separately. Sobol/CMA-ES provide budget-matched descriptive background evidence. The original failed gate remains unchanged. Conclusions concern this frozen decision rule, model, candidate process, and budget, without a coverage theorem or general high-dimensional claim. Complete competitive, resource, and application evidence remains unfinished.
'''
    prefix, abstract_marker, suffix = text.partition('# Abstract')
    assert abstract_marker
    _, keyword_marker, rest = suffix.partition('Keywords:')
    assert keyword_marker
    text = prefix+abstract+'\nKeywords:'+rest
    reproducibility = text.index('# Reproducibility and completion status')
    text = text[:reproducibility]+'''# Reproducibility and completion status

Frozen protocols, source fingerprints, dependency locks, seeds, PRE/LABEL journals, candidate pools, separate diagnostic labels, statistics, and failures are archived. Diagnostic labels never enter optimizers. Repeated executions do not enlarge the optimization sample. Budget counterexamples and post-hoc illustrations are identified separately. Competitive/application/resource evidence remains incomplete.
'''
    path = ROOT/'paper/english_mechanism_manuscript.md'; path.write_text(text, encoding='utf-8')
    sources = [DATA/'audit.json', DATA/'full_integrity_audit.json', DATA/'prespecified_comparisons.csv',
               REPORT/'combined_internal_basic_reference_function_scores.csv', ROOT/'paper/english_development_manuscript.md']
    (ROOT/'paper/english_mechanism_source_hashes.json').write_text(json.dumps(
        {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}, indent=2), encoding='utf-8')
    print(path)


if __name__ == '__main__':
    main()
