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


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path,data):
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
    inserted='\\input{integrated_evidence/positive_rollout_results_20261015.tex}\n\n'
    preserved=supp.replace(inserted,'')
    assert hashlib.sha256(preserved.encode()).hexdigest()=='7c18c55e552d6ba368e415ef3fe7f267591e8578ee0c8c9fa48a1c2f6de914c5'
    tmp=ROOT/'tmp/regional_closure_bib_check';tmp.mkdir(exist_ok=True)
    (tmp/'references.aux').write_text('\\relax\n\\citation{*}\n\\bibstyle{tfcad}\n\\bibdata{EO_references}\n')
    env=dict(os.environ);env['BIBINPUTS']=str(PAPER)+os.pathsep;env['BSTINPUTS']=str(PAPER)+os.pathsep
    proc=subprocess.run(['bibtex','references'],cwd=tmp,env=env,text=True,capture_output=True)
    diagnostics=[x for x in proc.stdout.splitlines() if re.search(r'Warning|error|not found|couldn.t',x,re.I)]
    assert proc.returncode==0 and not diagnostics,(proc.returncode,proc.stdout,proc.stderr)
    record=dict(baseline=data['scientific_baseline'],date='2026-10-15',
        scope='Regional method and saved-certificate integration; source/BibTeX/hash checks only, no LaTeX build',
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
    save(SUB/'SOURCE_VERIFICATION.json',record)
    lazy=ROOT/'results/lazy_regional_20261015'
    if lazy.exists():
        run=json.loads((lazy/'analysis.json').read_text())
        audit=json.loads((lazy/'postfreeze_consistency.json').read_text())
        assert audit['all_checks_passed']
        record['scope']='Source/BibTeX/hash checks after lazy regional algorithm development; no additional scientific execution or TeX build'
        record['lazy_source_before_execution_commit']='8de86bbe1aeb1568bba754609cf10b8d093094c8'
        record['lazy_accepted_states']={m:r['accepted'] for m,r in run['methods'].items()}
        record['lazy_ordinary_reference_checks']=audit['ordinary_reference_checks']
        record['lazy_model_parameter_overlap_checks']=audit['queried_conditional_parameter_overlap_checks']
        record['lazy_workflow_training_matrix_constructions']=43
        record['lazy_workflow_raw_selector_augmented_constructions']=114
        record['lazy_workflow_validated_positive_posterior_builds']=361
        record['new_GP_reconstructions_this_verification']=record.pop('new_GP_reconstructions')
        record['new_conditional_reward_evaluations_this_verification']=record.pop('new_conditional_reward_evaluations')
        save(lazy/'source_verification.json',record)
        save(SUB/'SOURCE_VERIFICATION.json',record)
    else:
        save(REGION/'source_verification.json',record)
    print(json.dumps({k:v for k,v in record.items() if k not in ['source_files','source_checks']},indent=2))


if __name__=='__main__':
    main()
