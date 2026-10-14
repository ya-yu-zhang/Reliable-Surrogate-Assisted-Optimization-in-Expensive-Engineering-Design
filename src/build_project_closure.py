"""Integrate verified GP certificates and a measured computational increment."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re

from .build_pre_submission_review import main as build_previous

TITLE = 'Certified Action Sets and Decision Limits in Surrogate-Assisted Engineering Optimization'


def build(root, destination):
    baseline = root/'baseline'
    study = root/'results/innovation_readiness_20261014'
    build_previous(baseline, destination, study)
    paper = Path('paper/engineering_optimization')
    dest = destination/paper
    timing = json.loads((root/'results/gp_envelope_acceleration_20261014/analysis.json').read_text())
    assert timing['all_action_sets_equal_frozen_pairwise_reader']
    h1 = json.loads((root/'results/gp_envelope_acceleration_20261014/H1_recheck.json').read_text())
    assert h1['new_categories'] == h1['new_selection_certificates'] == 0
    ratio = timing['pruner_stage_speed_ratio']
    total_ratio = timing['pruner_plus_external_proof_check_speed_ratio']
    abstract = rf'''A useful surrogate must support a credible evaluation decision, not only accurate predictions. We develop a conditional audit that distinguishes action changes, finite-horizon consequences and information costs. For a fixed-kernel Gaussian process with one unknown nonnegative response, enclosed affine posterior means define a response-domain outer set of possible next actions. An exact rational envelope computes the complete relaxed-band set in $O(M\log M)$ arithmetic operations, retains isolated ties and supplies at most two rival indices per exclusion. On 114 archived engineering branches, both declared response domains retain 2--7 of 1024 actions and include every stored next action. All 232,564 original exclusion proofs and binary coefficient systems are reverified. The envelope produces identical action sets with {ratio:.2f}-fold faster set construction, or {total_ratio:.2f}-fold including separate certificate replay, relative to the frozen pairwise implementation. These are computational-stage improvements. The engineering bounds remain too weak to certify any of 71 nonbaseline H1 contrasts; H5 adaptive allocation also gives no independent diagnostic advantage. Full deployment savings and physical accuracy of the decision margin remain unestablished. The study contributes an executable, proof-producing action-set operator and an engineering evaluation separating computational efficiency from decision sufficiency.'''
    s = (dest/'EO_manuscript.tex').read_text()
    s = re.sub(r'\\title\{[^\n]+\}', lambda _: r'\title{'+TITLE+'}', s, count=1)
    s = re.sub(r'\\begin\{abstract\}.*?\\end\{abstract\}', lambda _: r'\begin{abstract}'+'\n'+abstract+'\n'+r'\end{abstract}', s, count=1, flags=re.S)
    s = s.replace('The study is a bounded method evaluation.',
                  'The study combines a proof-producing action-set operator with a bounded method evaluation.')
    point = s.index('Reliability here means')
    s = s[:point]+rf'''The computational contribution is an exact coefficient-band envelope with constant-size exclusion witnesses and a measured {ratio:.2f}-fold construction improvement over the frozen pairwise reference. Its engineering evaluation supplies the boundary between sharper action information and a useful downstream judgment. The original learning-curve and audit failures remain part of the contribution's scope.

'''+s[point:]
    point = s.index(r'\hypertarget{decision-pathways-and-ranking-invariance}')
    method = r'''\subsection{Certified response-domain action sets}\label{sec:certified_sets}

Consider $n$ observed responses $y_1,\ldots,y_n$, a fixed first-action location with unknown response $z\geq\ell\geq0$, and a finite eligible next-action pool of size $M$. Kernel parameters and the normalized noise diagonal are fixed. Let $A$ be the augmented $(n+1)$-point binary kernel matrix and $w_i=A^{-1}k_i$. With target normalization, define $h_i=(1-\mathbf{1}^{\mathsf T}w_i)/(n+1)$. The exact mean for this binary system is
\begin{equation}
\mu_i(z)=a_i z+b_i,\quad a_i=w_{i,n+1}+h_i,\quad
b_i=\sum_{t=1}^{n}(w_{i,t}+h_i)y_t.\label{eq:affine_binary}
\end{equation}
The target standard deviation cancels in the denormalized mean; this statement does not extend the operator to uncertainty-based acquisition rules. Linear posterior updates and affine-envelope geometry are established, including in knowledge-gradient computation \citep{ref40}. The present operator concerns numerical coefficient enclosures, a closed response domain and verifiable exclusions, rather than a new acquisition policy.

The inverse-residual check bounds $\|I-A\widehat{P}\|_\infty\leq\rho<1$, giving $\|A^{-1}\|_\infty\leq\|\widehat{P}\|_\infty/(1-\rho)$. A weight residual then bounds its coefficient error; normalization, dot products and endpoint construction are enclosed outwards. The stored implementation uses a stricter $\rho<0.5$ gate. Failure retains the full eligible pool. This certificate is conditional on the supplied binary matrix and documented finite, normal arithmetic, with kernel evaluation error and native floating predictions at every unknown response outside its guarantee.

Write coefficient bands as $a_i\in[a_i^-,a_i^+]$, $b_i\in[b_i^-,b_i^+]$. For $z\geq0$, let $L_i(z)=a_i^-z+b_i^-$ and $U_i(z)=a_i^+z+b_i^+$. A potentially minimal action must satisfy
\begin{equation}
R_i=\{z\geq\ell:L_i(z)\leq U_j(z)\ \text{for every }j\}\ne\varnothing.\label{eq:band_domain}
\end{equation}
This is an exact relaxed-band problem and an outer approximation for the coupled GP coefficients. A retained action need not be realizable by those coupled coefficients.

\textbf{Theorem 1 (closed-domain band filter).} Given finite ordered binary bands and $\ell\geq0$, all nonempty $R_i$, their exact rational endpoints and exclusions can be constructed in $O(M\log M)$ arithmetic operations and $O(M)$ storage. Every excluded action has an infeasibility witness using at most two rival indices, together with the domain constraint. Every minimizer allowed by the coefficient enclosures is retained, including actions feasible only at one response.

\textit{Proof.} An allowed minimizer has $L_i\leq\mu_i\leq\mu_j\leq U_j$ for every competitor, proving inclusion. Sort upper lines by decreasing slope and build their lower envelope $E(z)=\min_j U_j(z)$ with exact rational intersections. Parallel dominated lines can be removed from the envelope; a tied boundary value remains represented by its neighbors. Each line is inserted and removed at most once. For every original candidate, $E-L_i$ is a continuous concave piecewise-affine function with decreasing segment slopes. Binary search locates its maximum and the two possible zero crossings on $[\ell,\infty)$. A nonnegative maximum yields the closed feasible interval, including a singleton. A negative maximum lies at the domain boundary, on a parallel segment or between two adjacent envelope lines. Those one or two constraints already make the candidate infeasible and supply its witness. Sorting costs $O(M\log M)$, the envelope scan $O(M)$, and the searches $O(\log M)$ per candidate. Rational bit complexity is additional.\hfill$\square$

\textbf{Algorithm 2. Exact band-envelope audit.} (1) Enclose coefficients using the verified inverse gate. (2) Build the shared lower envelope of upper lines. (3) Query every original lower line, retaining all closed-domain ties. (4) Emit exact feasible intervals or at most two rival indices. (5) Independently replay each exclusion as rational one-dimensional infeasibility. (6) Apply identical already available point bounds and account separately for GP construction, pruning, proof replay and physical work. The algorithm accepts no pending response. The synthetic unit checks compare complete intervals with an independent all-pairs rational oracle and include a boundary-only lowest-index minimizer.

For one continuation, the available pending-point bound $p$, next-point bound $\lambda_i$ and feasible response interval $R_i$ imply the joint incumbent lower bound
\begin{equation}
J=\min\left(m_{\mathrm{init}},\min_{i:R_i\ne\varnothing}\min\{\max(p,\inf R_i),\lambda_i\}\right).\label{eq:joint_lower}
\end{equation}
The nonnegative-range reader additionally receives the same pending-point trial bound as the full-pool reader. A paid baseline endpoint and $[J,m_{\mathrm{init}}]$ can certify a category only when the complete effect interval lies in its declared category. This H1 calculation does not certify a five-step adaptive history.

'''
    s = s[:point]+method+s[point:]
    point = s.index(r'\hypertarget{frozen-state-intervention-on-gp-acquisition-policies}')
    results = rf'''\subsection{{GP action-set certificates and computational comparison}}\label{{sec:gp_certificate_results}}

The separately frozen protocol selected two witnesses before either response and used its complete two-attempt allowance. Their true compliances were 14324.7435408532 and 9639.9247638608, versus stored two-vector lower bounds 232.5285149112 and 200.5953747176. Relative equilibrium residuals were below $1.1\times10^{{-10}}$. Both responses exceeded their root-tie thresholds. This identifies loose point bounds at those witnesses without disqualifying the full pool. No retry, replacement or optimization sample was acquired.

The GP construction retained all sixty metadata states and both complete ten-group datasets; seventeen alias-only states needed no bounds. The 43 nontrivial mean contexts have 114 first-action branches. Each next pool contains 1024 eligible actions. Both predeclared domains, $[0,\infty)$ and $[\lambda_{{\mathrm{{pending}}}},\infty)$, retain 2--7 actions, with medians four and three in the two datasets. Every stored next action is included. The original construction preceded reading first/next responses. The subsequent envelope comparison is explicitly post hoc development on its stored coefficient bands.

\FloatBarrier\begingroup\fontsize{{8.5}}{{10.5}}\selectfont\setlength\tabcolsep{{3pt}}
\begin{{longtable}}{{@{{}}p{{.24\linewidth}}p{{.13\linewidth}}p{{.13\linewidth}}p{{.13\linewidth}}p{{.13\linewidth}}p{{\dimexpr.24\linewidth-10\tabcolsep\relax}}@{{}}}}
\caption{{Both GP response domains give the same recorded summaries. Complete metadata groups remain retained; H1 counts exclude baseline contrasts.}}\label{{tab:gp_certified_summary}}\\
\toprule Dataset & Active states / branches & Retained min / median / max & Next-action inclusion & Joint lower / initial median & H1 category / selection increments \\
\midrule\endfirsthead\toprule Dataset & Active states / branches & Retained min / median / max & Next-action inclusion & Joint lower / initial median & H1 category / selection increments \\
\midrule\endhead\bottomrule\endlastfoot
Archived mean & 26 / 72 & 2 / 4 / 7 & 72/72 & 5.9786\% to 11.3742\% & 0/46; 0/26 \\
Previous holdout mean & 17 / 42 & 2 / 3 / 6 & 42/42 & 9.2066\% to 20.1462\% & 0/25; 0/17 \\
\end{{longtable}}\endgroup

All 204 frozen source hashes, 114 reconstructed binary kernel/cross systems and their coefficient enclosures match. The {timing['old_exclusion_proofs_exactly_rechecked']:,} original exclusions and an equal number of new exclusions pass exact rational replay. The envelope returns identical action sets for all 228 branch-domain cases, with exact feasible intervals contained in the previous outward intervals. Rechecking the tightened intervals leaves all 71 nonbaseline H1 contrasts per domain abstaining and no baseline selection certified.

The computational comparison times coefficient-to-set construction on the same machine and inputs, alternating algorithm order over three repetitions per case. Summed casewise medians are {timing['pairwise_pruner_seconds']:.4f} seconds for the frozen pairwise implementation and {timing['envelope_pruner_seconds']:.4f} seconds for the exact envelope: {ratio:.2f}-fold stage acceleration. Separate complete proof-replay passes cost {timing['old_independent_proof_check_seconds']:.4f} and {timing['new_independent_proof_check_seconds']:.4f} seconds, respectively; including those passes gives {total_ratio:.2f}-fold acceleration. The replay passes are single measurements, and repetitions, domains and branches are dependent. These times exclude the common coefficient systems, paid baseline and physical-bound library. They do not establish industrial or end-to-end deployment speedup, nor comparison with an optimized library or knowledge-gradient policy.

\begin{{figure}}[htbp]
\centering\includegraphics[width=\linewidth]{{figures/gp_certified_envelope_comparison.pdf}}
\caption{{Paired median construction times and same-set cardinalities. The time panel uses all 228 dependent branch-domain cases; the cardinality panel counts each of114 branches once because both domains have the same counts. No independent optimization sample is represented.}}\label{{fig:gp_envelope}}
\end{{figure}}

The complete comparative development actually acquired 44,146 cached state/design bounds, plus the GP and proof work. Full-pool versus subset counts of116,850 and568 are logical requests; the subset figure is counterfactual because the complete library was already acquired. Narrower action sets and faster certificate construction therefore establish a computational increment but do not repair the decision-sufficiency gate. H5 reachability and a useful H1 judgment remain unestablished. The original independent-optimization gate stays closed.

'''
    s = s[:point]+results+s[point:]
    s = s.replace('bringing the total for the reported records to 55,307.',
                  'bringing that earlier subtotal to 55,307. The separately frozen two-witness diagnosis adds two attempts, bringing the reported project total to 55,309; its GP construction and the new envelope verification add no physics.')
    s = s.replace('Figure 6 reports', r'Figure~\ref{fig:transfer_cost} reports')
    caption = r'\caption{Cost and performance of the independently executed beam transfer workflows.}'
    s = s.replace(caption, caption+r'\label{fig:transfer_cost}')
    start = s.index(r'\section{Conclusion}'); start = s.index('\n\n', start)+2
    end = s.index(r'\section*{Acknowledgements}')
    conclusion = rf'''The conditional audit separates action identity, target-horizon consequences and the cost of obtaining a judgment. Its fixed-kernel GP component produces response-domain action sets with explicit coefficient enclosures and rational exclusion witnesses. The exact band envelope retains closed ties and constructs the relaxed-band solution in $O(M\log M)$ arithmetic operations. On the complete retained development cases, it preserves every original action set and stored next action, with {ratio:.2f}-fold faster set construction than the frozen pairwise reference.

This computational result has a definite boundary. The original H1 point bounds remain too weak to produce a new category or baseline selection certificate, despite 2--7 retained actions from pools of1024. The primary independent H5 records contain no better alternative, and adaptive allocation does not improve on class-aware fixed depth. Complete baseline/alias execution and the acquired full-pool bound library must remain in the cost ledger. A smaller candidate set or a faster pruner is insufficient evidence of performance-preserving deployment savings.

The contributions are an executable certificate-producing operator, its scoped computational improvement and an engineering evaluation that exposes the remaining information bottleneck. Claims beyond the binary fixed-kernel model, native floating predictions for every response, physical margin accuracy, H5 reachable histories and independent positive-case efficacy require evidence outside this study. These limits make the present completed method evaluation falsifiable without changing historical protocols or adverse findings.

'''
    s = s[:start]+conclusion+s[end:]
    start = s.index(r'\section*{Acknowledgements}')
    end = s.index(r'\section*{Funding Statement}')
    acknowledgement = r'''\section*{Acknowledgements}

OpenAI Codex assisted software development and verification, computational workflow execution and recovery, evidence integration, formal argument drafting, manuscript preparation and language revision. The authors remain responsible for the research, statements and interpretations. This disclosure retains the known assistance history. Venue-specific AI preparation requirements will be assessed when a publication destination is selected; compliance is not certified by this working manuscript.

'''
    s = s[:start]+acknowledgement+s[end:]
    s = s.replace('The supplementary document contains the historical', 'The supplementary document contains the certified-envelope proof details and H1 cost boundaries as well as the historical')
    (dest/'EO_manuscript.tex').write_text(s)
    supp = (dest/'EO_supplementary.tex').read_text()
    supp = re.sub(r'\\title\{[^\n]+\}', lambda _: r'\title{Supplementary material: '+TITLE+'}', supp, count=1)
    supp = supp.replace(r'\bibliographystyle{tfcad}', r'\input{integrated_evidence/gp_envelope_completion.tex}'+'\n\n'+r'\bibliographystyle{tfcad}')
    (dest/'EO_supplementary.tex').write_text(supp)
    appendix = rf'''\section{{GP proof verification and exact envelope completion}}\label{{supp:gp_completion}}

The attached immutable GP execution archive has SHA-256 \path{{25501c61eedfb379312693829be3fe612c2285ed5f2e7e677c3dc4892ca8b139}}. Its 70 manifest-listed members, 204 frozen source files, 43 construction records and two completed witnesses are verified. All60 metadata states and complete ten-group datasets remain retained. The two attempts are consumed; there is no retry, replacement, recovery or new optimization sample in the present verification.

\subsection{{Scope of the affine and numerical certificates}}
Equation~(\ref{{eq:affine_binary}}) in the main text describes the exact solution of the supplied binary kernel matrix. For an approximate inverse $\widehat P$, a verified norm residual below one implies invertibility through the Neumann-series bound. If $\widehat w_i$ has residual $r_i=k_i-A\widehat w_i$, its error is bounded by $\|A^{{-1}}\|_\infty\|r_i\|_\infty$. The normalization correction contributes at most the same maximum weight error; the effective coefficients use twice that bound plus enclosed arithmetic. The serialized coefficient bands are endpoints of binary numbers. All114 reconstructed matrices and cross matrices have the original byte hashes; reapplying the original enclosures reproduces every stored coefficient and error array exactly.

The new pruner solves the necessary inequalities exactly over $[\ell,\infty)$. It reads no pending response and introduces no label. This is post hoc algorithm development on previously constructed bands, not a prospectively independent study. It does not certify the kernel's transcendental evaluation error or every native floating GP prediction for every unknown label. The mathematical interval may be an outer relaxation of the coupled coefficient uncertainty.

\subsection{{Why the certificate has at most two rival indices}}
Each necessary pair inequality is $(a_i^--a_j^+)z\leq b_j^+-b_i^-$. It imposes an upper half-line, a lower half-line, no constraint, or an immediate parallel contradiction. An empty intersection with $z\geq\ell$ therefore has a contradiction from one upper/domain pair, one parallel pair, or one lower and one upper bound. The envelope identifies these constraints at its maximizing gap location. Its separate checker uses only the indicated binary coefficients and exact rational subtraction/division. It neither trusts a floating intersection nor reconstructs the hull.

The envelope is the lower envelope of \emph{{upper-band}} lines. Every original lower-band line is queried afterwards. Removing a line from the envelope does not remove its candidate index. This distinction preserves an action that minimizes only at one response. For example, $\mu_0=1$, $\mu_1=z$ and $\mu_2=2-z$ give action0 the singleton interval $\{{1\}}$; it is the lowest-index argmin at that response. This is a synthetic unit example, not an added engineering optimization sample. Classical acceptance-set geometry is acknowledged in the main bibliography; no first-ever affine-envelope claim is made.

\subsection{{Paired construction times and complete cost scope}}
The frozen pairwise reader is the same-contract reference, not a state-of-the-art library benchmark. Both algorithms receive identical coefficient centers and outward error bands. Three repeated timings per branch/domain alternate algorithm order; casewise medians are summed. They give {timing['pairwise_pruner_seconds']:.6f} versus {timing['envelope_pruner_seconds']:.6f} seconds, ratio {ratio:.6f}. Complete independent proof replays separately require {timing['old_independent_proof_check_seconds']:.6f} versus {timing['new_independent_proof_check_seconds']:.6f} seconds. These single replay passes are additional component measurements; their combined ratio is {total_ratio:.6f}. Machine load, implementations, thread settings and versions limit transfer of the absolute times.

Shared GP coefficient work, original initial data and baseline endpoints are not charged as if avoided. The earlier execution paid44,146 unique state/design physical-bound computations and176.433648 seconds of construction. Its GP coefficient/outer-set component took21.019126 seconds and rational construction replay4.000773 seconds; grading took5.936882 seconds. The new benchmark/reconstruction is additional verification work, not a deduction from those historical elapsed times. No end-to-end rerun is performed and no realized deployment saving is claimed. Logical reader requests116,850 versus568, and unique cached requests44,146 versus498, remain counterfactual for the subset reader.

\subsection{{H1 and H5 interpretation}}
Both domains include114/114 stored next actions. All232,564 original and232,564 new exclusions pass independent rational checking. The new exact intervals are subsets of the original outward intervals; regrading them leaves all71 nonbaseline H1 contrasts per domain abstaining and all43 baseline selections uncertified. The H1 completed baseline is already paid and fallback is not a selection certificate. H5 reachability is not implemented. The original independent-study gate remains false, while the computational-stage increment is separately verified.

Runtime for this check is Python3.12, NumPy2.3.5, SciPy1.17.0 and scikit-learn1.8.0 with one BLAS thread. New physical attempts, physical-bound queries, hyperparameter fits, independent optimization samples and confirmatory families are zero. Two previous witness attempts bring the reported project total to55,309. Stored execution and verification records identify exact source/output hashes and dependent reporting units.
'''
    # Supplement compiles independently: avoid cross-document unresolved labels.
    appendix = appendix.replace(r'Equation~(\ref{eq:affine_binary})', 'The affine-mean equation')
    (dest/'integrated_evidence/gp_envelope_completion.tex').write_text(appendix)
    bib = (baseline/paper/'EO_references.bib').read_text()
    bib += '''\n@article{ref40,
  author = {Peter Frazier and Warren Powell and Savas Dayanik},
  title = {{The Knowledge-Gradient Policy for Correlated Normal Beliefs}},
  journal = {INFORMS Journal on Computing},
  year = {2009},
  volume = {21},
  number = {4},
  pages = {599--613},
  doi = {10.1287/ijoc.1080.0314},
}\n'''
    (dest/'EO_references.bib').write_text(bib)
    # Scientific plot uses measured paired timers; original figures are preserved.
    import csv
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
    print('Completed evidence-grounded manuscript source and computational figure.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', type=Path, default=Path('revision'))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    build(root, args.revision)
