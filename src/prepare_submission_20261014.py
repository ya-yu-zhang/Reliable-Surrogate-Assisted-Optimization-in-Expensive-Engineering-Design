"""Prepare an evidence-preserving journal packet; never execute engineering solvers."""
from __future__ import annotations
from collections import Counter
import argparse, hashlib, json, re, shutil
from pathlib import Path

BASELINE='58f539c2d0738b20c7d0d4889fe8d808a03a3019'
TITLE='Certified Action Sets and Decision Limits in Surrogate-Assisted Engineering Optimization'
DATA_STATEMENT=r'''The source repository is private: \url{https://github.com/ya-yu-zhang/Reliable-Surrogate-Assisted-Optimization-in-Expensive-Engineering-Design}. A repository URL alone does not provide reviewer access. The separately prepared data-and-code packet contains the immutable GP execution archive, the exact selected baseline and source snapshots needed for its reconstruction, coefficient bands, original and envelope exclusion certificates, recorded timings, and verification code. These materials support zero-solver reproduction of the current action-set contribution. The 114 kernel systems and 228 branch-domain outputs have been checked against the archived bytes; retiming can change machine-dependent times and does not acquire independent optimization evidence.

The supporting paired-grid tables and historical release audits are preserved, but their complete raw reconstruction is currently unavailable. As of 14 October 2026, 22 of the 25 files listed in the paired-grid provenance audit have been recovered with matching SHA-256 hashes. The final recovery journal (\path{events.jsonl}), response collection (\path{responses.json}) and status (\path{run_status.json}) under \path{results/engineering_optimization_paired_mesh_recovery_v1/} have not been recovered. The earlier full review ZIP is not currently accessible. The retained analysis outputs cannot substitute for those raw records, and the historical release-validation result is not a claim of a complete current replay. Consequently, the paired-grid observations remain supporting historical results, with an explicit raw-evidence limitation; they do not establish mesh convergence or physical accuracy of the decision margin.

The authors report preserving the historical raw-output archive of approximately 13.6 GB locally. That archive has not been fully inspected in the present preparation and is not included in the scoped reviewer packet. Availability of all historical records is therefore not guaranteed by this statement. Reviewer materials must be supplied through the journal's accepted attachment or access route before evaluation. No new physics, witness retry, replacement, or independent optimization sample was used to prepare these materials. Third-party implementations and publisher templates retain their own terms; private source access does not by itself grant an open-source license.'''

ARCHIVAL_NOTE=r'''\section{Current evidence availability and historical paired-grid limitation}\label{supp:current_availability}

The current contribution can be checked from the supplied GP execution archive and the new coefficient-band certificates without a finite-element solver. The execution archive retains both frozen witnesses and their original attempt accounting, all construction records and its file manifest. The separate envelope verifier reconstructs all 114 binary kernel systems, compares all 228 branch-domain sets and checks 232,564 new exclusions. The existing test record reports 31 scoped unit tests. The computational comparison is post hoc development, and its three repetitions and two response domains do not add independent optimization samples.

The supporting paired-grid archive has a different preservation status. Its repository provenance audit lists 25 exact JSON/JSONL files. Twenty-two files are currently recovered and match those recorded hashes. Three completed-recovery files are not recovered:
\begin{itemize}
\item \path{events.jsonl}: 566,891 bytes; SHA-256:\par
{\footnotesize\path{5c526b95919b6db0cd145bd78dc906f93457e10ac6bf8b0b99de7d45ec88c222}}.
\item \path{responses.json}: 341,628 bytes; SHA-256:\par
{\footnotesize\path{d8076558c9abf1ba6cd279320ed7fa2618bbe38617f12a2e0b0ad563d393e9e2}}.
\item \path{run_status.json}: 389 bytes; SHA-256:\par
{\footnotesize\path{beeb6072b9ea737617686064a64caf8e934f20cc8d4e45145644f4b3b305e65d}}.
\end{itemize}
These files belong to \path{results/engineering_optimization_paired_mesh_recovery_v1/}. No copy is present in the checked baseline tree or scoped attachments, and the user reports the selected directory absent from the local backup checked. This is not proof that every other saved archive lacks a copy. The missing complete base85 archive had one manifest and six segments; its old full review-package manifest records their hashes.

The preserved \path{analysis.json}, \path{paired_contrasts.csv} and \path{case_summary.csv} match the historical full review-package member hashes. They permit review of the reported contrasts and aggregate summaries, but do not permit a complete new validation of solver residuals, ordered request/label events, density replays or cache provenance. Earlier sections describe the completed historical study, not a newly performed full raw-record replay. The original source-agreement failure, 521 paid attempts and missing original response value/duration remain disclosed. Recovered final records would contain the historical remeasurement, not restore that absent original value or timing.

The missing files are not reconstructed from summary tables and no solver is rerun to fill the gap. The archive limitation is kept separate from the complete current GP action-set verification. It narrows the reproducibility claim for supporting paired-grid observations without changing their recorded values or promoting them to physical-error or convergence certificates.
'''

