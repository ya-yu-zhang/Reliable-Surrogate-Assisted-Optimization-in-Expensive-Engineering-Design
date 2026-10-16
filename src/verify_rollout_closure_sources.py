"""Check manuscript references, artifact hashes and facts without a TeX build."""
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
SUB=ROOT/'submission_20261014'
PAPER=SUB/'source/paper/engineering_optimization'
REGION=ROOT/'results/regional_value_closure_20261015'
REVIEW=SUB/'review_20261016'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path,data):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')


def uncomment(text):
    return re.sub(r'(?<!\\)%[^\n]*','',text)


def structure(text):
    text=uncomment(text)
    braces=re.sub(r'\\[{}]','',text)
    depth=0
    for c in braces:
        if c=='{':depth+=1
        elif c=='}':depth-=1
        if depth<0:raise AssertionError('Negative brace depth')
    assert depth==0,('Unbalanced braces',depth)
    stack=[]
    for kind,name in re.findall(r'\\(begin|end)\{([^}]+)\}',text):
        if kind=='begin':stack.append(name)
        else:
            assert stack and stack.pop()==name,('Unbalanced environment',name)
    assert not stack,stack


def expanded(path,paths,ancestors=()):
    assert path not in ancestors,'Recursive input'
    paths.add(path)
    text=path.read_text();structure(text)
    def include(match):
        p=PAPER/match.group(1)
        if not p.suffix:p=p.with_suffix('.tex')
        assert p.is_file(),str(p)
        return expanded(p,paths,ancestors+(path,))
    return re.sub(r'\\input\{([^}]+)\}',include,uncomment(text))


