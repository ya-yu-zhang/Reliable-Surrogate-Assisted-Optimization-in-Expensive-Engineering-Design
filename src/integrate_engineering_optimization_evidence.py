"""Generate new evidence sections from audited outputs; preserve old tables."""
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
PAPER=ROOT/"paper"


def table(headers, rows):
    return "| "+" | ".join(headers)+" |\n| "+" | ".join(["---"]*len(headers))+" |\n"+"".join("| "+" | ".join(map(str,r))+" |\n" for r in rows)


def readable_prose(text):
    words="Section|Table|Figure|dimension|volume|fraction|force|all|every|in|under|at|max|after|before|a|each|four|Their|The|Its|their|contains|contain|include|uses|requires|require|versus|scale|retains|total|is|to|with|by|than|on|or|budget|Python|paid|has|giving|and|only|plus|over|across|than|from|of|positive|further|per|within|NumPy|SciPy|EngiBench|kappa|are|makes|fixed|but|pays|for|gap|counts|parameters|takes"
    def clean(line):
        if line.startswith("|"):
            return line
        line=re.sub(r"\b("+words+r")(?=\d)",r"\1 ",line)
        return re.sub(r"\b(\d+)(steps|step|calls|points|labels|iterations|observations|continuations|responses)\b",r"\1 \2",line)
    return "\n".join(clean(line) for line in text.split("\n"))


def refresh_tables(existing, generated, start, end=None):
    """Refresh numeric blocks without overwriting an author's revised prose."""
    old_region=existing.split(start,1)[1]
    new_region=generated.split(start,1)[1]
    if end:
        old_region=old_region.split(end,1)[0]
        new_region=new_region.split(end,1)[0]
    pattern=r"(?m)^\|[^\n]*(?:\n\|[^\n]*)*"
    values=iter(re.findall(pattern,new_region))
    if len(re.findall(pattern,old_region)) != len(re.findall(pattern,new_region)):
        raise ValueError('Generated table count changed; review the evidence before updating.')
    revised=re.sub(pattern,lambda m:next(values),old_region)
    return existing.replace(start+old_region,start+revised,1)