def numeric(text):
    return Counter(x.strip() for x in text.splitlines() if '&' in x and re.search(r'\d',x) and not x.lstrip().startswith('>'))

def prepare(root:Path):
    paper=Path('paper/engineering_optimization')
    src=root/'revision'/paper
    out=root/'submission_20261014/source'/paper
    out.parent.mkdir(parents=True,exist_ok=True)
    shutil.copytree(src,out,dirs_exist_ok=True,ignore=shutil.ignore_patterns('build','__pycache__','*.pyc'))
    main=(src/'EO_manuscript.tex').read_text()
    old_main=main
    old_central='The central object of this study is a conditional first-action audit record. It fixes a learned state and objective context, changes the first action, and then follows a declared continuation with the same external candidate stream while each branch develops its own observed history. The horizon, comparison margin and reader-request budget specify the judgment. This target differs from changing an entire policy throughout an optimization trajectory.'
    new_central='The main computational object is a certified response-domain outer set of possible next actions for a fixed-kernel Gaussian process. Numerical coefficient bands account for the binary linear system; exact envelope queries produce closed feasible intervals and short exclusion witnesses. The engineering evaluation places this operator inside a conditional first-action audit: a learned state and objective context are fixed, the first action is varied, and each branch follows a declared continuation with the same external candidate stream and its own observed history. The horizon, comparison margin and reader-request budget specify the judgment. The audit differs from changing an entire policy throughout an optimization trajectory.'
    assert main.count(old_central)==1
    main=main.replace(old_central,new_central)
    old_questions='Three questions organize the evidence: does the signal change the paid action; does its immediate utility represent its declared finite-horizon consequence; and does obtaining that information justify complete cost relative to the strongest simple same-target reader? Calibration, conditional intervention and whole-policy validation are separate evidence objects. The implemented record, source-specific settings and frozen observation schedules are specified in Table~\\ref{tab:conditional_algorithm}.'
    new_questions='The evaluation separates computational correctness and cost from decision sufficiency. For the operator, we check complete action-set equality, closed ties and every exclusion witness, then compare construction times on identical coefficient bands. For downstream engineering use, we ask whether narrower action information changes a certifiable judgment and whether complete cost improves on the strongest simple same-target reader. Calibration, conditional intervention and whole-policy validation remain separate evidence objects. The implemented audit record, source-specific settings and frozen observation schedules are specified in Table~\\ref{tab:conditional_algorithm}.'
    assert main.count(old_questions)==1
    main=main.replace(old_questions,new_questions)
    main=re.sub(r'\\received\{[^\n]*\}\n','',main,count=1)
    main=main.replace(r'\noindent{\small\textit{Working manuscript. Affiliations b and c remain to be supplied.}}',r'\noindent{\small\textit{Preparation copy: author affiliations b and c remain to be supplied.}}')
    main=main.replace('expensive engineering optimization; surrogate model management; decision auditing; evaluation allocation; finite-element design','expensive engineering optimization; Gaussian processes; numerical certificates; affine envelopes; decision auditing')
    start=main.index(r'\section*{Availability of Data and Materials}')
    end=main.index(r'\section*{Ethics Approval}',start)
    main=main[:start]+r'\section*{Availability of Data and Materials}'+'\n\n'+DATA_STATEMENT+'\n\n'+main[end:]
    anchor='Supplementary tables retain all existing budgets/margins, complete seed-block counts and the selected paired-grid ranges.'
    assert main.count(anchor)==1
    main=main.replace(anchor,anchor+' The paired-grid ranges are preserved historical outputs; three final raw recovery files remain unavailable in the current preservation check. This limits complete independent raw-record replay for that supporting check, as detailed in the data-availability statement and supplement.')
    # Disclose the actual assistance; do not replace it with a copyediting-only claim.
    main=main.replace('Venue-specific AI preparation requirements will be assessed when a publication destination is selected; compliance is not certified by this working manuscript.','The present preparation uses a GPT-6-based Codex agent. Exact tool versions and full prompt histories for earlier assistance have not been independently certified. This statement does not certify compliance with a publication venue\'s manuscript-preparation policy.')
    assert not numeric(old_main)-numeric(main)
    (out/'EO_manuscript.tex').write_text(main)
    supp=(src/'EO_supplementary.tex').read_text()
    availability_pattern=r'(?m)^The manuscript sources, implementation, frozen configurations, and dependency records[^\n]*'
    assert len(re.findall(availability_pattern,supp))==1
    supplement_access=r'''The source repository is private, so its URL alone does not provide reviewer access. The scoped data-and-code attachment contains the complete inputs and certificates for the current GP action-set verification, plus selected frozen decision records. Complete raw reconstruction of the supporting paired-grid check is currently unavailable: 22 of 25 audit-listed files have been recovered, while the final recovery journal, response collection and status remain missing. The historical outputs are retained with this limitation; they cannot replace the absent raw records. The current preservation status is detailed in Section~\ref{supp:current_availability}. The authors report a local copy of approximately 13.6 GB of historical outputs, but it has not been fully inspected in this preparation and is not part of the scoped attachment. Full historical availability is not guaranteed. Third-party implementations and publisher templates retain their own terms. The detailed historical audit trail remains in S8; this map is a navigation layer rather than a substitute for those records.'''
    supp=re.sub(availability_pattern,lambda _:supplement_access,supp,count=1)
    assert r'\input{integrated_evidence/submission_archival_status.tex}' not in supp
    supp=supp.replace(r'\bibliographystyle{tfcad}',r'\input{integrated_evidence/submission_archival_status.tex}'+'\n\n'+r'\bibliographystyle{tfcad}',1)
    (out/'EO_supplementary.tex').write_text(supp)
    (out/'integrated_evidence/submission_archival_status.tex').write_text(ARCHIVAL_NOTE)
    status=json.loads((src/'work_status.json').read_text())
    status['sole_current_scientific_baseline']=BASELINE
    status['submission_ready']=False
    status['submission_preparation_20261014']={
      'target_journal':'Engineering Optimization','author_affiliations_b_c':'pending by user instruction',
      'publisher_ai_policy_reviewed':True,'publisher_ai_compliance_certified':False,
      'paired_grid_raw_expected':25,'paired_grid_raw_recovered_hash_matching':22,
      'paired_grid_complete_raw_replay_currently_possible':False,
      'gp_evidence_complete_in_scoped_packet':True,'new_physical_evaluations':0,
      'remaining_witness_attempts':0,'independent_optimization_gate_opened':False,
      'journal_specific_word_limit_and_upload_limits_verified':False,
      'actual_submission_performed':False}
    (out/'work_status.json').write_text(json.dumps(status,indent=2)+'\n')
    abstract=re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}',main,re.S).group(1).strip()
    authors=[{'name':'Shu-Chuan Chu','affiliation':'School of Computer Science, Nanjing University of Information Science and Technology, Nanjing 210044, Jiangsu, China','corresponding':True,'email':'100130@nuist.edu.cn','ORCID':None},
      {'name':'Ya-Yu Zhang','affiliation':'School of Computer Science, Nanjing University of Information Science and Technology, Nanjing 210044, Jiangsu, China','corresponding':False,'email':None,'ORCID':None},
      {'name':'Zhenyu Meng','affiliation':None,'corresponding':False,'email':None,'ORCID':None},
      {'name':'Jia Zhao','affiliation':None,'corresponding':False,'email':None,'ORCID':None}]
    plain_abstract=abstract.replace('$O(M\\log M)$','O(M log M)').replace('--','-')
    meta={'journal':'Engineering Optimization','journal_homepage':'https://www.tandfonline.com/journals/geno20',
      'article_type_suggested':'Research article; confirm actual portal dropdown','peer_review':'single blind, official journal search record checked on 14 October 2026',
      'title':TITLE,'abstract_tex':abstract,'abstract_plaintext':plain_abstract,'abstract_whitespace_word_count':len(plain_abstract.split()),
      'keywords':['expensive engineering optimization','Gaussian processes','numerical certificates','affine envelopes','decision auditing'],
      'authors':authors,'funding':'No specific funding, inherited manuscript statement; factual confirmation required before submission',
      'conflict_of_interest':'No conflicts, inherited manuscript statement; factual confirmation required before submission',
      'originality_and_exclusive_submission_statement':None,'reviewer_suggestions':[],
      'public_data_link':None,'license':None,'actual_submission':False,'manuscript_id':None,
      'ready_for_final_submit':False}
    folder=root/'submission_20261014';folder.mkdir(exist_ok=True)
    (folder/'PORTAL_FIELDS.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False)+'\n')
    (folder/'ABSTRACT_AND_KEYWORDS.txt').write_text(TITLE+'\n\n'+plain_abstract+'\n\nKeywords: '+ '; '.join(meta['keywords'])+'\n')
    receipts=[]
    for p in sorted(out.rglob('*')):
      if p.is_file() and 'build' not in p.relative_to(out).parts and p.name not in ['interact.cls','tfcad.bst']:
       b=p.read_bytes();receipts.append({'path':p.relative_to(folder).as_posix(),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
    verification={'baseline':BASELINE,'historical_main_numeric_rows_preserved':not numeric(old_main)-numeric(main),
      'historical_supplement_numeric_rows_preserved':not numeric((src/'EO_supplementary.tex').read_text())-numeric(supp),
      'original_bibliography_byte_preserved':(out/'EO_references.bib').read_bytes()==(src/'EO_references.bib').read_bytes(),
      'abstract_words':len(abstract.split()),'core_algorithm_or_empirical_results_changed':False,
      'source_files':receipts,'new_physical_evaluations':0,'final_submit_ready':False}
    assert verification['historical_supplement_numeric_rows_preserved']
    (folder/'SOURCE_VERIFICATION.json').write_text(json.dumps(verification,indent=2)+'\n')
    return {'source_folder':str(out),'main_numeric_rows':len(list(numeric(main).elements())),
      'supplement_numeric_rows':len(list(numeric(supp).elements())),'abstract_words':len(abstract.split()),'new_physical_evaluations':0,'final_submit_ready':False}

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);args=ap.parse_args()
    print(json.dumps(prepare(args.root),indent=2))