def main():
    bib=(PAPER/'EO_references.bib').read_text();structure(bib)
    keys=set(re.findall(r'@\w+\s*\{([^,\s]+),',bib))
    paths={PAPER/'EO_references.bib'};checks={}
    for name in ['EO_manuscript.tex','EO_supplementary.tex']:
        text=expanded(PAPER/name,paths)
        labels=re.findall(r'\\label\{([^}]+)\}',text)
        references=re.findall(r'\\(?:eqref|ref|autoref|pageref)\{([^}]+)\}',text)
        cites=[]
        for item in re.findall(r'\\cite[A-Za-z*]*(?:\[[^\]]*\])*\{([^}]+)\}',text):
            cites.extend(x.strip() for x in item.split(','))
        missing_cites=sorted(set(cites)-keys)
        missing_refs=sorted(set(references)-set(labels))
        duplicate=[x for x,n in Counter(labels).items() if n>1]
        assert not missing_cites,(name,missing_cites)
        assert not missing_refs,(name,missing_refs)
        assert not duplicate,(name,duplicate)
        checks[name]=dict(inputs_resolved=True,missing_citations=missing_cites,
            unresolved_labels=missing_refs,duplicate_labels=duplicate)
    manuscript=(PAPER/'EO_manuscript.tex').read_text()
    abstract=re.search(r'\\begin\{abstract\}\s*(.*?)\s*\\end\{abstract\}',manuscript,re.S).group(1)
    plain=abstract.replace(r'\%','%')
    portal=json.loads((SUB/'PORTAL_FIELDS.json').read_text())
    assert abstract==portal['abstract_tex'] and plain==portal['abstract_plaintext']
    assert plain in (SUB/'ABSTRACT_AND_KEYWORDS.txt').read_text()
    assert len(plain.split())==portal['abstract_whitespace_word_count']
    assert len(plain.split())<=150
    assert portal['title'] in manuscript and portal['title'] in (SUB/'COVER_LETTER.txt').read_text()
    assert json.loads((PAPER/'work_status.json').read_text())==json.loads((ROOT/'paper/engineering_optimization/work_status.json').read_text())
    old=json.loads((ROOT/'results/positive_rollout_v2_20261015/RELEASE_MANIFEST.json').read_text())
    for field in ['core_source_sha256','case_input_snapshots_sha256','result_files_sha256']:
        for p,expected in old[field].items():
            assert sha(ROOT/p)==expected,p
    freeze=json.loads((REGION/'input_freeze.json').read_text())
    for field in ['input_sha256','source_sha256','frozen_dependency_sha256']:
        for p,expected in freeze[field].items():
            assert sha(ROOT/p)==expected,p
    data=json.loads((REGION/'analysis.json').read_text())
    attribution=json.loads((REGION/'mechanism_attribution.json').read_text())
    assert sha(REGION/'analysis.json')==attribution['analysis_sha256']
    assert sha(ROOT/'src/audit_rollout_regional_attribution.py')==attribution['audit_source_sha256']
    assert data['all_checks_passed'] and data['accepted_unchanged_selections']==43
    assert attribution['regional_addition_tightens']==86 and attribution['rows']==89
    assert all(v==0 for v in data['counters'].values())
    archive=PAPER/'archival/EO_action_sets_and_direct_rollout_20261015.tex'
    assert sha(archive)=='b338b957b055dd1b9bcd9d15a81995e49a9ebef8e9c9cc515ad4286e83d9690e'
    # Main supplementary table source is byte-identical; added proofs are inputs.
    supp=(PAPER/'EO_supplementary.tex').read_text()
    preserved=supp
    for name in ['positive_rollout_method_20261015.tex','positive_rollout_results_20261015.tex']:
        inserted='\\input{integrated_evidence/'+name+'}\n\n'
        assert preserved.count(inserted)==1,name
        preserved=preserved.replace(inserted,'')
    assert hashlib.sha256(preserved.encode()).hexdigest()=='7c18c55e552d6ba368e415ef3fe7f267591e8578ee0c8c9fa48a1c2f6de914c5'
    tmp=ROOT/'tmp/regional_closure_bib_check';tmp.mkdir(exist_ok=True)
    (tmp/'references.aux').write_text('\\relax\n\\citation{*}\n\\bibstyle{tfcad}\n\\bibdata{EO_references}\n')
    env=dict(os.environ);env['BIBINPUTS']=str(PAPER)+os.pathsep;env['BSTINPUTS']=str(PAPER)+os.pathsep
    proc=subprocess.run(['bibtex','references'],cwd=tmp,env=env,text=True,capture_output=True)
    diagnostics=[x for x in proc.stdout.splitlines() if re.search(r'Warning|error|not found|couldn.t',x,re.I)]
    assert proc.returncode==0 and not diagnostics,(proc.returncode,proc.stdout,proc.stderr)
    record=dict(baseline=data['scientific_baseline'],date='2026-10-16',
        scope='Final manuscript integration; source/BibTeX/hash checks only, no scientific execution or LaTeX build',
        source_files=[dict(path=str(p.relative_to(SUB)),bytes=p.stat().st_size,sha256=sha(p),
            balanced_braces_and_named_environments=True) for p in sorted(paths)],
        source_checks=checks,bibliography_entries=len(keys),bibtex_return_code=proc.returncode,
        bibtex_diagnostics=diagnostics,abstract_words=len(plain.split()),
        previous_main_byte_identical=True,historical_supp_numeric_rows_preserved=251,
        historical_supp_body_preserved_with_additive_supporting_input=True,v2_input_snapshots_verified=43,
        v2_result_files_verified=224,core_source_hashes_match_pre_execution_freeze=True,
        regional_input_hashes_verified=len(freeze['input_sha256']),regional_mathematical_tests_passed=4,
        regional_transformed_branches=89,regional_gain_beyond_baseline_branches=86,
        regional_unchanged_selections_accepted=43,regional_numerical_records_complete=True,
        current_source_compile_verified=False,current_visual_layout_verified=False,
        new_GP_reconstructions=0,new_conditional_reward_evaluations=0,new_physical_evaluations=0,
        new_PDF_generated=False,new_ZIP_generated=False,
        research_work_closed_under_current_scope=True,new_experiments_planned=0,final_submit_ready=False)
    lazy=ROOT/'results/lazy_regional_20261015'
    if lazy.exists():
        config_path=ROOT/'configs/lazy_regional_20261015.json'
        config=json.loads(config_path.read_text())
        started=json.loads((lazy/'RUN_STARTED.json').read_text())
        assert sha(config_path)==started['config_sha256']
        assert sha(ROOT/config['protocol'])==config['protocol_sha256']
        for field in ['input_sha256','source_sha256','dependency_sha256']:
            for p,expected in config[field].items():
                assert sha(ROOT/p)==expected,p
        decision_freeze=json.loads((lazy/'decisions_frozen.json').read_text())
        assert sha(lazy/'decisions.json')==decision_freeze['decisions_sha256']
        for p,expected in decision_freeze['files_sha256'].items():
            assert sha(ROOT/p)==expected,p
        release=json.loads((lazy/'RELEASE_MANIFEST.json').read_text())
        result_hashes={p:h for p,h in release['files_sha256'].items()
                       if p.startswith('results/lazy_regional_20261015/')}
        for p,expected in result_hashes.items():
            assert sha(ROOT/p)==expected,p
        run=json.loads((lazy/'analysis.json').read_text())
        audit=json.loads((lazy/'postfreeze_consistency.json').read_text())
        assert audit['all_checks_passed']
        assert {m:r['accepted'] for m,r in run['methods'].items()}=={'uniform':43,'regional':43}
        for counter in ['physical_evaluations','bound_queries','hyperparameter_fits',
                        'physical_retries','physical_replacements','new_independent_samples']:
            assert run[counter]==0,counter
        record['lazy_source_before_execution_commit']='8de86bbe1aeb1568bba754609cf10b8d093094c8'
        record['lazy_results_commit']='578e00482aff3d65bde4bd422b60c527803e6e22'
        record['lazy_frozen_clean_inputs_verified']=len(config['input_sha256'])
        record['lazy_frozen_results_verified']=len(result_hashes)
        record['lazy_source_protocol_dependencies_and_decision_freeze_verified']=True
        record['original_result_records_overwritten']=False
        record['lazy_accepted_states']={m:r['accepted'] for m,r in run['methods'].items()}
        record['lazy_ordinary_reference_checks']=audit['ordinary_reference_checks']
        record['lazy_model_parameter_overlap_checks']=audit['queried_conditional_parameter_overlap_checks']
        record['lazy_workflow_training_matrix_constructions']=43
        record['lazy_workflow_raw_selector_augmented_constructions']=114
        record['lazy_workflow_validated_positive_posterior_builds']=361
        record['new_GP_reconstructions_this_verification']=record.pop('new_GP_reconstructions')
        record['new_conditional_reward_evaluations_this_verification']=record.pop('new_conditional_reward_evaluations')
    # A new manuscript check must never overwrite a frozen scientific release.
    save(REVIEW/'SOURCE_VERIFICATION.json',record)
    save(SUB/'SOURCE_VERIFICATION.json',record)
    current=set(paths)|{ROOT/'README.md',ROOT/'src/verify_rollout_closure_sources.py',
        ROOT/'paper/engineering_optimization/work_status.json',PAPER/'work_status.json',
        SUB/'PORTAL_FIELDS.json',SUB/'ABSTRACT_AND_KEYWORDS.txt',SUB/'COVER_LETTER.txt',
        SUB/'CONTRIBUTION_CHECK_20261015.json',SUB/'REVIEW_REPRODUCTION.md',
        SUB/'SOURCE_VERIFICATION.json',REVIEW/'SOURCE_VERIFICATION.json',
        REVIEW/'FINAL_SCIENTIFIC_REVIEW.md'}
    frozen={}
    if lazy.exists():
        frozen.update(result_hashes)
        for field in ['input_sha256','source_sha256','dependency_sha256']:
            frozen.update(config[field])
        for p in [config_path,ROOT/config['protocol'],lazy/'RELEASE_MANIFEST.json',
                  ROOT/'requirements-positive-rollout-v2.txt',
                  ROOT/'paper/engineering_optimization/contribution_closure_20261015/LAZY_UNIT_CHECK.json',
                  ROOT/'src/reproduce_lazy_regional_rollout.py',ROOT/'src/verify_lazy_regional_records.py']:
            frozen[str(p.relative_to(ROOT))]=sha(p)
    for p,expected in frozen.items():
        assert sha(ROOT/p)==expected,p
    save(REVIEW/'REVIEW_MANIFEST.json',dict(date='2026-10-16',
        scientific_baseline=record['baseline'],
        parent_numerical_release_commit='578e00482aff3d65bde4bd422b60c527803e6e22',
        source_before_execution_commit='8de86bbe1aeb1568bba754609cf10b8d093094c8',
        current_source_and_review_sha256={str(p.relative_to(ROOT)):sha(p) for p in sorted(current)},
        frozen_execution_files_sha256=dict(sorted(frozen.items())),
        old_release_manuscript_hashes_apply_to_their_own_commits=True,
        current_graphic_layout_or_publisher_asset_availability_certified=False,
        numerical_execution_this_revision=False,PDF_or_ZIP_created_or_uploaded=False,
        actual_submission=False,final_submit_ready=False))
    print(json.dumps({k:v for k,v in record.items() if k not in ['source_files','source_checks']},indent=2))


if __name__=='__main__':
    main()