def integrate(refresh_prose=False):
    gp=json.loads((PAPER/"engineering_optimization/gp_audit/summary.json").read_text())
    transfer=json.loads((PAPER/"engineering_optimization/transfer_validation/summary.json").read_text())
    cases=json.loads((PAPER/"engineering_optimization/transfer_validation/case_summaries.json").read_text())["cases"]
    frozen=json.loads((PAPER/"engineering_optimization/gp_audit/frozen_decisions.json").read_text())["states"]
    main=PAPER/"engineering_optimization_manuscript.md";supp=PAPER/"engineering_optimization_supplementary.md"
    text=main.read_text();support=supp.read_text()
    review_main=text;review_supp=support
    names={"gp_ei_shared_init":"EI history","gp_pi_shared_init":"PI history","gp_ucb_shared_init":"UCB history"}
    gp_rows=[[names[r["source_history"]],r["control"].upper(),f"{100*r['action_change_fraction']:.1f}",
              f"{1e6*r['mean_utility']:.6f}",f"{1e6*r['mean_delta_vs_mean']:+.6f}"] for r in gp["groups"]]
    short_gp=[r for r in gp_rows if r[1]!="MEAN"]
    groups=transfer["groups"]
    transfer_rows=[[f"{g['forcedist']:.2f}",f"{g['initial_compliance_median']:.1f}",
                    f"{g['audited_compliance_median']:.1f}",f"{g['portfolio_best_compliance_median']:.1f}",
                    f"{g['portfolio_gap_percent_median']:.3f}",f"{g['exact_best_matches']}/10"] for g in groups]
    section="""### 6.3 Frozen-state intervention on GP acquisition policies

To test the audit beyond the residual controller, thirty archived GP-EI, GP-PI and GP-UCB histories supply ten repeats per source policy. The states immediately before evaluations 59, 101, 151 and 200 are frozen, giving 120 interventions. Every fit uses only earlier labels. Logged ARD Matérn-5/2 parameters are replayed without refitting; all source-action means and standard deviations agree within the prespecified absolute and relative tolerance of 1e-8. Mean, EI, PI and LCB act on a shared 4,096-point Sobol pool augmented by the frozen source action. Here EI has zero improvement margin, PI uses 0.01 times training standard deviation, and LCB uses kappa=2. No intervention response is fed back into a source optimizer.

The 480 policy-state choices contain 261 distinct within-state actions. After choices have been frozen, 120 original action responses are legitimately reused; three further responses come from identical context-point pairs already evaluated in the diagnostic ledger. The audit therefore acquires 138 new FE labels. A separate solver-compatibility check incurs 102 attempts, including an initial 42-call check whose numerical tolerance was found too strict. The final 60 retained comparisons pass the disclosed 1e-6 solver-relative tolerance, with maximum relative difference 4.929e-8. The 1e-8 GP replay tolerance is unchanged. Input hashes and choices were committed before new diagnostic acquisition; see S9 for the archive transfer and verification boundary.

**Table 5. Acquisition-only intervention at frozen GP states. Results are means over ten repeat-level summaries, each averaging four checkpoints. U=max(0,training incumbent minus diagnostic compliance)/training standard deviation. Utility and paired differences are displayed in units of 1e-6; action-change percentages are relative to mean selection.**

"""+table(["Frozen source","Control","Changed (%)","Mean U (1e-6)","Delta U vs mean (1e-6)"],short_gp)+"""
LCB often changes the selected point yet has negative mean immediate-utility differences in all three source-history groups. EI and PI effects depend on the state-generating history; a different choice does not automatically provide immediate gain. The small normalized effects must not be described as a large engineering improvement: training standard deviations range from 7.332e5 to 9.122e8, reflecting high-compliance designs. This is a bounded immediate diagnostic, not evidence for rejecting uncertainty-based exploration. The next experiment explicitly assesses longer horizons under different physical loads.

### 6.4 Longer-horizon policies, load-position transfer and total cost

The separately frozen protocol at commit 7555d58b145a2c44b73bab5ec47d0f643a57dde1 changes the top-edge downward-force position from 0.0 to 0.25 and 0.75. Each condition has ten fresh, paired Sobol initializations of 58 designs. Material, supports, 100-by-50 FE mesh, dimension19 and volume fraction0.35 are unchanged. These are two new physical conditions within one beam family, not independent engineering application domains.

All four transfer policies share an isotropic Matérn-5/2 GP and the same candidate seeds at a given phase and step. The GP is refitted with deterministic bounded L-BFGS-B, at most100 iterations and no restarts; alpha=1e-6, normalized targets, constant bounds[0.05,20], length-scale bounds[0.005,2], and initial length scale0.2. A1,024-point Sobol pool excludes already observed points. EI and PI both use a0.01-scaled improvement margin; LCB retains kappa=2. This controlled implementation differs from the frozen ARD posterior and larger augmented pool in Section6.3, and from the historical GP optimizer. Consequently the new outcomes cannot be attributed solely to moving the force, or interpreted as exact reproductions of Table4.

For each repeat the audited-selection workflow actually pays for58 initial responses, four20-step pilots, and142 further evaluations of the pilot-selected policy. Its total is280 calls. Selection is written before validation; exact pilot-end ties use PI, mean, EI, LCB priority. The selected policy is validated from only the initial archive, with a candidate-seed namespace separate from the pilots. The comparison workflow separately pays for the same58 initial designs and all four142-step continuations, totaling626 calls. Deterministic duplicates between workflows are queried again and counted. Each fixed member of the portfolio represents a200-call alternative, not a free post hoc choice of its best member.

Every condition/policy has zero median improvement at its first pilot action, whereas20-step median improvement is positive. For LCB it is2.514% and3.649% in the two conditions; four of ten repeats in each condition improve after a zero-gain first action. This provides a concrete reason to keep delayed policy assessment separate from immediate screening. It measures diverging policy histories, not the isolated causal effect of a first action under a fixed continuation.

**Table 6. Independent selected-policy validation and complete-portfolio comparison. Compliance is lower-is-better. Each compliance column is a median across ten repeats; the gap is the median of paired percent ratios, not a ratio of medians. Selected-policy validation uses200 algorithm observations but280 paid workflow calls including pilots; the portfolio pays626.**

"""+table(["Force position","Initial compliance","Selected-policy compliance","Portfolio-best compliance","Paired gap (%)","Exact best matches"],transfer_rows)+"""
The selected policy matches the independently executed portfolio-best endpoint in seven of twenty repeats. Its paired median gaps are9.014% and27.217%, and maxima83.067% and289.223%. Pilot-end ties occur in seven and four repeats, so frequent PI selection is partly a consequence of the declared tie rule and must not be reported as strong empirical selection evidence. Compared with fixed PI, the selected workflow wins/ties/loses in1/6/3 and1/8/1 repeats; it makes40% more calls than every fixed200-call policy. Against the explicitly executed full portfolio it makes55.272% fewer calls, accompanied by the disclosed endpoint losses. These counts do not establish universal savings, equivalence, or a performance-preserving deployment gate.

![Cost and performance of the independently executed beam transfer workflows.](engineering_optimization/figures/transfer_cost_performance.svg)

Figure6 reports median initial-incumbent improvement and interquartile ranges together with the actual per-repeat call requirement. Selected-policy performance is the prespecified validation endpoint; pilot outcomes are excluded from its training. Portfolio performance is the best of all four paid members and is not a200-call oracle baseline.

For practical design use, an engineer could retain a better design found in a pilot. A secondary analysis therefore also reports the best among every design paid for by the audited workflow. Its paired median portfolio gaps are9.014% and2.116%, respectively, compared with9.014% and27.217% for the prespecified selected-policy endpoint. Both endpoints are disclosed in S10; the secondary result does not replace the selected-policy test or create a retrospectively chosen promotion threshold. The difference shows why an audit must define the performance object as carefully as its cost boundary.

The retained transfer ledger contains18,120 physical attempts and20,000 full-trajectory algorithm observations across100 budget200 continuations, with shared initial observations counted inside each trajectory but paid only once per workflow. Loss of access to the previous complete local transfer journals required an explicit unchanged-protocol recovery; the earlier18,120 attempts are also counted. Together with the138 immediate diagnostics and102 solver checks, this revision has36,480 new FE attempts. Recovery responses enter each retained history once. Observed GP and FE component times from the retained execution are reported in S10 and are not exclusive resource measurements or demonstrated production wall-time savings. All new comparisons are descriptive and separate from the original prespecified inferential families.

"""
    # Insert or replace only the new engineering evidence block.
    text=re.sub(r"### 6\.3 .*?(?=## 7 )","",text,flags=re.S)
    text=text.replace("## 7 Discussion and Design Guidance",section+"## 7 Discussion and Design Guidance")
    # Preserve the exact older numerical table rows by excluding new blocks.
    old="The engineering controls demonstrate successful and unsuccessful searches, but they do not yet constitute full independent validation of the audit as a transferable tool. Model and training-cap sensitivity within the prototype also do not replace validation across surrogate families. The beam application has one loading and support configuration; its extension to different physical conditions and the measurement of audit overhead remain necessary before broader engineering or savings claims."
    new="The added GP intervention tests the audit on actionable acquisition rules, while the two force-position conditions test finite-horizon policy and selection outcomes within the same beam family. The strongest reusable result is the evidence procedure: identify exact decision classes, pay only for undetermined immediate responses, preserve a label-free intervention boundary, and then disclose both closed-loop endpoints and total cost. The transfer selector illustrates a failure boundary rather than a new competitive optimizer. Its pilot ties, endpoint losses and extra cost relative to fixed policies delimit engineering deployment. Validation on distinct physical model families and competitive warm-start selectors remains outside the evidence."
    assert old in text or new in text
    text=text.replace(old,new)
    text=text.replace("Its transfer across mechanisms and its net engineering-budget benefit remain to be evaluated; they are not conclusions of the present experiments.","The GP intervention and force-position study extend the evidence beyond the residual controller: decisions can differ without immediate gain, later policy value can arise after a zero-gain first action, and cheaper selection can lose final performance. The contribution is a reproducible audit of these distinctions and its query-allocation and cost records, not a guarantee of optimization superiority or net savings.")
    text=text.replace("All source code, numerical outputs, statistical summaries, citations, and AI-assisted text were reviewed and verified by the authors, who revised the manuscript and accept full responsibility for the published content.","The revised sources and additional evidence require final author verification before submission; responsibility for scientific interpretation and the submitted content rests with the authors.")
    text=text.replace("All authors reviewed the results and approved the final version of the manuscript.","Final approval of the revised manuscript by all authors is pending.")
    old_avail="Approximately 13.6 GB of raw experiment outputs and the full execution archives are not committed to that repository."
    text=text.replace(old_avail,"The curated GP intervention ledger and the lossless compact transfer record release support the new results. The supplied GP input files are released in a lossless text bundle with all60 original byte-level checksums. Approximately13.6 GB of historical raw outputs and full execution archives remain outside the repository.")
    text=text.replace("The supplementary document contains full function-level results, LassoBench and 300-dimensional transfer evidence, model and budget sensitivity studies, exclusive resource measurements, recovery accounting, and reproducibility audits.","The supplementary document contains the historical function-level, LassoBench, dimensional, sensitivity and resource evidence, plus the new GP intervention, force-position transfer, per-repeat endpoints, fixed-policy comparisons, horizon diagnostics and complete recovery-aware cost ledger.")
    refs="""
[36] E. Kus, O. Akgun, N. Dang, and I. Miguel, "Frugal algorithm selection," in Proc. CP 2024, LIPIcs, vol.307, pp.38:1-38:16, 2024. doi:10.4230/LIPIcs.CP.2024.38.

[37] A. Kostovska, A. Jankovic, D. Vermetten, J. de Nobel, H. Wang, T. Eftimov, and C. Doerr, "Per-run algorithm selection with warm-starting using trajectory-based features," in Parallel Problem Solving from Nature - PPSN XVII, LNCS, vol.13398, pp.46-60, 2022. doi:10.1007/978-3-031-14714-2_4.

[38] A. J. Booker, J. E. Dennis Jr., P. D. Frank, D. B. Serafini, V. Torczon, and M. W. Trosset, "A rigorous framework for optimization of expensive functions by surrogates," Structural Optimization, vol.17, pp.1-13, 1999. doi:10.1007/BF01197708.
"""
    if not re.search(r"^\[36\] ",text,re.M):text=text.rstrip()+"\n\n"+refs
    text=text.replace("No such net-savings experiment is reported here.","Section 6.4 reports a complete paid-workflow comparison with endpoint losses; it does not establish performance-preserving net savings.")
    text=text.replace("These outcomes show that the audit can distinguish actionable Bayesian, evolutionary-surrogate, and trust-region management from mechanisms whose plausible uncertainty signal does not translate into valuable evaluations.","These outcomes provide optimizer context; the new frozen-state intervention supplies mechanism-level evidence for the GP acquisition rules. A full decision-level audit of DRSO and TuRBO-1 is not claimed.")
    text=text.replace("**Shu-Chuan Chu1,*, Ya-Yu Zhang1, Zhenyu Meng2 and Jia Zhao3**", "**Shu-Chuan Chu**$^{1,*}$, **Ya-Yu Zhang**$^1$, **Zhenyu Meng**$^2$ and **Jia Zhao**$^3$")
    main.write_text(readable_prose(text) if refresh_prose else refresh_tables(review_main,text,"### 6.3 ","## 7 "))
    s9="""\n\n# S9 Frozen GP intervention and immediate diagnostic accounting

This additional study is separately frozen, descriptive, and not part of the original Holm families. Input hashes and120 decisions were committed at f1c9bbdebc35071bd935d0b11c92857f5e07201e before new intervention labels. The initially transmitted binary ZIP was incomplete, despite an intact local author-supplied archive. Local scientific input hashes and frozen choices did not change. The public input release now uses a byte-preserving text bundle at commit 71e074945262e1dbfc223726c7216e5415385ddc, replacing the incomplete repository binary. Its restoration checks every original file hash, all segment hashes and the decoded payload hash before writing any file. It preserves all60 original file bytes, including line endings; it does not claim to reconstruct the original ZIP container bytes. The original supplied archive remains identified by SHA256 c59079aaf34f560ee2f3e93a55bd60e13b2fa4c53097285842580df4d3b8098b. Public distribution integrity and scientific execution integrity are separate checks.

Thirty source histories contain6,000 budgeted algorithm observations and580 distinct common initial labels across ten repeats. Frozen states stop at PRE(t), exclude LABEL(t), and contain only observations before59,101,151 or200. The same recorded ARD Matérn-5/2 posterior scores mean, EI, PI and LCB on4,096 scrambled Sobol points plus the original action. EI uses zero margin, PI uses0.01 times the training standard deviation, and LCB uses kappa2. Logged hyperparameters are not refitted. All120 source-action mean/standard-deviation comparisons satisfy rtol=atol=1e-8. Decisions and candidate records are hashed before source action labels are looked up. No new diagnostic label enters a source optimizer history.

**Table S26. All controls and source-history groups. Four checkpoint estimates are averaged within each repeat before averaging ten repeats. U and DeltaU are in units of1e-6.**

"""+table(["Source history","Control","Changed (%)","Mean U (1e-6)","DeltaU vs mean (1e-6)"],gp_rows)+"""
The training scale ranges from"""+f"{min(s['scale'] for s in frozen):.6g} to {max(s['scale'] for s in frozen):.6g}"+""". This can make normalized gains small even when raw compliance changes. The metric is retained as frozen; no post hoc replacement or new p-value is used. These comparisons neither test delayed exploration nor authorize promotion.

The480 control-state choices reduce to261 distinct within-state actions. Source-action reuse accounts for120 responses; exact diagnostic reuse across states accounts for3;138 are new FE calls. New diagnostic FE time is4.437432s and GP state preparation time13.435883s. The initial solver compatibility check made42 calls before detecting a4.929e-8 relative discrepancy at a large-compliance point. That discrepancy was numerical, not a failed FE response. The complete retained60-call check uses the disclosed1e-6 relative tolerance and passes every comparison. The original prediction replay tolerance remains1e-8. The first42 outputs and timings were not retained but their attempts are included. The retained solver check takes2.327726s. Total additional attempts for this GP revision are240. These observed times do not establish exclusive wall-time savings.

"""
    s10="""# S10 Independent load-position transfer, horizon effects and paid workflows

The protocol and executable implementation were committed at7555d58b145a2c44b73bab5ec47d0f643a57dde1 before acquiring new transfer labels. Conditions forcedist0.25 and0.75 each have ten independently seeded58-point Sobol initializations. Fixed seed namespaces distinguish initialization, pilots and validation. The same case/step candidate namespace is shared across policies inside a phase. All policies use one shared specification; tie ordering, fit limits and budgets were not tuned using outcomes. This is within-family physical-condition transfer, not cross-domain validation.

**Table S27. Differences between the two additional GP experiments. The original beam wrapper, material, supports, volume0.35 and dimension19 are retained.**

"""+table(["Setting","Frozen intervention (S9)","Independent transfer (S10)"],[
      ["Source state","Archived EI/PI/UCB histories","Fresh initialization in each force condition"],
      ["Kernel","Logged ARD Matérn-5/2","Isotropic Matérn-5/2"],
      ["Hyperparameters","Frozen, optimizer disabled","L-BFGS-B, max100 iterations, no restarts"],
      ["Candidate pool","4096 Sobol + original action","1024 Sobol; observed points excluded"],
      ["EI margin","0","0.01 times training standard deviation"],
      ["PI margin / LCB kappa","0.01 scaled / 2","0.01 scaled / 2"],
      ["GP alpha / normalization","1e-6 / normalized targets","1e-6 / normalized targets"],
      ["Physical force position","0.0","0.25 and 0.75"]])+"""
The transfer constant bounds are[0.05,20] and length-scale bounds[0.005,2], with initial length scale0.2. Fit convergence warnings are recorded and do not trigger restarts. Beams2D caches force-dependent matrices; each case creates a fresh problem object configured once with its actual force position. This prevents cross-condition state reuse. The environment pins NumPy2.2.6, SciPy1.15.3, scikit-learn1.7.2, EngiBench0.2.0 and cvxopt1.3.2. These settings define a separate controlled study and do not rerun the historical ARD/continuous-refinement GP optimizer.

## S10.1 Paid selection and independent validation

Each audited workflow pays58 initial labels,4x20 pilot labels and142 selected-policy validation labels:280. Each complete portfolio independently pays58 initial labels and4x142 continuation labels:626. A fixed single policy needs200. The pilot winner is the lowest final pilot compliance, with exact ties broken in PI, mean, EI, LCB order. Selection is persisted after138 calls and before any canonical validation label. Canonical histories start again from the initial58 labels and never include pilot responses. Validation candidates use a different namespace; no warm-starting selector is claimed. The selected canonical trajectory and its separately paid portfolio counterpart agree exactly in every repeat. All duplicate designs across workflows are physically evaluated and counted, rather than credited as free labels.

**Table S28. All twenty paired endpoints. The selected-policy column is the prespecified independent canonical endpoint. All-paid best is a secondary descriptive endpoint including every pilot design; it does not replace the validation criterion. Gap is100x(selected/portfolio-best-1).**

"""+table(["Force","Rep","Selected","Initial","Selected-policy","Portfolio-best","Gap (%)","All-paid best"],[
       [f"{s['forcedist']:.2f}",s['repeat'],s['selected'].upper(),f"{s['initial_best']:.3f}",f"{s['audited']['best']:.3f}",
        f"{min(v['best'] for v in s['portfolio'].values()):.3f}",f"{100*(s['audited']['best']/min(v['best'] for v in s['portfolio'].values())-1):.3f}",
        f"{min(s['audited']['best'],*(v['best'] for v in s['pilots'].values())):.3f}"] for s in cases])+"""
The primary median paired gaps are9.013698% and27.217435%. Exact portfolio-best matches are4/10 and3/10. The selected counts are PI6, EI2, mean2 at force0.25, and PI8, LCB1, mean1 at force0.75. Exact pilot-end ties occur in7 and4 repeats; counts should not be interpreted independently of the tie rule. The secondary all-paid gaps have medians9.013698% and2.115716%. The discrepancy between primary and secondary endpoints is disclosed because the practical availability of a pilot design differs from evidence that the chosen policy transfers well.

**Table S29. Each200-call fixed policy compared with the280-call selected workflow. Median effects are paired100x(selected/fixed-1); negative favors selection. Wins/ties/losses are descriptive, not tests of superiority or equivalence.**

"""+table(["Force","Fixed policy","Median fixed compliance","Paired effect (%)","Selection wins/ties/losses"],[
      [f"{r['forcedist']:.2f}",r['policy'].upper(),f"{r['fixed_compliance_median']:.3f}",f"{r['audit_minus_fixed_ratio_percent_median']:+.3f}",
       f"{r['audit_wins']}/{r['ties']}/{r['audit_losses']}"] for r in transfer["fixed_policy_comparisons"]])+"""
Selecting the best fixed policy retrospectively from these validation outcomes would be a separate selection procedure. No such200-call oracle advantage is attributed to the audit or its comparator.

## S10.2 Horizon separation

**Table S30. Pilot improvement from the common initial incumbent. First and20-step columns are medians of per-repeat percentages. The final count concerns the same pilot trajectory.**

"""+table(["Force","Policy","First step (%)","20 steps (%)","Zero first, positive20 /10"],[
      [f"{r['forcedist']:.2f}",r['policy'].upper(),f"{r['first_improvement_percent_median']:.3f}",f"{r['20_step_improvement_percent_median']:.3f}",r['zero_first_then_positive_20']]
      for r in transfer["pilot_horizons"]])+"""
![Pilot improvement across twenty steps under the two force positions.](engineering_optimization/figures/transfer_pilot_horizons.svg)

Figure S14 plots condition-specific median incumbent improvement over the pilot horizon. It illustrates why a first action without gain is not a sufficient rejection rule. These are whole-policy trajectories with diverging histories; the figure does not estimate a first-action treatment effect with an identical continuation. Pilot-to-canonical selection transfer is a further question because the canonical candidate stream is independent.

## S10.3 Costs, recovery and evidence integrity

**Table S31. Complete additional FE-attempt boundary for this revision. Historical experiments before the revision are not included.**

"""+table(["Component","Physical attempts","Use in reported endpoints"],[
      ["New frozen GP intervention","138","Separate diagnostics only"],
      ["Solver compatibility verification","102","Never optimizer training"],
      ["Earlier complete transfer execution","18120","Prior checked endpoints; raw journals unavailable in current workspace"],
      ["Retained unchanged-protocol transfer recovery","18120","Retained canonical and pilot records, labels used once"],
      ["Total including recovery","36480","No repeated attempt is hidden in a budget200 trajectory"]])+"""
The prior transfer journals became unavailable in the working environment before their raw release. An explicit recovery record at62560a245a8b804dcff3ce00aa45aae0af9f3884 preserves the unchanged scientific configuration and caps additional recovery calls at18,120. All twenty previously recorded selected-policy and portfolio-best endpoints are reproduced. Recovery contributes additional physical cost, not additional independent repeats or a changed inferential family. The initial zero-call bootstrap failure from the earlier launch adds no FE cost. The retained20 cases comprise2,320 physical initialization calls,1,600 pilot calls and14,200 canonical postinitial calls. Their100 full-budget trajectories contain20,000 algorithm observations because initialization is shared among forks inside each workflow.

**Table S32. Retained observed component times summed across ten repeats per condition, in seconds. Four workers run concurrently; sums are not exclusive elapsed-time benchmarks.**

"""+table(["Force","Audited FE","Portfolio FE","Audited GP/selection","Portfolio GP/selection"],[
      [f"{g['forcedist']:.2f}",f"{g['fe_seconds']['audited']:.3f}",f"{g['fe_seconds']['portfolio']:.3f}",f"{g['gp_seconds']['audited']:.3f}",f"{g['gp_seconds']['portfolio']:.3f}"] for g in groups])+"""
The analyzer validates complete PRE/LABEL pairing,906 physical calls per case,280/626 workflow counts,20 pilot steps and142 canonical steps per policy, selection before validation, correct seed namespaces, identical initial history hashes, exclusion of pilot labels from every canonical history, exact selected/portfolio trajectory replay, and every endpoint and component-time sum. It makes zero new FE calls. The compact release regenerates deterministic Sobol points and reconstructs each retained source JSONL byte for byte, checked against its SHA256; no objective call is needed to restore or analyze the records. Original full journals remain the source of timing and information-boundary checks.

There are no added p-values, confidence guarantees, retrospective deployment tolerances, claims of cross-domain transfer, or demonstrated production wall-time savings. The two loads strengthen within-family applicability. They do not establish optimizer superiority, a competitive selection advance over warm-starting, or validation of unrestricted5000-variable topology optimization.
"""
    support=re.sub(r"\n+# S9 .*","",support,flags=re.S).rstrip()+s9+s10+"\n"
    support=support.replace("During peer review, supporting data and code are available from the corresponding author upon reasonable request; upon acceptance, the publicly releasable portions will be deposited in the public GitHub repository identified in Section S0, together with a fixed release tag and version identifier.","The repository contains sources and curated revision evidence. The byte-preserving GP source bundle, frozen intervention records and lossless compact transfer release support the added results. Larger historical archives remain available from the corresponding author upon reasonable request. Frozen source revisions, data-release commits and file checksums identify the evidence.")
    support=re.sub(r"^6\. \*\*Additional mechanism and engineering evidence:\*\*[^\n]*\n", "", support, flags=re.M)
    support=support.replace("5. **Information order and accounting:** S7.3-S8.3 and Table S25 preserve finite-element replay, source hashes, recovery ledgers, and matched-initialization evidence.","5. **Information order and accounting:** S7.3-S8.3 and Table S25 preserve finite-element replay, source hashes, recovery ledgers, and matched-initialization evidence.\n6. **Additional mechanism and engineering evidence:** S9-S10, Tables S26-S32 and Figure S14 contain the frozen GP intervention, delayed policy outcomes, force-position transfer, fixed-policy comparisons and full revision cost boundary.")
    supp.write_text(readable_prose(support) if refresh_prose else refresh_tables(review_supp,support,"# S9 "))
    return {"new_main_sections":["6.3","6.4"],"new_supplement_sections":["S9","S10"],"new_objective_calls":0}


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--refresh-prose',action='store_true',
                        help='Explicitly replace the generated working prose; default updates tables only.')
    print(json.dumps(integrate(parser.parse_args().refresh_prose)))
