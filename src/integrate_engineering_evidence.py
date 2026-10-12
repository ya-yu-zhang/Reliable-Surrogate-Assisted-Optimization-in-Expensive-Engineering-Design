"""Measured-table integration and narrowly scoped factual edits of existing drafts.

No new scientific argument sections or author approval claims are generated.
Earlier source bytes remain in the immutable baseline Git commit and local backup.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,re,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PAPER=ROOT/'paper/engineering_optimization'
DEST=PAPER/'integrated_evidence'
BASELINE_COMMIT='062c1b62a773f80cc4383d51a4d6655e9cc3f083'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads((ROOT/p).read_text())
def tidy(text):
    text=re.sub(r'\b(All|Original|Budget|budget|within|in|max|shared|plus|at|across|for|the|of|smooth|unrestricted|primary|illustrative|including|has|and|is|followup|alpha|length|horizon|margin|threshold|both|native|transferred|means|authored|dependent|account)(?=\d)',r'\1 ',text)
    text=re.sub(r'\b(depth|adaptive|states|cases|seeds|labels|requests|pool)(?=\d)',r'\1 ',text)
    return re.sub(r'([;:])(?=\d)',r'\1 ',text)
def escaped(value):
    # Data-only strings: escaping does not generate article argument.
    text=str(value)
    for a,b in [('&',r'\&'),('%',r'\%'),('_',r'\_')]:text=text.replace(a,b)
    return text
def table(caption,label,headers,rows,widths):
    cols=''.join(r'>{\raggedright\arraybackslash}p{(\columnwidth - '+str(2*(len(headers)-1))+r'\tabcolsep) * \real{'+str(w)+'}}' for w in widths)
    head=' & '.join(escaped(v) for v in headers)+r' \\'
    body='\n'.join(' & '.join(escaped(v) for v in row)+r' \\' for row in rows)
    return ('\\FloatBarrier\\begingroup\\fontsize{8.5}{10.5}\\selectfont\\setlength\\tabcolsep{3pt}\n'
       '\\begin{longtable}{@{}'+cols+'@{}}\n\\caption{'+caption+'}\\label{'+label+'}\\tabularnewline\n'
       '\\toprule\n'+head+'\n\\midrule\n\\endfirsthead\n\\toprule\n'+head+'\n\\midrule\n\\endhead\n'
       '\\bottomrule\n\\endlastfoot\n'+body+'\n\\end{longtable}\n\\endgroup\n\n')
def generate():
    DEST.mkdir(parents=True,exist_ok=True)
    common=read('paper/engineering_optimization/common_continuation/analysis.json')
    denom=read('paper/engineering_optimization/common_continuation/denominator_analysis.json')
    budget=read('paper/engineering_optimization/budget_audit/analysis.json')
    thermal=read('paper/engineering_optimization/thermal_analysis.json')
    mesh=read('paper/engineering_optimization/paired_mesh/analysis.json')
    assert common['states']==30 and budget['seed_blocks']==10 and thermal['independent_cases']==20
    assert denom['distinct_nonbaseline_action_contrasts']==46 and mesh['selected_contrasts']==14
    costs={'earlier_gp_transfer':36480,'common_continuation':282,'thermal':thermal['cumulative_thermal_attempts'],
           'independent_budget':budget['new_physics_attempts'],'paired_mesh':mesh['total_new_physics_attempts']}
    total=sum(costs.values());assert total==55305
    main_rows=[
      ['Archived common continuation','30 states within10 shared seeds','90 named /46 distinct contrasts;7 distinct changes in4 states',282],
      ['Independent budget audit','10 new seed blocks;30 dependent states','Budget18: no allocation advantage; budget12: depth17/25, adaptive9/25',budget['new_physics_attempts']],
      ['Small thermal verification','20 cases;2 source positions','2 gate/simple disagreements:1 tie and1 loss',thermal['cumulative_thermal_attempts']],
      ['Selected paired-grid check','14 contrasts;9 existing states;104 designs',f"Fixed h5 class stable in{mesh['fixed_h5_all_contexts_stable_cases']}/14, including{mesh['distinct_fixed_h5_pairs_stable']}/{mesh['distinct_fixed_h5_endpoint_pairs']} differing endpoint pairs",mesh['total_new_physics_attempts']]]
    caption=('Additional released measured records. States, seed blocks, thermal cases and selected design pairs are separate reporting units. '
       'Paid solver attempts include recovery and verification; they are not pooled optimization-budget observations. '
       'The paired-grid record is fixed-design reevaluation, not fine-grid GP optimization. '
       'Tables were assembled using OpenAI Codex (GPT-6)-assisted Python code and remain subject to author verification.')
    (DEST/'main_records.tex').write_text(r'\Needspace{18\baselineskip}'+'\n'+tidy(table(caption,'tab:released_records',['Record','Unit','Measured result','Paid attempts'],main_rows,[.20,.23,.44,.13])))
    supp=''
    settings=[
      ['Original GP audit','Logged ARD Matérn-5/2; snapshot does not reoptimize','4096 plus source action','120 states; immediate alternatives'],
      ['Common continuation','Same source ARD theta; fixed during branch updates','First: original pool; followup1024','30 archived states; h0/1/3/5; mean continuation'],
      ['Beam transfer','Isotropic Matérn-5/2; bounded L-BFGS-B, max100 iterations per fit','1024','20 fresh cases; full-policy pilots/continuations'],
      ['Independent budget','ARD theta fitted once at shared50-label warm state, max30 iterations; then fixed','1024;8 calibration probes','10 new seeds;100-label states; mean/EI followup5'],
      ['Thermal verification','Isotropic Matérn-5/2; fixed length0.4; no hyperparameter fitting','256','12 variables;24 initial labels;96 calls/workflow']]
    supp+=table('Settings of separate evidence releases. These implementations differ and are not pooled as exact replications. All new GP records use alpha1e-6 and normalized targets.','tab:extension_settings',['Record','GP fitting','Candidate pool','Target'],settings,[.19,.39,.17,.25])
    denomrows=[['Original named contrasts',denom['original_named_contrasts']],['Baseline-action aliases',denom['structural_alias_contrasts']],['Different-action named contrasts',denom['different_action_named_contrasts']],['Distinct nonbaseline-action contrasts',denom['distinct_nonbaseline_action_contrasts']],['Named h0/h5 changes',denom['named_classification_changes']],['Distinct-action changes',denom['distinct_action_classification_changes']],['Distinct delayed non-ties',denom['distinct_action_delayed_non_ties']],['States containing changes',len(denom['changed_states'])]]
    supp+=table('Archived common-continuation denominators. Original90-contrast reporting is retained; action equivalence supplies a supplementary denominator, not extra independent samples.','tab:extension_denominators',['Reporting object','Count'],denomrows,[.77,.23])
    comparison=[]
    for source in ['gp_ei_shared_init','gp_pi_shared_init','gp_ucb_shared_init']:
        for control in ['ei','pi','lcb']:
            rr=[r for r in common['comparisons'] if r['method']==source and r['control']==control]
            a=next(r for r in rr if r['horizon']==0);b=next(r for r in rr if r['horizon']==5)
            comparison.append([source.replace('gp_','').replace('_shared_init','').upper(),control.upper(),f"{a['better']}/{a['tie']}/{a['worse']}",f"{b['better']}/{b['tie']}/{b['worse']}",f"{b['median_paired_advantage_percent']:.3f}"])
    supp+=table('Archived first-action contrasts with common posterior-mean continuation. Better/tie/worse counts use the original named-control denominator; each row has10 dependent-source states and margin1e-6. Positive advantage favours the named control.','tab:extension_common',['Source history','Control','h0 B/T/W','h5 B/T/W','Median h5 (%)'],comparison,[.21,.14,.21,.21,.23])
    budgetrows=[]
    for r in budget['sensitivity']:
        if r['margin']==.001 and ((r['budget']==18 and r['method'] in ['calibration','immediate','fixed_depth','adaptive']) or (r['budget']==12 and r['method'] in ['fixed_depth','adaptive'])):
            budgetrows.append([r['continuation'].upper(),r['budget'],r['method'].replace('_',' '),f"{r['classified']}/{r['contrasts']}",r['classification_error'],r['total_audit_requests'],f"{r['mean_selection_regret_percent']:.4f}"])
    supp+=table('Independent budget replay: horizon5, margin0.001,25 distinct nonbaseline-action contrasts per continuation. Requests are conservatively charged response lookups across30 states. Calibration is a constructed root-EI proxy gate, not a published diagnostic algorithm. Completed-horizon zero errors come from measuring the target; they are not predictive guarantees.','tab:extension_budget',['Followup','Budget','Rule','Classified','Errors','Requests','Selection regret (%)'],budgetrows,[.12,.10,.20,.13,.10,.13,.22])
    thermalrows=[[r['condition'].replace('_',' '),r['comparator'].replace('_',' '),f"{r['median_paired_difference_percent']:.3f}",f"{r['wins']}/{r['ties']}/{r['losses']}"] for r in thermal['comparisons']]
    supp+=table('Small thermal model: audit gate versus simple selector and fixed policies at96 calls per workflow. Paired difference is100(audit/comparator-1); negative favours audit. This authored24x24 finite-volume verification is not an industrial expense benchmark.','tab:extension_thermal',['Source','Comparator','Median difference (%)','Win/tie/loss'],thermalrows,[.24,.27,.25,.24])
    meshrows=[[r['case'],r['group'].replace('_',' '),r['original_h5_class'],r['native_fine_h5_class'],r['transferred_fine_h5_class'],'different' if r['distinct_fixed_h5_endpoint_designs'] else 'same'] for r in mesh['case_summaries']]
    supp+=table('Selected fixed endpoint-design checks. All14 h5 classes persist in six mesh/mapping contexts;8 pairs have different endpoint designs and6 are same-design ties. Selection was frozen from known contrasts and is not a new independent optimization sample. Fine means200x100.','tab:extension_mesh',['Case','Selection group','Original class','Native fine','Transferred fine','Endpoints'],meshrows,[.09,.27,.16,.16,.18,.14])
    numerical=[['Original strict source-response gate','Failed on fourth paid attempt; threshold1e-8 unchanged'],
               ['Coarse source agreement flags',f"{mesh['coarse_source_flagged_unique_points']}/104 unique points"],
               ['Flagged coarse relative discrepancy',f"{mesh['coarse_source_flags'][0]['relative_difference']:.8g}"],
               ['Maximum equilibrium relative residual',f"{mesh['max_equilibrium_relative_residual']:.8g}"],
               ['Maximum energy/work relative gap',f"{mesh['max_energy_work_gap']:.8g}"],
               ['Maximum native200x100 objective difference',f"{100*mesh['max_relative_objective_changes']['200x100/native_parameter_resampling']:.4f}%"],
               ['Maximum transferred200x100 objective difference',f"{100*mesh['max_relative_objective_changes']['200x100/conservative_base_field_transfer']:.4f}%"],
               ['Fine-grid optimization / convergence certification','Neither performed nor established']]
    supp+=r'\Needspace{16\baselineskip}'+'\n'+table('Numerical flags and absolute objective variation for104 selected design points. Recovery records retain the original failed gate. Objective differences are not known solver errors; fixed-design ranking stability does not imply physical convergence.','tab:extension_numerical_flags',['Check','Measured record'],numerical,[.56,.44])
    costrows=[['Earlier GP/transfer stages',costs['earlier_gp_transfer'],'Includes both18120-call transfer executions'],['Archived common continuation',282,'273 original attempts plus9 record recovery attempts'],['Thermal verification',costs['thermal'],'7200 retained +22 checks +1080 recovery +7586 earlier unavailable'],['Independent budget verification',costs['independent_budget'],'All initialization/source/probe/oracle/mesh calls'],['Selected paired-grid verification',costs['paired_mesh'],'4 stopped-run attempts +517 recovery-execution attempts'],['Full revision cumulative paid attempts',total,'Earlier historical experiments outside this revision excluded']]
    supp+=table('Updated cumulative paid physics-attempt ledger. FE and thermal solves are both counted; recovery adds cost, not independent samples. Source/calibration GP times in the budget release were not separately recorded, so this is not an end-to-end speedup measurement.','tab:extension_cost',['Stage','Paid attempts','Boundary'],costrows,[.37,.16,.47])
    (DEST/'supp_records.tex').write_text(tidy(supp))
    hashes={p:sha((ROOT/p).read_bytes()) for p in ['paper/engineering_optimization/common_continuation/analysis.json','paper/engineering_optimization/common_continuation/denominator_analysis.json','paper/engineering_optimization/budget_audit/analysis.json','paper/engineering_optimization/thermal_analysis.json','paper/engineering_optimization/paired_mesh/analysis.json']}
    (DEST/'table_inputs.json').write_text(json.dumps({'source_hashes':hashes,'cumulative_physics_attempts':total,'main_rows':main_rows,'original_numeric_rows_retained':True,'new_argument_sections_drafted':False,'author_confirmation':'pending'},indent=2)+'\n')
    return mesh,total

def factual_edits(mesh,total):
    backup=ROOT.parent/'eo_integration_before';backup.mkdir(exist_ok=True)
    audit={};marker='% Factual evidence integration v1; scientific author review pending.'
    for name in ['EO_manuscript.tex','EO_supplementary.tex']:
        p=PAPER/name;old=p.read_text()
        if marker in old:continue
        shutil.copyfile(p,backup/name);new=old;changes=[]
        def replace(before,after):
            nonlocal new
            after=tidy(after)
            if new.count(before)!=1:raise ValueError(f'Unexpected source anchor {name}: {before[:80]} count{new.count(before)}')
            new=new.replace(before,after);changes.append({'before':before,'after':after})
        if name=='EO_manuscript.tex':
            replace('independent optimization and complete cost accounting.','independent optimization and physical-call cost accounting.')
            replace('without establishing universal selector superiority or performance-preserving savings.\n\\end{abstract}',
                    'without establishing universal selector superiority or performance-preserving savings. An archived common-continuation record has seven distinct immediate-to-later classification changes across four states. Independent budget validation on ten new seed blocks finds no adaptive-allocation advantage. Selected fixed-design classifications remain stable across three grids and two density mappings.\n\\end{abstract}')
            replace('The new evidence remains separate from the original statistical families.',
                    'The new evidence remains separate from the original statistical families. Table~\\ref{tab:released_records} also reports the archived common-continuation extension, ten new budget-validation seed blocks, twenty small thermal cases and selected paired-grid checks; these reporting units are not pooled as independent samples.')
            replace('Together with the138 immediate diagnostics and 102 solver checks, this revision has 36,480 new FE attempts.',
                    'Together with the138 immediate diagnostics and102 solver checks, the earlier GP/transfer stages account for36,480 new FE attempts. The cumulative ledger including later released checks is'+f'{total:,}'+ ' paid physics attempts; its stage-wise boundary is reported in the supplement.')
            anchor='\\hypertarget{discussion-and-design-guidance}{%'
            replace(anchor,'\\input{integrated_evidence/main_records.tex}\n\n'+anchor)
            replace('Validation on distinct physical model families and competitive warm-start selectors remains outside the evidence.',
                    'The added thermal record uses a small authored heat-conduction model; industrial cross-domain validation and competitive warm-start selectors remain outside the evidence.')
            replace('The beam study uses a smooth 19-dimensional design family, not unrestricted 5,000-variable topology optimization.',
                    'The beam study uses a smooth19-dimensional design family, not unrestricted5,000-variable topology optimization. The independent budget record is offline sequential replay; its primary18-request budget completes all distinct action classes, and source/calibration GP times were not separately recorded. Three-grid checks reevaluate recorded designs without refitting fine-grid GPs or refining every training point. Absolute compliance remains mesh/mapping-sensitive and the strict original coarse-response check flags one high-compliance point; neither mesh convergence nor physical accuracy of the illustrative0.1\\% margin is certified.')
            replace('The contribution is a reproducible audit of these distinctions and its query-allocation and cost records, not a guarantee of optimization superiority or net savings.',
                    'The contribution is a reproducible audit of these distinctions and its query-allocation and cost records, not a guarantee of optimization superiority or net savings. The independently collected budget record shows no adaptive-allocation advantage, and the two thermal gate/simple disagreements end in a tie and a loss.')
            replace('The authors confirm contribution to the paper as follows:','The following contribution assignment is proposed for author confirmation:')
            replace('This statement records the working draft\'s status and must be completed by the authors before submission; it does not certify author approval or policy compliance.',
                    'For the present evidence integration, Codex-assisted Python code assembled measured-data tables and performed numerical and reproducibility checks. This statement records the working draft\'s status and must be completed by the authors before submission; it does not certify author approval or policy compliance.')
            replace('The curated GP intervention ledger and the lossless compact transfer record release support the new results.',
                    'The curated GP intervention, transfer, thermal, common-continuation, independent budget and paired-grid records support the additional results. Their lossless release manifests, source hashes and analysis scripts identify the exact records; selected grid checks are numerical reevaluation rather than new optimizer runs.')
        else:
            replace('Complete additional FE-attempt boundary for this revision. Historical experiments before the revision are not included.',
                    'Additional FE-attempt boundary of the earlier GP/transfer stages. Later released checks are accounted for separately in Table~\\ref{tab:extension_cost}; historical experiments before this revision are not included.')
            replace('\\Needspace{14\\baselineskip}\n\\bibliographystyle{tfcad}',
                    '\\input{integrated_evidence/supp_records.tex}\n\n\\Needspace{14\\baselineskip}\n\\bibliographystyle{tfcad}')
        new=marker+'\n'+new
        # Inline historical tabular data must remain exactly the same; all new
        # numerical records live in separate generated input files.
        def numeric_rows(text):
            blocks=re.findall(r'\\begin\{longtable\}.*?\\end\{longtable\}',text,re.S)
            return [line for b in blocks for line in b.splitlines() if '&' in line and re.search(r'\d',line) and line.strip().endswith(r'\\')]
        assert numeric_rows(old)==numeric_rows(new)
        p.write_text(new);audit[name]={'baseline_commit':BASELINE_COMMIT,'before_sha256':sha(old.encode()),'after_sha256':sha(new.encode()),'historical_numeric_rows_unchanged':True,'changes':changes}
    abstract=(PAPER/'EO_manuscript.tex').read_text().split('\\begin{abstract}',1)[1].split('\\end{abstract}',1)[0]
    count=len(re.findall(r'\S+',abstract));assert count<=250
    if audit:(DEST/'factual_edit_audit.json').write_text(json.dumps({'files':audit,'abstract_words_whitespace':count,'new_scientific_argument_sections':False,'author_review_pending':True},indent=2)+'\n')
    print(json.dumps({'edited_files':list(audit),'abstract_words':count,'historical_numeric_rows_unchanged':True,'cumulative_physics_attempts':total}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args();mesh,total=generate()
    if a.apply:factual_edits(mesh,total)
