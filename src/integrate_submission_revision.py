"""Factual code specification, measured tables and reorganization of existing text.

No primary protocol or label is changed. Existing scientific paragraphs are
relocated intact, with a factual comparison row and algorithm/data tables added.
Historical AI drafting disclosure is preserved. All-author approval is removed
from active workflow at the user's explicit instruction, not certified as done.
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
from .integrate_engineering_evidence import table

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / 'paper/engineering_optimization'
DEST = PAPER / 'submission_revision_20261013'
MARKER = '% Operational specification revision 20261013; frozen experiments unchanged.'
BASE_HASHES = {
    'EO_manuscript.tex': '416671d36a37d00ef2d0a0b4cbb6654d1f6d0ca599b059b61573802e11cae2db',
    'EO_supplementary.tex': '71b8a09dc13c9e814799bbed74331d2d5eb2e07eb5f97df364a465f0bf885496',
    'EO_references.bib': 'efad9f03f4c2d22031661670fff2e4e43d4f2b9c357d367be2a77ced9e0ba89d',
}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def generate():
    report = json.loads((DEST / 'operational_comparison.json').read_text())
    rows = []
    for c in ['mean', 'ei']:
        for mode in ['named_full_horizon', 'exact_class_full_horizon', 'fixed_depth_v1_B18',
                     'immediate_v1_B18', 'adaptive_v1_B18', 'calibration_original', 'calibration_skip_alias_posthoc']:
            r = next(x for x in report['primary'] if x['continuation'] == c and x['method'] == mode)
            rows.append([c.upper(), mode.replace('_', ' '), f"{r['classified']}/{r['contrasts']}",
                         r['errors'], r['requests'], f"{r['mean_state_selection_loss_percent']:.4f}"])
    caption = ('Retrospective operational comparators answering the same conditional h5 question at margin 0.001. '
               'Named and exact-class full-horizon readers are transparent baselines, not published-algorithm replications. '
               'The strongest simple class-aware fixed-depth comparator is the frozen v1 method itself. '
               'Alias-skipping calibration is post hoc and leaves all labels unchanged; original results are retained. '
               'Requests include cache reads and are not new physical attempts. No predictive or deployment advantage is inferred. '
               'Data table assembled from the frozen analysis outputs.')
    (PAPER / 'integrated_evidence/submission_comparison.tex').write_text(
        table(caption, 'tab:operational_comparison', ['Followup', 'Reader / rule', 'Classified', 'Errors', 'Requests', 'Selection loss (%)'],
              rows, [.09, .40, .12, .08, .10, .21]))
    (PAPER / 'integrated_evidence/submission_algorithm.tex').write_text(r'''\Needspace{12\baselineskip}
\FloatBarrier\begingroup\fontsize{8.5}{10.5}\selectfont\setlength\tabcolsep{3pt}
\begin{longtable}{@{}>{\raggedright\arraybackslash}p{.17\linewidth}>{\raggedright\arraybackslash}p{\dimexpr.83\linewidth-2\tabcolsep\relax}@{}}
\caption{Frozen v1 conditional audit: executable operation specification. This table describes the existing code, including the unsuccessful adaptive heuristic; it does not propose a new optimizer. The transcription from code to operations follows the implementation as frozen.}\label{tab:conditional_algorithm}\tabularnewline
\toprule
Operation & Exact implementation \\
\midrule
\endfirsthead
\toprule
Operation & Exact implementation \\
\midrule
\endhead
\bottomrule
\endlastfoot
State / target & Freeze the 100-label history, fitted ARD kernel, first candidate pool, context and first actions. Baseline is the mean first action. Each branch updates its own history under the same mean or EI continuation and candidate-seed stream. $h0$ is the intervention; $H=5$ is five further actions. The primary target is $d_j=[m_0(5)-m_j(5)]/m_{\mathrm{init}}$, margin $\tau=0.001$. \\
Alias / access & Group exactly identical first actions only within the same state and declared continuation. If $K=1$, output structural tie for all names with zero requests. Otherwise \texttt{observe(branch,step)} may reveal only the next prefix response. Each request costs one, including an exact cache read. \\
Fixed depth & Complete the baseline to step 5; then complete alternatives in original class order while budget remains. Original class insertion follows mean, EI, PI, LCB. Incomplete comparisons abstain. Full mode uses $6K$ requests as its allowance. \\
Breadth / proxy & Breadth loops over steps 0--5 and advances baseline then alternatives at each step. Immediate mode reads h0 for each class; its labels are proxies for the h5 target, not certificates. \\
Adaptive reads & Read h0 and h1 for all classes, baseline first; then complete the baseline. Rank alternatives by descending $p_j=|m_0(1)-m_j(1)|/m_{\mathrm{init}}+\sigma_j^{\mathrm{root}}/m_{\mathrm{init}}$. Equal priorities use original class order. Advance each alternative to stages 3 and 5 before moving to the next. This priority is an observed-effect/uncertainty heuristic, not a confidence bound. \\
Measured outputs & A nonalias better/tie/worse certificate requires both baseline and alternative to reach h5. Use better if $d_j>\tau$, worse if $d_j<-\tau$, otherwise tie. Budget-incomplete output is abstain; an immediate tie never certifies a later tie. \\
Acquisitions & Independent budget collection uses 1024 candidates, normalized targets, $\alpha=10^{-6}$ and $\kappa=2$. EI/PI use an improvement margin $0.05$ times training-label standard deviation. ARD parameters are fitted once at the shared 50-label warm state (max 30 iterations), then fixed. These settings differ from the archived intervention and transfer studies. \\
Calibration proxy & Eight frozen-root probes give NRMSE (scaled by training-label standard deviation) and empirical coverage of $\mu\pm1.6448536269514722\sigma$. The constructed gate requires NRMSE $\leq0.25$ and coverage $\geq0.8$. If eligible, classify the root-EI difference divided by $m_{\mathrm{init}}$ using the same margin; otherwise abstain. It predicts h5 utility without a horizon guarantee. The original comparator charges eight probes in all 30 states. \\
State selection & Start with mean and effect threshold $\tau$. Visit EI, PI, LCB; replace the selected control only for label better and a strictly larger recorded effect. Thus exact ties retain the earlier control. Select only from the disclosed outputs, not oracle h5 truth. \\
Loss / averaging & State-selection loss is $100[m_{\mathrm{selected}}(5)-\min_j m_j(5)]/m_{\mathrm{init}}$. Average over all 30 states, including alias-only states. Complete truth is used only after the reader finishes, to evaluate the decision; it cannot change the observation trace. Ten shared seed blocks, not these dependent states or contrasts, are the independent units. \\
\end{longtable}
\endgroup

''')


def apply():
    mainp, suppp = PAPER / 'EO_manuscript.tex', PAPER / 'EO_supplementary.tex'
    before = {p.name: p.read_bytes() for p in [mainp, suppp, PAPER / 'EO_references.bib']}
    main, supp = mainp.read_text(), suppp.read_text()
    if MARKER not in main:
        old = '\\input{integrated_evidence/review_method_records.tex}'
        assert main.count(old) == 1
        main = main.replace(old, old + '\n\\input{integrated_evidence/submission_algorithm.tex}')
        # Add a checked bibliographic comparison row; no superiority inference.
        old = 'Diagnostic benchmarking \\citep{ref34} & Effectiveness, efficiency, reliability, parameter controllability, and runtime dynamics across real applications & Mechanism-level decision effects connected to separate closed-loop outcomes \\\\'
        assert main.count(old) == 1
        main = main.replace(old, old + '\nTwo-step lookahead \\citep{ref39} & Model-based expected future improvement for choosing evaluations & Recorded first actions followed by actual responses under a declared common continuation \\\\')
        main = main.replace('Sections 6.3-6.4 provide the additional GP evidence.', 'Sections 6.3-6.5 provide the additional GP evidence.')
        # Relocate the existing conditional-results paragraph out of transfer costs.
        start = main.index(' The independent conditional record in Table~')
        end = main.index('\n\n\\input{integrated_evidence/main_records.tex}', start)
        paragraph = main[start:end].lstrip()
        main = main[:start] + main[end:]
        insert = '\\input{integrated_evidence/review_main_results.tex}'
        assert main.count(insert) == 1
        main = main.replace(insert, '\\subsection{Conditional first-action records and budgeted replay}\\label{conditional-first-action-records}\n\n'
                            + paragraph + '\n\n' + insert)
        # Explicit task removal; no statement that approval occurred.
        main = main.replace('Author review draft. Affiliations b and c and final author approval are pending.',
                            'Working manuscript. Affiliations b and c remain to be supplied.')
        main = main.replace(' Final approval of the revised manuscript by all authors is pending.', '')
        main = main.replace('it does not certify author approval or policy compliance.', 'it does not certify publisher-policy compliance.')
        main = MARKER + '\n' + main
        mainp.write_text(main)
    if MARKER not in supp:
        old = '\\input{integrated_evidence/review_supp_records.tex}'
        assert supp.count(old) == 1
        supp = supp.replace(old, old + '\n\\input{integrated_evidence/submission_comparison.tex}')
        suppp.write_text(MARKER + '\n' + supp)
    supp = suppp.read_text().replace('Author review draft. Affiliations b and c and final author approval are pending.',
                                   'Working manuscript. Affiliations b and c remain to be supplied.')
    if supp != suppp.read_text():
        suppp.write_text(supp)
    bib = PAPER / 'EO_references.bib'
    if '@inproceedings{ref39,' not in bib.read_text():
        bib.write_text(bib.read_text() + '''\n@inproceedings{ref39,
  author = {Jian Wu and Peter Frazier},
  title = {{Practical Two-Step Lookahead Bayesian Optimization}},
  booktitle = {Advances in Neural Information Processing Systems},
  volume = {32},
  year = {2019},
  url = {https://papers.neurips.cc/paper_files/paper/2019/hash/2e6d9c6052e99fcdfa61d9b9da273ca2-Abstract.html},
}\n''')
    def numeric_rows(text):
        return [r for block in re.findall(r'\\begin\{longtable\}.*?\\end\{longtable\}', text, re.S)
                for r in block.splitlines() if '&' in r and re.search(r'\d', r) and r.strip().endswith(r'\\')]
    for p in [mainp, suppp]:
        oldrows = [r for r in numeric_rows(before[p.name].decode()) if 'Two-step lookahead' not in r]
        # The new citation row is a factual bibliography addition, not a numeric result.
        newrows = [r for r in numeric_rows(p.read_text()) if 'Two-step lookahead' not in r]
        assert oldrows == newrows
    assert (PAPER / 'EO_references.bib').read_bytes().startswith(before['EO_references.bib'])
    changes = {p.name: {'before_sha256': BASE_HASHES[p.name], 'after_sha256': sha(p.read_bytes())}
               for p in [mainp, suppp, bib]}
    if changes:
        (DEST / 'manuscript_change_record.json').write_text(json.dumps({
            'baseline_commit': 'a8a04d797c23a6c205fbf48f83c127a8903bfae4', 'changes': changes,
            'existing_inline_numeric_results_unchanged': True, 'prior_38_bibliography_records_preserved': True,
            'existing_conditional_result_paragraph_relocated_intact': True,
            'new_article_argument_sections_drafted': False,
            'all_author_approval_task': 'excluded by explicit user instruction 2026-10-13',
            'all_author_approval_certified': False,
            'historical_ai_draft_assistance_disclosure_preserved': True}, indent=2) + '\n')


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    generate()
    apply()
    print(json.dumps({'generated_tex_inputs': 2, 'new_physics_attempts': 0,
                      'all_author_approval_task_required': False}))


if __name__ == '__main__':
    main()
