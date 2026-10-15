"""Write the focused scientific manuscript from recorded, preserved results.

No PDF creation/upload, packaging, model fitting or engineering evaluation.
The full earlier manuscript and every historical supplementary row are retained.
"""
from pathlib import Path
import hashlib
import json
import re
from .prepare_submission_20261014 import numeric

BASELINE='58f539c2d0738b20c7d0d4889fe8d808a03a3019'


def build(root):
    prep=root/'submission_20261014';paper=prep/'source/paper/engineering_optimization'
    active=paper/'EO_manuscript.tex';archive=paper/'archival/EO_full_evidence_20261014.tex'
    archive.parent.mkdir(exist_ok=True)
    if not archive.exists():archive.write_bytes(active.read_bytes())
    old=archive.read_text()
    s=json.loads((root/'results/gp_strong_comparison_20261015/analysis.json').read_text())
    route=json.loads((root/'results/h1_certificate_routing_20261015/analysis.json').read_text())
    diagnostic=json.loads((root/'results/nominal_band_diagnostic_20261015/analysis.json').read_text())
    assert s['complete'] and s['all_exact_sets_and_intervals_equal']
    assert route['nonbaseline_scalar_requests_early_rejected']==142
    assert diagnostic['cases']==228 and diagnostic['counts']['extra_band_actions']==0
    assert diagnostic['counts']['shared_intervals_changed']==908
    design=json.loads((root/'results/gp_strong_comparison_20261015/DESIGN.json').read_text())
    for n,h in design['source_hashes'].items():assert hashlib.sha256((root/n).read_bytes()).hexdigest()==h
    speed=s['filtered_pairwise_over_integer_workflow'];filter_speed=s['filtered_pairwise_over_integer_construction']
    abstract=rf'''We study certified numerical computation of possible next actions before a pending engineering response is observed. Classical affine-envelope geometry is adapted to fixed-kernel Gaussian-process coefficient bands, closed response intervals and independently checked exclusions. A common-scale integer implementation agrees exactly with an optimized pairwise control on all 228 archived beam-design branch/domain cases. Filtering is {filter_speed:.2f} times faster; including coefficient reconstruction and independent checking gives a {speed:.2f}-fold improvement. Against the same-complexity Fraction envelope, the corresponding ratios are 4.46 and 1.70. A frozen nominal-versus-band diagnostic finds identical retained indices in every case, although all 908 shared intervals widen. Thus these engineering data do not demonstrate rescue of additional actions. An elementary domain-cover identity explains the failed H1 lower certificates and permits their scalar rejection without action-set construction in all 142 nonbaseline requests. Two cases selected before diagnostic outputs illustrate the required information and cost boundaries. These dependent development results establish a specialized implementation and its decision limits, rather than a new optimization principle, improved physical designs or deployment savings.'''
    front=old[:old.index(r'\begin{abstract}')]+r'\begin{abstract}'+'\n'+abstract+'\n'+r'''\end{abstract}
\begin{keywords}
surrogate-assisted engineering optimization; Gaussian processes; certified action sets; exact arithmetic; certificate routing
\end{keywords}
\noindent{\small\textit{Preparation copy: affiliations b and c remain to be supplied.}}

'''
    begin=old.index(r'\subsection{Certified response-domain action sets}')
    end=old.index(r'\hypertarget{decision-pathways-and-ranking-invariance}',begin)
    method=old[begin:end].replace('Algorithm 2. Exact band-envelope audit.','Algorithm 1. Exact band-envelope audit.')
    method=method.replace('Theorem 1 (closed-domain band filter).',
                          'Theorem 1 (classical-envelope specialization to closed bands).')
    body=r'''\section{Introduction}

Surrogate-assisted engineering optimization converts predictions into choices of expensive design evaluations \citep{ref01,ref02,ref03,ref35}. A useful computational question arises before a pending response is observed: which eligible designs can still be chosen by a declared posterior-mean continuation? A sound answer must keep every permitted minimizer, including actions that are optimal only at an isolated response. An engineering decision aid also needs to recognize when computing that answer cannot change its requested certificate.

We address these two computations within an existing finite design workflow. The first output is a complete relaxed-band action set with exact response intervals and independently verifiable exclusions. The second is a Boolean H1 lower-certificate test. Their output contracts differ: a scalar rejection does not supply an action set or establish actual design inferiority. Keeping those contracts explicit allows computational work to be removed without changing the requested result.

The affine structure of fixed Gaussian-process (GP) updates and envelope computations is established \citep{ref40,ref42}. The shared-envelope core here is isomorphic, after a sign change, to the classical affine-breakpoint construction. Reliable geometric predicates and exact arithmetic are also established \citep{ref41}. We therefore frame this work as a specialized certified numerical implementation and verification study. Its outputs combine binary-system coefficient bands, complete closed action intervals and independently replayable exclusions. The scalar router is an auxiliary use rule derived from the same contract. We do not claim a new geometric algorithm, a new acquisition policy or global convergence of an optimizer.

The engineering evaluation uses all retained states of two previously observed structural-design datasets. We compare complete outputs with both an independent optimized pairwise control and a same-complexity Fraction envelope, charging common coefficient reconstruction and independent proof checking. A subsequent frozen-coefficient diagnostic finds no additional retained indices from bands on these data, and two cases chosen before its outputs make the engineering use conditions explicit. An elementary domain-cover identity explains why none of the nonbaseline H1 lower certificates can succeed with the available pending-point information. The original adverse optimization and horizon results remain in the supporting evidence.

\section{Related work and the computation being compared}

Surrogate-assisted search and Bayesian optimization select evaluations through explicit model-management and acquisition rules \citep{ref01,ref02,ref03,ref18}. Rigorous surrogate-management frameworks require their own search assumptions \citep{ref38}; no such global convergence result follows from the present filter. Knowledge-gradient and lookahead policies evaluate future information to select observations \citep{ref39,ref40}. Our declared continuation instead takes a posterior-mean minimum on a finite eligible pool with fixed hyperparameters.

The author-maintained software snapshot accompanying \citet{ref40} provides the closest explicit affine construction \citep{ref42}. In its \texttt{AffineBreakpoints} routine, set the nominal intercept and slope to $a^{\rm KG}_j=-b_j^+$ and $b^{\rm KG}_j=-a_j^+$. Its increasing-slope maximum envelope becomes our decreasing-slope minimum envelope of upper lines. The intersection formula and stack-deletion ordering then agree. The original expected-maximum calculation can discard zero-measure support without error for its own functional. Our contract instead queries every original lower line and keeps singleton feasibility and candidate identities. Adapting the classical envelope this way retains $O(M\log M)$ arithmetic complexity; the present formulation is not an asymptotic breakthrough. Source identities and the inspected file hashes are recorded with the reproduction materials.

Coefficient bands change the requested numerical output. For example, nominal means $1$, $33/32$, $z$ and $2-z$ never select the second constant. With that constant's intercept enclosed by $[31/32,35/32]$, its relaxed-band interval becomes $[31/32,33/32]$. This synthetic example motivates retaining a band-feasible action; it is not an engineering sample or a claim that coupled GP errors realize every independent box corner. Section~\ref{sec:nominal_diagnostic} reports that this additional-action effect is absent from the archived beam cases.

Our strong control uses vectorized floating-point pairwise proposals, exact checks, and complete exact scans for unresolved candidates. It does not construct the shared envelope. It is an optimized same-output reference, not a claim to represent every library or the best possible implementation. Exact-predicate foundations are acknowledged \citep{ref41}; their use alone is not presented as an original discovery.

\section{Certified action-set computation}

'''+method+r'''
\subsection{Exact meaning of the relaxed bands}

\textbf{Proposition 1 (independent-band realizability).} For a fixed $z\geq0$, $z\in R_i$ if and only if some selection of coefficients from the independent bands makes action $i$ a posterior-mean minimizer at $z$.

\textit{Proof.} Necessity is the enclosure argument in Theorem 1. For sufficiency choose both lower endpoints for candidate $i$ and both upper endpoints for every other candidate. Nonnegative $z$ makes these choices attain $L_i(z)$ and $U_j(z)$ simultaneously. The defining inequalities then make $i$ minimal, with equality allowed. This statement concerns the independent-band relaxation, not realization by the coupled GP coefficients.\hfill$\square$

\subsection{Common-scale integer envelope}

Every finite binary coefficient is a dyadic rational. Choose a common power-of-two denominator $D$ and write $A_i^\pm=Da_i^\pm$, $B_i^\pm=Db_i^\pm$. Each necessary inequality is
\begin{equation}
 (A_i^- - A_j^+)z\leq B_j^+-B_i^- .\label{eq:integer_band}
\end{equation}
Sorting and parallel-line tests are integer operations. Breakpoints are unreduced numerator/positive-denominator pairs and are compared by cross-products. At $z=p/q$, the envelope-gap sign is the sign of $(A_j^+-A_i^-)p+(B_j^+-B_i^-)q$. Reduced fractions are constructed for returned intervals and envelope breakpoints, rather than inside every predicate.

Every original lower line is queried even if its corresponding upper line disappears from the envelope. Closed equality is retained throughout. The integer representation preserves Theorem 1's exact output and arithmetic-operation count, with integer bit complexity additional. Extreme exponent differences can enlarge $D$; the operation count is not a machine-time guarantee. A separate checker reconstructs binary coefficients as rational values and checks only the candidate and its at most two rivals. It does not trust the hull or its intersections.

\subsection{Independent filtered pairwise control}

For each block of 64 candidates, NumPy ratios propose extremal lower and upper constraints from all competitors. Every proposed exclusion is checked using Eq.~\eqref{eq:integer_band} in exact integers. Unresolved candidates receive a complete exact scan, returning their exact feasible interval or a one/two-rival infeasibility witness. Overflow or NaN in a proposal can cause fallback but cannot justify an unchecked exclusion. For fixed block size, proposal work is quadratic with linear workspace. Both algorithms include band validation and common-scale conversion in their filtering timer.

\section{Domain-cover saturation and certificate routing}

Let $d\geq0$ be the declared domain endpoint, $p$ the already available pending-point lower bound, $m_0$ the initial incumbent, and $\mathcal R=\{i:R_i\ne\varnothing\}$. Write $l_i=\inf R_i$. A paid baseline endpoint $B$ and fixed relative margin $\epsilon$ define $T=B-\epsilon m_0$. The scalar lower-certificate request is whether $J\geq T$, with $J$ from Eq.~\eqref{eq:joint_lower}.

\textbf{Proposition 2 (pending-bound saturation).} Finite ordered coefficient bands on $[d,\infty)$ give
\begin{equation}
 \min_{i\in\mathcal R}l_i=d,\qquad
 J=\min\{m_0,\max(p,d),\min_{i\in\mathcal R}\lambda_i\}.
 \label{eq:saturation}
\end{equation}

\textit{Proof.} At every $z\geq d$, choose an index $j$ minimizing the finite set of upper lines. Band ordering gives $L_j(z)\leq U_j(z)\leq U_k(z)$ for every $k$, so $z\in R_j$. The sets cover the domain, and at least one contains $d$. All lower endpoints are at least $d$, hence their minimum is $d$. Distributing the finite minima in Eq.~\eqref{eq:joint_lower} and using $\min_i\max(p,l_i)=\max(p,d)$ gives the identity.\hfill$\square$

\textbf{Corollary (sound early rejection).} If $\min\{m_0,\max(p,d)\}<T$, this particular lower certificate cannot pass, regardless of further next-point bounds. A lazy reader can return the same Boolean false without constructing an action set. Equality requires continuing to the next-bound test.

\textbf{Algorithm 2. Output-aware routing.} If complete actions/intervals are requested, run Algorithm 1 with integer predicates. For a scalar no-better certificate, first evaluate the corollary. If it rejects, return certificate failure without invoking the action-set reader. Otherwise obtain the retained actions and their already available next-point bounds, and compare Eq.~\eqref{eq:saturation} with $T$.

The corollary does not establish that an alternative is actually better, tied or inferior. It does not replace a requested complete category interval, a selection rule, or an H5 reachable-history analysis. The pending bound must already be available or paid for. The minimum algebra and early-exit principle are elementary; the useful result is their exact consequence for this audit and an executable route that avoids an ineffective computation.

For the two frozen domains, $d=0$ or $d=p$, so $\max(p,d)=p$. Consequently action-set refinement alone cannot lift this lower certificate above the pending bound. This is stronger than merely counting failed terms at the observed states: it identifies a structural limit of the declared computation.

On these domains the rejection condition is simply $\min(m_0,p)<T$. Implementing that necessary threshold test does not require a new optimization algorithm. The domain-cover proof explains when it equals the earlier interval-based lower-certificate obstruction; the router records its use without claiming a separate principle of early rejection.

\section{Engineering setting and verification protocol}

\subsection{Structural design problem and fixed information}

EngiBench Beams2D v1 models half a symmetric Messerschmitt--Bolkow--Boehm beam \citep{ref23}. The domain has $100\times50$ bilinear elements, left-boundary horizontal symmetry, a lower-right vertical support and a unit downward top-left nodal load. SIMP uses stiffness limits $10^{-9}$ and 1, exponent 3, and Poisson ratio 0.3; smaller compliance is preferred. Nineteen effective logits plus one anchor form a $4\times5$ coarse field, interpolated to $50\times100$; a logistic shift fixes mean density to 0.35. This is a smooth 19-dimensional engineering design family.

Both complete ten-group datasets and all 60 metadata states are retained. Seventeen action-alias-only states need no bound construction. The remaining 43 contexts contain 114 first-action branches with eligible pools of 1024 actions. Two domains give 228 dependent branch/domain cases. These are already observed development data; the former holdout is not a new unseen validation set.

The frozen two-witness diagnosis has consumed both permitted attempts. The recorded true responses, approximately 14324.74 and 9639.92, are far above their trial lower bounds, approximately 232.53 and 200.60. This supports a weak-point-bound diagnosis at those witnesses. Equilibrium residuals do not establish mesh or physical accuracy at the decision margin. This study adds no physical evaluation, replacement, retry, bound query, hyperparameter fit or independent optimization sample.

\subsection{Same-output timing and separate routing verification}

The computational comparison uses the Fraction envelope, the filtered pairwise control and the integer envelope. All receive identical binary bands and domains. Each branch's fixed kernel and cross matrix are reconstructed three times; hashes and coefficient arrays must match the frozen records exactly. The comparison does not expose the pending or next response when constructing sets. Exact equality with the earlier intervals preserves the already recorded next-action inclusion without creating new label validation.

Three repetitions rotate method order. Reported totals sum casewise medians for coefficient reconstruction, filtering and independent rational proof replay. Coefficient work is timed once per branch and charged identically to both domains. Every method's complete proof set is checked in every repetition. Python 3.12, NumPy 2.3.5, SciPy 1.17.0 and scikit-learn 1.8.0 use one BLAS thread. Timings, branches and domains are dependent; no independent-sample significance claim is made.

The separate router verification reconstructs the historical scalar result from archived complete intervals as an oracle, verifies Eq.~\eqref{eq:saturation} exactly, then evaluates the lazy route. Its callback contains the actual integer action-set operation and next-bound reader. Reference verification work is outside the routing call; we report callback counts, not an end-to-end speed claim for this exercise. No historical physical/bound acquisition cost is removed.

\section{Results}

\subsection{Correct outputs and same-output computational improvement}

All 228 exact action sets and feasible intervals agree across the three algorithms. Each complete pass has 232,564 exclusions, all accepted by the independent checker in every repetition. Retained sets contain 2--7 actions and inherit inclusion of every stored next action. The scaled coefficients have 84--103 bits on these inputs.

Six numerical test groups compare both implementations against an independent all-pairs Fraction oracle: closed singleton/domain ties, duplicate parallel candidates, floating-proposal overflow, subnormal and mixed exponents, randomized interval bands, and nominally dominated but band-feasible actions. Four router tests cover early rejection without callback use, closed-threshold equality, a stronger valid domain and a failing next-point bound. These are program tests, not new engineering samples.

\begin{table}[htbp]\centering\small
\caption{Sum of casewise component medians over all 228 dependent branch/domain cases. I/O, grading, physical evaluations and historical bound acquisition are excluded.}\label{tab:strong_comparison}
\begin{tabular}{lrrrr}\toprule
Method & Coefficients (s) & Filter (s) & Proof check (s) & Sum (s)\\\midrule
'''
    for key,label in [('fraction_envelope','Fraction envelope'),('filtered_pairwise','Filtered pairwise'),('integer_envelope','Integer envelope')]:
        t=s['timings'][key]
        body+=f"{label} & {s['coefficient_seconds_sum']:.4f} & {t['construct']:.4f} & {t['check']:.4f} & {t['workflow']:.4f} \\\\\n"
    body+=rf'''\bottomrule\end{{tabular}}\end{{table}}

Integer filtering is {filter_speed:.2f} times faster than the optimized pairwise control. Charging the same coefficient reconstruction and independent checks gives {speed:.2f} times faster computation, or approximately {100*(1-1/speed):.1f}\% less time for these three components. The integer sum is lower in all 228 cases. These observed gains concern a specified implementation and computational task, rather than universal library superiority or complete engineering deployment savings.

The same recorded comparison also separates representation cost from the quadratic control. Against the Fraction envelope, which has the same asymptotic operation count, integer filtering is 4.46 times faster and the three-component sum is 1.70 times faster. These are implementation-specific observations, not comparisons with every optimized classical-envelope library.

'''+r'''\subsection{Frozen nominal-versus-band diagnostic}\label{sec:nominal_diagnostic}

The diagnostic reads the frozen nominal slopes and intercepts as point coefficients, computes their exact closed intervals and compares them with the previously verified band intervals. It does not reconstruct a kernel, refit a GP or replay the full proof benchmark. All 228 nominal index sets equal their band counterparts: no additional action is retained by the bands in these engineering data. All 908 shared action intervals are wider in at least one endpoint, with 680 lower and 680 upper endpoints changed. Every nominal interval is contained in its band interval.

For each finite changed endpoint, divide its outward displacement by $\max(1,|e_0|)$, where $e_0$ is the nominal endpoint. The median and maximum are $5.7389010\times10^{-9}$ and $5.8820973\times10^{-5}$. This measures displacement between numerical contracts, not physical error, statistical coverage or true-GP coefficient error. The synthetic example demonstrates a possible contract difference; the beam results do not establish that bands rescued an otherwise lost engineering action.

\subsection{A structural limit that makes routing useful}

Equation~\eqref{eq:saturation} holds exactly in all 228 archived branch/domain cases and reproduces the recorded scalar lower bound. The router returns the same Boolean certificate result in every case. It invokes the action-set callback zero times, including all 142 nonbaseline branch/domain requests (71 distinct contrasts per domain). Thus the requested scalar rejection can be computed without action-set construction once its pending bound and comparator threshold are available.

This does not make the independent study gate pass. All 71 nonbaseline H1 contrasts still abstain under the original complete category rule, and the 43 baseline-selection certificates remain unestablished. The H5 reachable-history extension is not implemented. The new router preserves a limited certificate predicate; it does not relabel these negative decisions as successful optimization.

The earlier term decomposition remains informative: each domain has 281 retained action terms, 71 failing pending terms and 276 failing next-point terms. The median weakest next-bound/threshold ratio is 0.1622233735904155. Proposition 2 explains why increasing action-set precision alone cannot repair the pending-term obstruction for either frozen domain. Obtaining a useful judgment needs information that raises the applicable response lower endpoint or otherwise changes the declared certificate.

\subsection{Engineering computation and complete cost boundaries}

The practical use is conditional on the requested output. A full-set request receives exact intervals and replayable exclusion witnesses more efficiently on these structural-design states. A scalar no-better request can reject ineffective analysis before invoking that engine. Neither operation claims to improve the physical design objective.

Before computing the nominal diagnostic, we fixed one illustrative case per dataset: the first construction filename and its first branch in lexical order. Case A is archived state \texttt{gp\_ei\_shared\_init\_r0\_t101}, branch 0; case B is former-holdout state \texttt{beam\_holdout\_r11\_ei}, branch b0. Both domains are retained. Table~\ref{tab:engineering_examples} gives their required scalar information. In each case the paid comparator equals the initial incumbent. Both nominal and band readers retain the same three actions in A and the same five in B, from pools of 1024.

\begin{table}[htbp]\centering\small
\caption{Predetermined engineering examples; rounded displays, with exact interval endpoints in the recorded diagnostic.}\label{tab:engineering_examples}
\begin{tabular}{lrrr}\toprule
Case & Pending bound $p$ & Threshold $T$ & Retained actions\\\midrule
A & 407.257488 & 2872.944916 & 3\\
B & 684.825302 & 1935.045522 & 5\\\bottomrule
\end{tabular}\end{table}

Since $\min(m_0,p)<T$, both cases return the same scalar certificate failure without constructing actions. Case B is itself a baseline branch, as fixed by the selection rule; it supplies no independent policy win. Its known path identity can provide information beyond the weak bound-only certificate, so an abstention from that certificate is not a judgment against self-comparison. The complete response intervals extend without an upper bound and have switching responses of order $10^7$--$10^8$ in these examples. Such mathematical tails must not be described as observed or typical physical responses. Full interval tables and branch identities are recorded in the supplement.

In a warm request, $p$, $m_0$ and $T$ are already available, so the scalar guard can precede action-set construction. In a cold request, acquiring a sound pending bound and the paid comparator remains a prerequisite and a cost. No cold deployment or physical saving is measured here.

The historical GP comparison acquired 44,146 distinct state/design bounds and took 176.433648 s for construction before grading. Its full-pool and subset readers have 116,850 versus 568 logical bound requests, or 44,146 versus 498 unique requests under their respective cache rules. Subset request counts are counterfactual because the complete library had already been acquired. The pending bound used by routing is not free in a cold deployment. The project ledger remains 55,309 physical attempts, including the two witnesses. No paid work is refunded by the new readers.

\section{Discussion and limitations}

The supported contribution is a specialized certified numerical implementation and verification study within surrogate-assisted optimization. Its envelope core is classical, common-scale dyadic arithmetic is a representation choice, and the frozen-domain guard is an elementary necessary-condition test. The integrated contract and reproducible same-output comparisons document a concrete engineering computation. They do not, by themselves, establish an original optimization principle or priority over all related certified-envelope work.

The engineering diagnostic limits the practical claim further: bands widen response intervals but retain no additional indices on the available states. There is no observed recovery of an extra engineering action or successful new H1 decision. The computational gains therefore support more efficient delivery of a specified numerical output, with an explicit account of when that output is unnecessary. Neither test counts nor timing ratios demonstrate optimization-policy efficacy.

The engineering evidence is limited to archived states of one deterministic beam family. There is no new independent policy-performance experiment, no physical/PDE error certificate and no realized FE saving. Exact-band feasibility can overapproximate coupled GP coefficient realizability. Kernel evaluation error and native floating predictions at every unknown response are outside the binary-system guarantee. The inverse-residual enclosure assumptions remain conditional; a failed enclosure gate requires retaining the full pool. The scalar router assumes sound closed-domain coverage and available bounds and cannot replace other requested outputs.

The complete preceding manuscript and all historical adverse tables are retained in the archive and supplement. Twenty-two of 25 supporting paired-grid raw records are available; three final recovery records remain missing. Derived tables do not replace their raw replay or establish mesh convergence. The current GP inputs, original certificates, new algorithms and complete recorded comparisons support scoped zero-solver reproduction.

\section{Conclusion}

For a fixed-kernel GP continuation, a classical envelope adapted to binary coefficient bands can deliver complete closed action intervals and independently checkable exclusions. Common-scale integer predicates reduce the recorded computation time against both the optimized pairwise control and the same-complexity Fraction implementation. In the beam archives, bands widen intervals but rescue no additional action. The elementary domain-cover identity explains the unchanged H1 obstruction and allows the specified scalar failure to be returned before constructing action sets. The result is a bounded numerical implementation and decision-limit study. Positive optimization-policy efficacy, physical accuracy at the decision margin and complete deployment savings remain unestablished.

'''
    closing=old[old.index(r'\section*{Acknowledgements}'):]
    closing=closing.replace('As of 14 October 2026','As of 15 October 2026')
    closing=closing.replace('the certified-envelope proof details and H1 cost boundaries',
                            'the integer-filter and scalar-router proof details, recorded strong comparisons and H1 cost boundaries')
    closing=closing.replace('These materials support zero-solver reproduction of the current action-set contribution.',
        'These frozen inputs support zero-solver reproduction when combined with the current sources. The 15 October implementation, same-output comparison and nominal-band diagnostic are preserved separately as text, code and results on the private research branch; the earlier packet alone does not include those updates.')
    active.write_text(front+body+closing)
    bib=paper/'EO_references.bib'
    if '@article{ref41,' not in bib.read_text():
        bib.write_text(bib.read_text()+r'''
@article{ref41,
 author = {Shewchuk, Jonathan Richard},
 title = {Adaptive Precision Floating-Point Arithmetic and Fast Robust Geometric Predicates},
 journal = {Discrete \& Computational Geometry},
 volume = {18}, pages = {305--363}, year = {1997},
 url = {https://www.cs.cmu.edu/~quake/robust.html}
}
''')
    if '@misc{ref42,' not in bib.read_text():
        bib.write_text(bib.read_text()+r'''
@misc{ref42,
 author = {Frazier, Peter and Powell, Warren B. and Dayanik, Savas},
 title = {Software Snapshot for: The Knowledge-Gradient Policy for Correlated Normal Beliefs},
 howpublished = {INFORMS Journal on Computing software archive},
 year = {n.d.},
 doi = {10.1287/ijoc.1080.0314.cd},
 url = {https://github.com/INFORMSJoC/1080.0314},
 note = {Author-maintained historical software snapshot; files inspected 15 October 2026}
}
''')
    supp=paper/'EO_supplementary.tex';text=supp.read_text()
    marker=r'\input{integrated_evidence/contribution_20261015.tex}'
    if marker not in text:
        text=text.replace(r'\bibliographystyle{tfcad}',marker+'\n'+r'\bibliographystyle{tfcad}')
        supp.write_text(text)
    note=rf'''\section{{Exact integer comparison and scalar-certificate routing}}

The active manuscript now focuses on certified action filtering and output-aware routing. Its prior complete source is preserved as \path{{archival/EO_full_evidence_20261014.tex}}. All historical numerical rows remain in that archive and this supplement.

The three-method comparison uses all 43 contexts, 114 branches and 228 branch/domain cases. All exact sets and intervals agree with the prior Fraction certificates. Each method supplies 232,564 exclusions per full pass, independently checked in each of three rotating-order repetitions. The recorded filter speed ratio is {filter_speed:.9f}; the three-component ratio, charging common coefficient reconstruction and proof checks, is {speed:.9f}. All 228 integer component sums are smaller than the filtered pairwise sums. Times are dependent development observations and exclude I/O, grading, physical work and historical bound acquisition.

For the scalar H1 lower certificate, domain coverage gives $\min_i\inf R_i=d$ and therefore $J=\min\{{m_0,\max(p,d),\min_i\lambda_i\}}$. Choose a minimal upper-band line at $d$; its lower line is below every upper line, so its interval contains $d$. Distributing the minima proves the identity. If $\min(m_0,\max(p,d))<T$, a lazy reader can reject the certificate without constructing actions. Equality must proceed to the next-bound reader. This result does not decide true inferiority, a full category or H5 behavior.

All 228 archived identities and scalar predicates match exactly. All 142 nonbaseline requests reject before the actual action-set callback; the same is true for the 86 baseline-branch requests. Oracle reconstruction is verification overhead, not a claimed free production computation. Historical acquisition costs remain charged. No new physical evaluation, bound query, GP fit or independent optimization sample is made, and no original gate is changed.

Recorded outputs and pre-run source/input hashes are in \path{{results/gp_strong_comparison_20261015/}}; routing verification and its source/input hashes are in \path{{results/h1_certificate_routing_20261015/}}. The six action-set test groups and four routing tests are numerical program cases. Earlier tests, physical costs, failure labels and the missing paired-grid raw-record disclosure remain separate and unchanged. No previous unpreserved timing is used as evidence.
'''
    note+=r'''
\subsection{Closest construction and contribution scope}

The author-maintained knowledge-gradient snapshot \citep{ref42} contains \texttt{AffineBreakpoints.m}, \texttt{AffineBreakpointsPrep.m} and \texttt{LogEmaxAffine.m}. Setting its intercept and slope to $-b_j^+$ and $-a_j^+$ gives the same shared upper-line envelope after sign reversal, with the same intersection and stack ordering. Querying every original lower line extends the output contract without a new asymptotic complexity result. Short one-dimensional exclusion proofs, exact predicates and the frozen-domain guard are not claimed as new mathematical foundations. Source file hashes are recorded in \path{paper/engineering_optimization/contribution_closure_20261015/CLOSEST_SOURCE_RECORD.json}.

The same recorded three-method run gives integer implementation speedups relative to the Fraction envelope of 4.46 for filtering and 1.70 for the three components; their asymptotic operation counts agree. The comparison with the optimized pairwise control does not alone establish algorithmic novelty.

\subsection{Nominal diagnostic and predetermined engineering examples}

Frozen nominal coefficients give exactly the same retained indices in all 228 branch/domain cases as the bands. All 908 shared intervals widen, with 680 lower and 680 upper endpoints changed. Nominal intervals are contained in the band intervals. For changed finite endpoints, outward displacement divided by $\max(1,|e_0|)$ has median $5.7389010\times10^{-9}$ and maximum $5.8820973\times10^{-5}$. No added engineering action or successful new H1 decision is demonstrated. This diagnostic creates no GP system, physical evaluation, bound query or independent sample and does not rerun the timing/proof benchmark.

Before diagnostic outputs, one case per dataset was fixed by first filename and first lexical branch. A is \texttt{gp\_ei\_shared\_init\_r0\_t101}, branch 0, and B is \texttt{beam\_holdout\_r11\_ei}, branch b0. A is nonbaseline; B is a baseline branch and cannot be presented as an independent policy win. Both response domains are kept. Their pending bounds are approximately 407.257488 and 684.825302, below thresholds 2872.944916 and 1935.045522. The scalar guard therefore returns certificate failure in both. Path identity in B provides information outside this numerical bound-only request.

\begin{table}[htbp]\centering\small
\caption{Trial-lower-domain intervals in the predetermined cases. Approximate displays only; exact rational pairs are in the diagnostic JSON.}
\begin{tabular}{llrr}\toprule
Case & Local eligible index & Response lower endpoint & Response upper endpoint\\\midrule
A & 156 & 10804388.9161 & 65213438.5057\\
A & 223 & 65213438.4116 & $\infty$\\
A & 991 & 407.257488 & 10804388.9350\\
B & 118 & 34020243.1438 & 202700114.0870\\
B & 417 & 10700230.4110 & 18261454.9959\\
B & 430 & 18261454.9048 & 34020243.1720\\
B & 662 & 684.825302 & 10700230.4182\\
B & 945 & 202700114.0304 & $\infty$\\\bottomrule
\end{tabular}\end{table}

The nominal and band index sets are $\{156,223,991\}$ in A and $\{118,417,430,662,945\}$ in B. The unbounded response domain is a model contract; switches of order $10^7$--$10^8$ are not observed or typical beam responses. Warm scalar requests assume the pending bound and paid comparator are already available. Cold acquisition costs remain charged; no new deployment was run. The three-component difference of 2.208568264 seconds and historical bound-library construction of 176.433648 seconds concern different scopes and are not combined into a measured deployment speedup.

Preselection, all 228 diagnostic rows, exact example intervals and input hashes are in \path{results/nominal_band_diagnostic_20261015/}. The closest-method review and engineering interpretation accompany the contribution record. They constrain the paper to implementation/verification evidence, with originality of an optimization method and positive engineering efficacy unestablished.
'''
    (paper/'integrated_evidence/contribution_20261015.tex').write_text(note)
    baseline_main=(root/'baseline/paper/engineering_optimization/EO_manuscript.tex').read_text()
    baseline_supp=(root/'revision/paper/engineering_optimization/EO_supplementary.tex').read_text()
    assert not numeric(baseline_main)-numeric(old)
    assert not numeric(baseline_supp)-numeric(supp.read_text())
    meta=json.loads((prep/'PORTAL_FIELDS.json').read_text())
    keywords=['surrogate-assisted engineering optimization','Gaussian processes','certified action sets','exact arithmetic','certificate routing']
    meta.update(abstract_tex=abstract,abstract_plaintext=abstract,abstract_whitespace_word_count=len(abstract.split()),
                keywords=keywords,ready_for_final_submit=False)
    (prep/'PORTAL_FIELDS.json').write_text(json.dumps(meta,indent=2)+'\n')
    (prep/'ABSTRACT_AND_KEYWORDS.txt').write_text(meta['title']+'\n\n'+abstract+'\n\nKeywords: '+'; '.join(keywords)+'\n')
    report={'baseline':BASELINE,'focused_main_text_updated':True,'complete_older_main_preserved':str(archive.relative_to(root)),
      'all_32_baseline_main_numeric_rows_retained_in_archive':True,'all_251_supplement_numeric_rows_retained':True,
      'strong_comparison_cases':228,'filter_speed_ratio':filter_speed,'three_component_speed_ratio':speed,
      'nonbaseline_scalar_requests_early_rejected':142,'nonbaseline_action_set_callback_calls':0,
      'new_numerical_test_groups_passed':10,'new_physical_evaluations':0,'new_bound_queries':0,
      'new_GP_hyperparameter_fits':0,'new_independent_optimization_samples':0,'remaining_witness_attempts':0,
      'H1_H5_or_independent_gate_changed':False,'optimization_policy_performance_improvement_demonstrated':False,
      'complete_physical_deployment_savings_demonstrated':False,'journal_novelty_sufficiency_certified':False,
      'closest_method_source_review_completed':True,'shared_envelope_core_is_classical':True,
      'new_asymptotic_complexity_result_claimed':False,'scalar_guard_is_elementary_use_rule':True,
      'positioning':'Specialized certified numerical implementation and verification study',
      'nominal_band_cases':diagnostic['cases'],'additional_band_actions_observed':0,
      'shared_nominal_band_intervals_widened':908,'predetermined_engineering_cases':2,
      'positive_engineering_action_rescue_demonstrated':False,
      'Engineering_Optimization_originality_threshold_demonstrated':False,
      'target_fit_reviewer_inference':'Substantial originality/desk-review risk as a new optimization method; no journal decision inferred',
      'PDF_or_ZIP_uploaded':False,'PDF_or_ZIP_created_this_step':False,
      'author_facts_and_venue_conditions_still_pending':True,'final_submit_ready':False}
    (prep/'CONTRIBUTION_CHECK_20261015.json').write_text(json.dumps(report,indent=2)+'\n')
    status=json.loads((paper/'work_status.json').read_text());status['contribution_20261015']=report
    status['submission_ready']=False;(paper/'work_status.json').write_text(json.dumps(status,indent=2)+'\n')
    return report


if __name__=='__main__':print(json.dumps(build(Path(__file__).resolve().parents[1]),indent=2))
