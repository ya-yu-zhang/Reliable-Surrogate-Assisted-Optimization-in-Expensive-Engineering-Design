"""Printable independent-validation tables; no new estimands or tests."""
import hashlib
import json
from pathlib import Path

import pandas as pd
from .build_mechanism_manuscript import table

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'results/mechanism_validation_analysis_v1'
REPORT = ROOT/'results/mechanism_validation_report_v1'
METHODS = ['greedy','fixed01','fixed03','pool_random','PEM_T','PEM_ST']
LABELS = {'greedy':'Greedy','fixed01':'Fixed .1','fixed03':'Fixed .3',
          'pool_random':'Random','PEM_T':'PEM-T','PEM_ST':'PEM-ST'}


def section(title, description, frame):
    frame = frame.copy()
    for name in frame.columns:
        if pd.api.types.is_float_dtype(frame[name]):
            frame[name] = frame[name].map(lambda v: f'{v:.3e}' if 0 < abs(v) < .0001 else f'{v:.4f}')
    return '\n\\newpage\n\n# '+title+'\n\n'+description+'\n\n'+table(frame)+'\n'


def main():
    audit = json.loads((DATA/'full_integrity_audit.json').read_text('utf-8'))
    assert audit['runs'] == 3888 and audit['states'] == 7776 and audit['frozen_sources_unchanged']
    sources = [DATA/'function_scores.csv', DATA/'prespecified_function_contrasts.csv',
               REPORT/'internal_raw_error_iqr.csv', REPORT/'structural_endpoint_scores.csv',
               REPORT/'localization_description.csv', DATA/'full_integrity_audit.json',
               REPORT/'secondary_metric_conventions.json', ROOT/'configs/mechanism_validation.json',
               ROOT/'docs/frozen_mechanism_validation_v1/sha256.json', Path(__file__)]
    fingerprints = {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    endpoints = pd.read_csv(sources[0]); contrasts = pd.read_csv(sources[1])
    iqr = pd.read_csv(sources[2]); groups = pd.read_csv(sources[3]); local = pd.read_csv(sources[4])
    assert len(endpoints) == 24*3*6 and len(contrasts) == 24*9 and len(iqr) == 24*3*6
    text = '''---
title: "Supplement: Independent Mechanism Validation"
date: "17 September 2026"
---

# S1 Scope, aggregation, and audit

This supplement accompanies the English mechanism working manuscript. All printed numbers derive from the completed independent validation; development data are not pooled into its tests. The full design comprises 24 BBOB functions, dimensions 10/20/40, instances 11/12/13, three repeats, six methods, and budget 10D: 3,888 runs, 907,200 paid algorithm calls. Independent diagnostics comprise 7,776 states and 1,990,656 additional labels, never supplied to optimizers. Failed runs and exact duplicate calls are zero.

Endpoint and contrast tables use the frozen hierarchy: three-repeat median within instance, three-instance average within function, then equal function weights for suite summaries. Contrasts are constructed at their prespecified component level. Raw-error IQR tables instead describe all nine paid runs for a function and method; they are not the estimators used for primary hypothesis tests.

Only the nine prespecified comparisons form the primary Holm family. Tables here provide complete function-level inputs and descriptive secondary outputs; they add no tests. The observed training truncation count is 185,328 fits. Source, pre-information, original residual, candidate-selection, and diagnostic-index audits passed. Real-arithmetic ordering equivalence is separate from arbitrary floating-point tie behavior.

The original optimization-improvement gate remains failed. New instances support mechanism and failure analysis. Neither this supplement nor the manuscript claims a pointwise coverage theorem, FDP/FDR control, evaluation savings, or application acceleration. Live GP-EI/TuRBO batches and unexecuted exclusive-cost measurements are absent from these tables.

All raw runs, predicted-before-label journals, candidate pools, hidden diagnostic labels, four checkpoint state tables, dependency locks, seeds, and failure logs are available in the project. Seed = 100000D + 1000f + 10i + r, with r=0,1,2. Initialization, candidates, and management use distinct random streams. Sharing this seed alone is not a claim of identical downstream histories.
'''
    for dim in [10,20,40]:
        frame = endpoints[endpoints.dim == dim].pivot(index='fid',columns='method',values='log_relative_error')
        frame = frame[METHODS].rename(columns=LABELS).reset_index().rename(columns={'fid':'Function'})
        text += section(f'S2.{dim} Full function endpoint scores, D={dim}',
            'Lower is better. Scores are log10(max(final error / common initial error, 1e-12)), with the frozen within-instance median and across-instance average. Random means the paid random candidate policy, not independent-domain Sobol.', frame)
    for dim in [10,20,40]:
        frame = contrasts[contrasts.dim == dim].pivot(index='fid',columns='comparison',values='contrast')
        frame = frame[['P1_history_interaction','P2_endpoint_PEM_T_minus_fixed01','P2_step_feedback_minus_mean']]
        frame = frame.rename(columns={'P1_history_interaction':'History interaction',
            'P2_endpoint_PEM_T_minus_fixed01':'Endpoint T - .1',
            'P2_step_feedback_minus_mean':'Gain feedback - mean'}).reset_index().rename(columns={'fid':'Function'})
        text += section(f'S3.{dim} Full primary contrast inputs, D={dim}',
            'The three columns have different units. Positive endpoint difference means worse PEM-T; positive gain difference favors feedback. History interaction is a difference of selected-minus-pool failure gaps between fixed .3 and greedy histories and has no inherent favorable sign. It is not a same-pool causal effect.',frame)
    for dim in [10,20,40]:
        records = []
        for fid in range(1,25):
            row = {'Function':fid}
            for method in ['fixed01','PEM_T']:
                values = iqr[(iqr.dim==dim)&(iqr.fid==fid)&(iqr.method==method)].iloc[0]
                row[LABELS[method]+' median [Q25, Q75]'] = f"{values['median']:.3e} [{values.q25:.3e}, {values.q75:.3e}]"
            records.append(row)
        text += section(f'S4.{dim} Raw paid-run error dispersion, D={dim}',
            'Absolute final error above the known optimum; all nine runs per function and method. This raw dispersion uses a different aggregation from the primary contrasts. Complete six-method IQR values are retained in internal_raw_error_iqr.csv. Scientific notation avoids rounding nonzero errors to zero.',pd.DataFrame(records))
    mapping = {'Separable':'S1','Low/moderate conditioning':'S2','Ill-conditioned unimodal':'S3',
               'Structured multimodal':'S4','Weakly structured multimodal':'S5'}
    groups['Group'] = groups.structure.map(mapping)
    frame = groups.pivot(index=['dim','Group'],columns='method',values='log_relative_error')
    frame = frame[METHODS].rename(columns=LABELS).reset_index().rename(columns={'dim':'D'})
    text += section('S5 Fixed BBOB structural groups',
        'S1=f1-5 (separable), S2=f6-9 (low/moderate conditioning), S3=f10-14 (ill-conditioned unimodal), S4=f15-19 (structured multimodal), S5=f20-24 (weakly structured multimodal). Values are equal-function means of endpoint scores. These groups are descriptive and do not become new significant subgroup claims.',frame)
    frame = local.rename(columns={'dim':'D','history':'History','quantile_loss':'Loss ST-T',
        'margin':'Margin ST-T','neff':'ESS ST-T','fallback':'Fallback ST-T'})
    text += section('S6 Localized bounds and metric conventions',
        'Actual selected points; differences are ST minus T, within each dimension/history. Lower quantile loss does not establish optimization gains. State-level fallback and component-level aggregation differ; this table uses the frozen function-level diagnostic aggregation.',frame)
    text += '''
The frozen AUC and convergence curve floor absolute error at 1e-12 before division by initial error, then take log10, inclusive from n0 through B. The endpoint floors the error ratio after division. They are distinct formulas at the near-zero boundary. This dataset has no curve entries below -12 and no exactly optimal final run; the boundary distinction remains documented.

Full CSV sources include function_scores.csv, prespecified_function_contrasts.csv, internal_raw_error_iqr.csv, structural_endpoint_scores.csv, and localization_description.csv. Full checkpoint records and sparse declaration denominators accompany the audit. This printable supplement does not replace the machine-readable records or source fingerprint manifest.
'''
    path = ROOT/'paper/english_mechanism_supplement.md'
    path.write_text(text,encoding='utf-8')
    fingerprints[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    (ROOT/'paper/english_mechanism_supplement_source_hashes.json').write_text(
        json.dumps(fingerprints,indent=2),encoding='utf-8')
    print('Independent supplement generated from complete audited data; 11 tables, no new tests.')


if __name__ == '__main__':
    main()
