"""Package checked preparation files and a scoped zero-solver review archive."""
from pathlib import Path
import hashlib,json,zipfile

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write_zip(dest,files,metadata):
    manifest={**metadata,'files':[{'path':n,'bytes':p.stat().st_size,'sha256':sha(p)} for n,p in sorted(files.items())]}
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
      for name,p in sorted(files.items()):
        info=zipfile.ZipInfo(name,(2026,10,14,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,p.read_bytes(),compresslevel=9)
      info=zipfile.ZipInfo('PACKAGE_MANIFEST.json',(2026,10,14,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,json.dumps(manifest,indent=2)+'\n',compresslevel=9)
    with zipfile.ZipFile(dest) as z:
      assert z.testzip() is None
      assert len(z.namelist())==len(files)+1
      for x in manifest['files']:assert len(z.read(x['path']))==x['bytes'] and hashlib.sha256(z.read(x['path'])).hexdigest()==x['sha256'],x['path']
      assert not any(Path(n).name in ['interact.cls','tfcad.bst'] for n in z.namelist())
    return {'file':str(dest),'bytes':dest.stat().st_size,'sha256':sha(dest),'members':len(files)+1,'all_member_hashes_verified':True}

def add_tree(files,root,folder,prefix=None):
    for p in (root/folder).rglob('*'):
      if not p.is_file() or any(x in p.parts for x in ['__pycache__','build']) or p.suffix=='.pyc' or p.name in ['interact.cls','tfcad.bst']:continue
      files[(prefix+'/'+p.relative_to(root/folder).as_posix()) if prefix else p.relative_to(root).as_posix()]=p

def package(root):
    prep=root/'submission_20261014';delivery=root/'deliverables';delivery.mkdir(exist_ok=True)
    review={}
    for folder in ['baseline','baseline_more','revision','restored','src','tests','results/innovation_readiness_20261014','results/gp_envelope_acceleration_20261014','submission_20261014/source','recovery/EO_paired_mesh_partial_recovery_20261014']:
      add_tree(review,root,folder)
    review['upload/01-gp_reachability_20261013_results.zip']=root/'upload/01-gp_reachability_20261013_results.zip'
    for name in ['baseline_receipt.json','baseline_more_receipt.json','runtime_record.json','project_closure_verification.json','project_closure_verification_record.txt','unit_test_record_gp_completion.txt','REPRODUCE_PROJECT_CLOSURE.md','PROJECT_CLOSURE_AND_REVIEW.md','BACKUP_BEFORE_CLEANUP.md']:
      review[name]=root/name
    for name in ['REVIEW_REPRODUCTION.md','SOURCE_VERIFICATION.json','VENUE_AND_SUBMISSION_STATE.json','core_verification_record.txt']:
      review['submission_20261014/'+name]=prep/name
    common={'sole_current_scientific_baseline':'58f539c2d0738b20c7d0d4889fe8d808a03a3019','date':'2026-10-14',
      'new_physical_evaluations':0,'remaining_witness_attempts':0,'new_independent_optimization_samples':0,
      'full_historical_13_6_GB_archive_included':False,'complete_paired_mesh_raw_archive_included':False,
      'paired_mesh_raw_files_verified':22,'paired_mesh_raw_files_expected':25,
      'publisher_assets_excluded':['interact.cls','tfcad.bst'],'journal_submission_performed':False}
    code_zip=delivery/'Data_and_Code_for_Review_20261014.zip'
    code_receipt=write_zip(code_zip,review,{**common,'scope':'Current complete GP inputs, certificates and verification code; selected historical records and partial paired-grid recovery.'})
    files={'Data_and_Code_for_Review_20261014.zip':code_zip}
    for p in (root/'output/pdf/submission_20261014').glob('*.pdf'):files['pdf/'+p.name]=p
    add_tree(files,root,'submission_20261014/source',prefix='source')
    for name in ['START_HERE_20261014.md','REVIEW_REPRODUCTION.md','COVER_LETTER.txt','ABSTRACT_AND_KEYWORDS.txt','PORTAL_FIELDS.json','SOURCE_VERIFICATION.json','VENUE_AND_SUBMISSION_STATE.json','PDF_REVIEW.json','FINAL_CHECKS.json','core_verification_record.txt','main_build_record.txt','supplement_build_record.txt']:
      files[name]=prep/name
    for name in ['prepare_submission_20261014.py','build_submission_documents.py','package_submission_20261014.py']:
      files['preparation_code/'+name]=root/'src'/name
    dest=delivery/'EO_submission_preparation_20261014.zip'
    receipt=write_zip(dest,files,{**common,'scope':'Journal preparation copy; author metadata and policy applicability remain pending.',
      'final_submit_ready':False,'author_affiliations_b_c':'pending by user instruction','publisher_ai_compliance_certified':False})
    record={'review_archive':code_receipt,'submission_archive':receipt,'actual_submission':False,'final_submit_ready':False}
    (prep/'DELIVERY_RECEIPT.json').write_text(json.dumps(record,indent=2)+'\n')
    return record

if __name__=='__main__':print(json.dumps(package(Path(__file__).resolve().parents[1]),indent=2))
