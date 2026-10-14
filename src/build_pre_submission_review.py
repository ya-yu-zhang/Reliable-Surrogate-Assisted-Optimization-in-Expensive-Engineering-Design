"""Prepare a bounded author-review overlay from the sole baseline.

No claim of author-originated writing or submission-policy compliance is made.
Historical numeric tables and statistical families are preserved verbatim.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

TITLE='Conditional Decision Audits in Surrogate-Assisted Engineering Optimization: Evidence and Cost Limits'
ABSTRACT=r'''Surrogate prediction quality does not determine whether a paid evaluation decision is useful. We examine three questions: whether a surrogate-derived signal changes the action, whether immediate utility represents its finite-horizon consequence, and whether the resulting information justifies the audit's complete cost. The central object fixes a learned state, objective context, first action, continuation, horizon, margin and observation budget, and records exact action classes, permissible prefix observations and output reasons. A residual-monitor case exposes a redundant ranking correction despite near-nominal aggregate monitoring. In archived common-continuation data, seven distinct classifications change between the immediate and five-additional-action endpoints. At the original margin, better branches occur in only two of thirty states. Independent validation retains ten complete seed blocks and thirty dependent states: neither continuation contains a better primary h5 contrast, and adaptive allocation gives no advantage over class-aware fixed depth. Both consume 252 audit requests at budget 18, or 330 including chosen-branch execution in all thirty states; at budget 12, fixed depth classifies 17 of 25 contrasts and adaptive allocation 9. Separate longer-horizon policy and paid-workflow records demonstrate delayed value and endpoint--cost tradeoffs, but do not validate the conditional reader. The study provides a reproducible, bounded method evaluation; it establishes neither positive-case diagnostic efficacy nor performance-preserving deployment savings.'''

POSITION=r'''The central object of this study is a conditional first-action audit record. It fixes a learned state and objective context, changes the first action, and then follows a declared continuation with the same external candidate stream while each branch develops its own observed history. The horizon, comparison margin and reader-request budget specify the judgment. This target differs from changing an entire policy throughout an optimization trajectory.

Three questions organize the evidence: does the signal change the paid action; does its immediate utility represent its declared finite-horizon consequence; and does obtaining that information justify complete cost relative to the strongest simple same-target reader? Calibration, conditional intervention and whole-policy validation are separate evidence objects. The implemented record, source-specific settings and frozen observation schedules are specified in Table~\ref{tab:conditional_algorithm}.

The outputs are an executable conditional record, a same-target comparison with class-aware fixed depth, and explicit request/physical-attempt/execution ledgers. The independent primary record contains no better h5 alternatives and demonstrates no adaptive-allocation advantage. Exact caching, structural aliases and the immediate-query accounting proposition are implementation checks, rather than standalone optimization innovations. A descriptive opportunity analysis retains each dataset's original margin and every original seed group. Its supporting sources and the separate failed development stages appear in the supplement.

The study is a bounded method evaluation. It does not establish a new acquisition rule, a positive-case diagnostic advantage, a superior selector or performance-preserving savings over complete common continuation. The residual controller, immediate GP interventions and independent policy transfer provide complementary evidence within their stated targets; their reporting units are not pooled as independent samples. Reliability here means the credibility and utility of a surrogate-management decision, rather than structural failure-probability design.

'''

CONCLUSION=r'''This study evaluates a conditional decision record with an explicit learned state, objective context, first-action intervention, continuation, horizon, margin and request budget. Exact action classes and prefix-only access distinguish structural equivalence, measured target consequences, immediate proxies and abstention. These objects keep calibration, conditional intervention and whole-policy outcomes separate.

The residual monitor has a redundant ranking correction and fails its optimization-benefit gate despite near-nominal aggregate monitoring. Archived common-continuation branches show delayed first-action consequences. The independent primary h5 record, however, contains no beneficial alternative: mean gives 0 better, 24 tie and 1 worse; EI gives 0 better, 23 tie and 2 worse. Completed-target zero errors follow from measurement and do not validate positive-case prediction. Adaptive allocation does not improve on class-aware fixed depth, and performs worse at the tighter budget.

The subsequent development records likewise do not establish a complete-cost increment. Audit requests, chosen-branch completion and alias-only execution must be counted separately. The strongest supported outcome is a reproducible, limited method evaluation with explicit evidence and cost boundaries. Positive-case efficacy, superiority over strong simple continuation, performance-preserving savings and physical accuracy of the decision margin remain unestablished. A shorter H1 specification or a narrower candidate set cannot replace primary H5 validation.

'''


def main(baseline, revision, study):
    p=Path('paper/engineering_optimization');src=baseline/p;dest=revision/p
    s=(src/'EO_manuscript.tex').read_text()
    s=s.replace(r'\renewcommand\bibfont{\fontsize{10}{11.5}\selectfont}',r'\renewcommand\bibfont{\fontsize{10}{11.25}\selectfont}')
    s=s.replace(r'\maketitle',r'\received{Author-review preparation, 14 October 2026}'+'\n'+r'\maketitle',1)
    s=re.sub(r'\\title\{[^\n]+\}',lambda _:r'\title{'+TITLE+'}',s,count=1)
    s=re.sub(r'\\begin\{abstract\}.*?\\end\{abstract\}',lambda _:r'\begin{abstract}'+'\n'+ABSTRACT+'\n'+r'\end{abstract}',s,count=1,flags=re.S)
    start=s.index('A decision-consequence auditing framework is developed')
    end=s.index(r'\hypertarget{related-work}')
    s=s[:start]+POSITION+s[end:]
    old='The methodological advance argued here is their joint use to make a signal-to-action claim falsifiable before treating it as demonstrated engineering-budget value.'
    s=s.replace(old,'The combined record makes the signal-to-action claim and information boundary inspectable; the present results do not establish a diagnostic-quality increment over matched-state complete continuation.')
    core=r'''\subsection{Conditional first-action object}\label{conditional-audit-object}

The record is $(s,c,a,r,H,\tau,B,\mathcal{P},\mathcal{E},q,\mathcal{L})$: frozen learned state, objective context, first action, continuation, additional-action horizon, margin, request allowance, observed prefix, exact action class, output reason and cost ledger. With baseline mean first action and positive initial incumbent, $d_j(H)=[m_0(H)-m_j(H)]/m_{\mathrm{init}}$. The independent primary target retains $H=5$, $\tau=0.001$ and $B=18$ per state. The archived common continuation retains $\tau=10^{-6}$. A complete branch has six response positions, h0 through h5. Equal endpoints do not define action equivalence. An immediate tie cannot certify a later tie, and an incomplete nonalias target abstains.

'''
    point=s.index(r'\hypertarget{optimization-system-and-information-boundary}')
    s=s[:point]+core+s[point:]
    start=s.index(r'\subsection{Conditional first-action records and budgeted replay}')
    end=s.index(r'\hypertarget{discussion-and-design-guidance}')
    conditional=s[start:end]
    s=s[:start]+s[end:]
    addition=r'''The observed opportunity is $[m_0(5)-\min_jm_j(5)]/m_{\mathrm{init}}$, including the baseline in the minimum. This describes the recorded branches, not a global optimum. At its original margin, archived mean continuation has above-margin opportunities in only two of thirty states and two of ten seed groups. Its 46 distinct nonbaseline contrasts have 3 better, 34 tie and 9 worse labels. In the independently acquired mean and EI records, best-observed improvement is exactly zero in every state, including below-margin gains. All original groups and margins remain retained; positive-case diagnosis cannot be validated by those independent outcomes.

'''
    conditional=conditional.replace('\n\n','\n\n'+addition,1)
    conditional += r'''The response-request totals above describe the audit reader. Executing the chosen branch in all 30 states additionally includes alias-only states: the original complete-target audit subtotal of 252 becomes 330, and the budget-12 subtotal of 204 becomes 282. These logical counts include previously acquired responses and do not measure additional physical solves. The subsequent monotone development schedules also require explicit chosen-branch completion and a separate selection-certification count; their 13-cell reconciliation appears in the supplementary checked-records section.

'''
    point=s.index(r'\hypertarget{frozen-state-intervention-on-gp-acquisition-policies}')
    s=s[:point]+conditional+s[point:]
    start=s.index(r'\section{Conclusion}');start=s.index('\n\n',start)+2
    end=s.index(r'\section*{Acknowledgements}')
    s=s[:start]+CONCLUSION+s[end:]
    s=s.replace('bringing the project total to 55,307; the stage-wise boundary is reported in the supplement.',
                'bringing the total for the reported records to 55,307. The opportunity, cost-reconciliation and assumption screens add no physical calls; their boundaries are reported in the supplement.')
    s=s.replace('Codex based on GPT-6 was used for the present formatting and copyediting step.',
                'Codex based on GPT-6 assisted scientific argument drafting as well as factual transcription, numerical verification, formatting and copyediting. The resulting manuscript remains an author-review draft; publication-policy compliance and author-originated scientific writing are not certified.')
    s=s.replace(r'\textbf{Algorithm 1. Decision-consequence audit for a surrogate-assisted model-management mechanism.}',r'\textbf{Evidence stages for a surrogate-assisted model-management audit.}')
    s=s.replace(r'\input{integrated_evidence/submission_algorithm.tex}',r'\textbf{Algorithm 1. Frozen conditional first-action audit.} Table~\ref{tab:conditional_algorithm} gives its exact observation schedules and outputs.'+'\n\n'+r'\input{integrated_evidence/submission_algorithm.tex}')
    # Remove obsolete manually numbered references after moving conditional data.
    for prefix,key in [('Prespecified independent validation contrasts.','tab:bbob_validation'),('Stage-omission ablation and the resulting loss of evidence.','tab:stage_omission'),('Finite-element endpoint compliance over ten optimization repeats.','tab:beam_endpoints')]:
        match=re.search(r'\\caption\{'+re.escape(prefix)+r'[^\n]*\}',s);assert match
        s=s[:match.end()]+r'\label{'+key+'}'+s[match.end():]
    for n,key in [(2,'tab:bbob_validation'),(3,'tab:stage_omission'),(4,'tab:beam_endpoints')]:s=s.replace('Table '+str(n),r'Table~\ref{'+key+'}')
    s=s.replace('Section 6.3',r'Section~\ref{frozen-state-intervention-on-gp-acquisition-policies}').replace('Section 6.4',r'Section~\ref{longer-horizon-policies-load-position-transfer-and-total-cost}')
    s=s.replace('Sections 6.3-6.5',r'Sections~\ref{conditional-first-action-records}--\ref{longer-horizon-policies-load-position-transfer-and-total-cost}')
    s=s.replace('transfer_cost_performance.png','transfer_cost_performance.pdf')
    (dest/'EO_manuscript.tex').write_text('% Author-review preparation 20261014; sole baseline 58f539c2; no new physics.\n'+s)
    supp=(src/'EO_supplementary.tex').read_text()
    supp=re.sub(r'\\title\{[^\n]+\}',lambda _:r'\title{Supplementary material: '+TITLE+'}',supp,count=1)
    supp=supp.replace('transfer_pilot_horizons.png','transfer_pilot_horizons.pdf')
    supp=supp.replace(r'\bibliographystyle{tfcad}',r'\input{integrated_evidence/pre_submission_checked_records.tex}'+'\n\n'+r'\bibliographystyle{tfcad}')
    (dest/'EO_supplementary.tex').write_text('% Author-review preparation 20261014; frozen evidence unchanged.\n'+supp)
    data=json.loads((study/'innovation_feasibility.json').read_text())
    costs=[]
    import csv
    with (study/'development_cost_reconciliation.csv').open() as f:costs=list(csv.DictReader(f))
    appendix=r'''\section{Checked opportunity, development costs and assumption boundaries}\label{supp:checked_records}

The additional checks read losslessly restored frozen records and existing derived summaries. They retain 60 metadata states, 90 dependent contexts and ten original seed groups per dataset. All 179 archived file hashes match. No new physical evaluation, bound query, GP fit, optimization sample or confirmatory test family is acquired. These are post hoc development and descriptive checks, not new independent validation.

\subsection{Opportunity and branch-shape scope}
At its original $10^{-6}$ margin, archived common continuation has 3 better, 34 tie and 9 worse distinct nonbaseline contrasts, with better branches in only two states. Both independent continuations retain their $0.001$ margin and have zero better branches; all statewise best-observed improvements are exactly zero. Complete horizon measurement therefore cannot demonstrate positive-case prediction or avoidance of false rejection.

Observed gains need not have diminishing increments. The check below includes the initial-to-h0 increment and the following five increments, allowing relative numerical tolerance $10^{-12}$. It concerns deterministic recorded paths, not stochastic expected loss, and is not a replication or rejection of published model-based bandit algorithms.

\FloatBarrier\begingroup\fontsize{8.5}{10.5}\selectfont\setlength\tabcolsep{3pt}
\begin{longtable}{@{}p{.34\linewidth}p{.18\linewidth}p{.20\linewidth}p{\dimexpr.28\linewidth-6\tabcolsep\relax}@{}}
\caption{Descriptive shape check of distinct recorded branches. Each row retains 30 states and ten complete groups.}\label{tab:shape_screen}\\
\toprule Record & Curves & Violating curves & States with a violation \\
\midrule\endfirsthead\toprule Record & Curves & Violating curves & States with a violation \\
\midrule\endhead\bottomrule\endlastfoot
'''
    for r in data['summaries']:
        name='Archived mean' if r['dataset']=='archived_common' else 'Previous '+r['continuation']
        appendix+=f"{name} & {r['distinct_branch_curves']} & {r['curves_violating_diminishing_returns']} & {r['states_with_a_diminishing_returns_violation']} "+r'\\'+'\n'
    appendix+=r'''\end{longtable}\endgroup

\subsection{Audit, certification and chosen-branch execution}
Table~\ref{tab:reconciled_costs} separates audit requests, chosen nonalias completion and alias-only execution. Previously quoted nontrivial-state totals 252, 204 and 402 become 330, 282 and 426 when all original states are executed. These totals do not mean every unobserved competitor is completed or every selection is certified. Selection certification coverage is shown separately. They are logical request costs, including cache reads, not new physical solves or end-to-end wall-time savings.

\FloatBarrier\begingroup\fontsize{8.5}{10.5}\selectfont\setlength\tabcolsep{3pt}
\begin{longtable}{@{}p{\dimexpr.31\linewidth-12\tabcolsep\relax}p{.12\linewidth}p{.10\linewidth}p{.12\linewidth}p{.10\linewidth}p{.10\linewidth}p{.15\linewidth}@{}}
\caption{Original monotone development costs and certified-selection coverage, retaining all 30 states per row. Coverage in the last column excludes alias-only states.}\label{tab:reconciled_costs}\\
\toprule Record / budget / reader & Classified & Audit & Chosen nonalias completion & Alias execution & Total & Certified selection \\
\midrule\endfirsthead\toprule Record / budget / reader & Classified & Audit & Chosen nonalias completion & Alias execution & Total & Certified selection \\
\midrule\endhead\bottomrule\endlastfoot
'''
    names={'v1_fixed_depth':'fixed','h0_largest_upper':'h0-directed','alternative_depth':'alternative first'}
    for r in costs:
        name='Archived mean' if r['dataset']=='archived_common_mean' else 'Previous '+r['continuation']
        appendix+=f"{name} / B{r['budget']} / {names[r['reader']]} & {r['classified']}/{r['contrasts']} & {r['audit']} & {r['chosen_nonalias_completion']} & {r['alias_execution']} & {r['total_all_states']} & {r['certified_nonalias_selection']}/{r['nonalias_states']} "+r'\\'+'\n'
    appendix+=r'''\end{longtable}\endgroup

Under independent terminal intervals $[L_j,U_j]$, the worst-case chosen-branch loss is $\max(0,U_i-\min_{j\ne i}L_j)$. With an unfinished competitor lower bound zero, a chosen upper bound above $\tau m_{\mathrm{init}}$ cannot certify the loss tolerance. Every recorded branch terminal incumbent exceeds that threshold, so all its earlier prefixes do as well. Within this interval-only information model, certifying every selection and then executing the chosen branch returns to six requests per exact class: 456 over archived states and 330 per previous continuation. This is a scope-limited accounting barrier, not a new theorem for all physical or GP-informed audits. Structural alias choices have zero selection regret without an audit, but executing their branch still costs six requests.

The completed two-reference/full-pool screen separately fails necessary root-tie sharpness on all 43 nontrivial states. Its 1,720 bound queries and two reference solves remain original development costs. A sampled minimum can disqualify the full envelope but cannot certify it. Fixed-kernel GP reachability has a shorter H1 specification; no H1 result is used here as H5 efficacy or independent validation.

The checks and source hashes are supplied with \path{innovation_readiness_20261014/}. The reported experiment/reference ledger contains 55,307 physics attempts within its stated scope. This descriptive preparation adds zero. No physical accuracy of the illustrative margin, independent positive-case efficacy or journal novelty sufficiency is certified.
'''
    (dest/'integrated_evidence/pre_submission_checked_records.tex').write_text(appendix)
    print('Prepared a bounded author-review overlay; historical numeric tables unchanged.')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--revision',type=Path,required=True);p.add_argument('--study',type=Path,required=True)
    a=p.parse_args();main(a.baseline,a.revision,a.study)
