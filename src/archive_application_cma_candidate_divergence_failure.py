"""Archive the zero-call CMA replay that exposed eigensystem-amplified divergence."""
from __future__ import annotations
import hashlib,json,shutil
from pathlib import Path
from .run_solo_cost import process_inventory
ROOT=Path(__file__).resolve().parents[1];ARCHIVE=ROOT/'results/application_cma_candidate_divergence_failure_v3'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not ARCHIVE.exists() and not any('resume_application_after_cma_state_roundoff_v6' in (p['CommandLine'] or '') or 'recover_interrupted_application_run_v3' in (p['CommandLine'] or '') for p in process_inventory())
    status=json.loads((ROOT/'results/application_completion_v1/status.json').read_text('utf-8'));assert status['stage']=='failed'
    cma=ROOT/'results/application_formal_v1/cma_es_DNA_r08_b500';assert cma.is_dir() and not (cma/'summary.json').exists() and (cma/'recovery_physical_calls.jsonl').read_text('utf-8')==''
    ARCHIVE.mkdir();shutil.move(str(cma),str(ARCHIVE/cma.name));shutil.move(str(ROOT/'results/application_completion_v1'),str(ARCHIVE/'failed_completion_state'))
    for p in sorted((ROOT/'results').glob('seventeenth_application_*.log')):shutil.move(str(p),str(ARCHIVE/p.name))
    files=sorted(p for p in ARCHIVE.rglob('*') if p.is_file());m={'schema':'application_cma_candidate_divergence_failure_v3','physical_objective_calls':0,
      'state_tolerance_pairs_passed':76,'first_candidate_divergence_t':77,'candidate_max_absolute_difference':1.015067141452164e-9,
      'files':{p.relative_to(ROOT).as_posix():digest(p) for p in files}}
    (ARCHIVE/'archive_manifest.json').write_text(json.dumps(m,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in m.items() if k!='files'},indent=2))
if __name__=='__main__':main()
