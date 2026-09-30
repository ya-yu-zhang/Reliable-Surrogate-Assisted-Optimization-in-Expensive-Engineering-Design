"""English development manuscript generated from audited stage-one tables."""
import hashlib
import json
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'results/analysis_v1'


def table(frame):
    formatted=frame.copy()
    for column in formatted:
        formatted[column]=formatted[column].map(lambda value:'NA' if pd.isna(value) else f'{value:.4f}' if isinstance(value,float) else str(value))
    return '\n'.join(['| '+' | '.join(formatted.columns)+' |','| '+' | '.join(['---']*len(formatted.columns))+' |']+
                     ['| '+' | '.join(row)+' |' for row in formatted.itertuples(index=False,name=None)])


def main():
    audit=json.loads((DATA/'audit.json').read_text('utf-8'))
    gate=json.loads((DATA/'gate.json').read_text('utf-8'))
    assert audit['audited_runs']==1872 and not gate['full_gate_passed']
    paired=pd.read_csv(DATA/'paired_comparisons.csv')
    endpoints=pd.read_csv(DATA/'endpoint_scores.csv')
    closed=pd.read_csv(DATA/'closed_loop_metrics.csv')
    calibration=pd.read_csv(DATA/'calibration_aggregate.csv')
    step=pd.read_csv(DATA/'single_step_aggregate.csv')
    selected=paired[paired.comparator=='fixed01'].sort_values('dim')
    assert len(selected)==2
    r10,r20=selected.to_dict('records')
    abstract=f'''Across eight preselected BBOB functions, dimensions 10 and 20, and instances 1–3, we execute 1,872 closed-loop runs and 432 common histories, with 442,368 separate diagnostic labels. Relative to the fixed .1 exploration control selected on development data, the temporal prototype has function-level geometric endpoint-error ratios of {r10['error_ratio_geometric']:.3f} and {r20['error_ratio_geometric']:.3f}; each dimension has zero wins and eight losses. Both Holm-adjusted p-values are {r10['p_holm']:.5f}, so the directional failure does not establish a multiplicity-adjusted significant deterioration. Two equivalence audits each recover 144/144 identical trajectories. Common-history diagnostics show history-dependent differences between monitoring objects, while partial improvements in spatial quantile loss do not yield overall closed-loop benefits. The prototype fails the optimization-benefit development gate. We retain a bounded mechanism and failure analysis without a coverage theorem or a general high-dimensional claim.'''
    methods=['greedy','fixed01','PEM_T','PEM_ST','error_only','stagnation_only']
    endpoint=endpoints[endpoints.method.isin(methods)].pivot(index='dim',columns='method',values='log_relative_error').reindex(columns=methods).reset_index()
    endpoint.columns=['D','Greedy','Fixed .1','PEM-T','PEM-ST','Error only','Stagnation']
    effects=selected[['dim','mean_log_delta','error_ratio_geometric','wins','losses','p_holm']].copy()
    effects.columns=['D','Log difference','Geometric ratio','Wins','Losses','Holm p']
    intervals='; '.join(f"D={r['dim']}: [{r['ci_low']:.3f}, {r['ci_high']:.3f}]" for r in [r10,r20])
    declaration=closed[closed.method.isin(methods[1:])].groupby(['dim','method']).agg(claims=('claims','sum'),false=('false_claims','sum'),explore=('explore_frequency','mean'),failure=('upper_failure','mean')).reset_index()
    declaration['FDP']=declaration.false/declaration.claims.replace(0,float('nan'))
    declaration=declaration[['dim','method','explore','failure','claims','false','FDP']]
    declaration.columns=['D','Method','Exploration','Failure','Claims','False','Pooled FDP']
    c=calibration[(calibration.calibrator=='T') & calibration.group.isin(['pool','top10','actual_selected'])].pivot(index=['dim','history'],columns='group',values='failure').reset_index()
    c=c[['dim','history','pool','top10','actual_selected']]
    c.columns=['D','History','Pool','Top 10%','Actually selected']
    local=calibration[calibration.group=='actual_selected'].groupby(['dim','calibrator'])[['loss','margin','neff','fallback']].mean().reset_index()
    local.columns=['D','Calibrator','Quantile loss','Margin','ESS','Fallback']
    single=step[step.calibrator=='T'].pivot(index=['dim','history'],columns='strategy',values='improvement').reset_index()[['dim','history','mean','fixed','feedback']]
    single.columns=['D','History','Mean','Fixed .3','Feedback']
    assert audit['equivalence']['PEM_T == no_upper']['identical_runs']==144
    assert audit['equivalence']['fixed03 == T_fixed']['identical_runs']==144
    results=f'''## 7.1 Completion and event audits

All 1,872 development runs complete without exceptions, charging 280,800 objective calls. The 432 common histories charge 64,800 calls. Their four checkpoints yield 1,728 states and 442,368 separate diagnostic labels. The two batches therefore execute 2,304 runs and 345,600 algorithm calls. Greedy and fixed .3 common histories repeat 288 development trajectories to capture full pools; these executions do not increase the optimization statistical sample. Optimization statistics use only the 1,872 development runs. Prediction-before-label ordering, common initialization, and unchanged diagnostic-source journals pass the audit.

PEM-T and the removed-upper-mode variant have identical trajectories in all 144 pairs. Fixed .3 and temporal monitoring with fixed .3 management also match in all 144 pairs. These are correspondence checks for the structural result, not two independently effective components.

## 7.2 Endpoint behavior and the development gate

The selected fixed probability is .1 among .1/.3/.5/.8. Table 1 gives function-equally-weighted log-relative endpoints; lower is better. The complete feedback prototype and the spatial version do not outperform that fixed control on this summary. Mean greedy is slightly better than fixed .1 in both dimensions.

Table: Function-weighted development endpoint scores

{table(endpoint)}

Table 2 reports PEM-T minus fixed .1. The geometric ratios exceed one and each dimension has zero wins and eight losses. Paired hierarchical bootstrap intervals for the log difference are {intervals}. The Holm tests do not reach .05. The intervals and adjusted tests address different procedures and must not be selectively combined into a confirmatory significance claim; the control is also selected on development data.

Table: Paired function-level development effects

{table(effects)}

![Development convergence curves. Each evaluation pools normalized log errors over functions, instances, and runs using a median. This differs from Table 1's function-level aggregation, so curve endpoints are not Table 1 estimates.](../results/analysis_v1/convergence.png)

The necessary optimization-benefit gate is unmet in both dimensions. We do not enlarge the original optimization-confirmation experiment to circumvent that result. A later mechanism validation is separately specified, and any future new optimizer would require a new development stage and held-out range.

## 7.3 Exploration, failure, and sparse declarations

PEM-T explores approximately 36.6% and 33.4% of post-initialization evaluations, compared with approximately 10% for the fixed control. Its observed failure fractions are approximately 9.9% and 9.5%. Being near the nominal monitoring level does not correspond to better endpoints.

Table: Joint closed-loop decision indicators, 72 runs per dimension/method

{table(declaration)}

PEM-T makes only three declarations in dimension 10, one false, and no declarations in dimension 20. The latter FDP is NA, not zero. PEM-ST makes 32 declarations with two false in dimension 20, but its endpoint remains worse. Table 3's pooled declaration ratio is distinct from a mean over runs with nonzero declarations. These sparse denominators do not establish stable conditional success probabilities.

![Counts of actual improvement and false claims on declared candidates. A zero column denotes no declarations, not an established reliability advantage.](../results/supplement_v1/declarations.png)

Failure-only feedback is less detrimental than full feedback on the endpoint summary but still does not achieve an overall benefit over fixed .1. Its combined removal of width and stagnation cannot isolate those terms' independent contributions.

## 7.4 Common-history diagnostics

Table 4 uses the same T bound within each frozen history/model/pool. Under fixed .3 histories, failures at the actually selected point exceed pool failures. Under greedy histories, their ordering reverses. The observation supports history-dependent differences among monitoring objects and does not support a universal direction of selection-induced undercoverage. Each dimension/history has 288 frozen states; each state contributes one actually selected candidate, 256 pool candidates, and 26 top-10% candidates.

Table: Temporal bounds across monitoring objects

{table(c)}

![State-averaged one-sided failure fractions under frozen common histories. The dashed target is .1. Pool labels are correlated and are not treated as independent problems.](../results/analysis_v1/selection_failure.png)

Table 5 compares calibrators on the actually selected points, with the three histories equally weighted. Spatial localization lowers some diagnostic losses and margins; this is a common-history estimation result, not a closed-loop optimization gain or a coverage guarantee. Approximately one quarter of the dimension-10 checkpoint states fall back because of support, whereas these dimension-20 checkpoints do not.

Table: Calibrators on actually selected points

{table(local)}

Pool-declaration subsets are also sparse: T has only 13 declared candidates under dimension-10 fixed .3 histories, and one under dimension-20 fixed .3 histories. Full state, nonempty-state, candidate, and failure denominators are publicly retained in the diagnostic CSV files. We do not infer stable reliability from a small or empty subset.

## 7.5 Common-state immediate utility

Table 6 reports normalized true improvement at one chosen candidate from the same frozen pool. T upper-bound selection is identical to mean greedy and is not repeated as an independent column. Full feedback has lower mean immediate improvement than mean greedy and than the predeclared fixed .3 rule in all six dimension/history cells.

Table: Common-state normalized one-step improvement

{table(single)}

Immediate utility does not exclude a delayed benefit from exploration; however, the closed-loop development experiment supplies no evidence of that benefit for this prototype. It is therefore unsupported to state that additional distance exploration repaired the model.
'''
    text=(ROOT/'paper/english_development_template.md').read_text('utf-8').replace('{{ABSTRACT_RESULTS}}',abstract).replace('{{RESULTS}}',results)
    text=text.replace('a explicitly post-hoc','an explicitly post-hoc')
    assert '{{' not in text
    (ROOT/'paper/english_development_manuscript.md').write_text(text,encoding='utf-8')
    sources=['audit.json','gate.json','paired_comparisons.csv','endpoint_scores.csv','closed_loop_metrics.csv','calibration_aggregate.csv','single_step_aggregate.csv']
    (ROOT/'paper/english_development_source_hashes.json').write_text(json.dumps({name:hashlib.sha256((DATA/name).read_bytes()).hexdigest() for name in sources},indent=2),encoding='utf-8')
    print('English development manuscript generated from audited data.')


if __name__=='__main__':main()
