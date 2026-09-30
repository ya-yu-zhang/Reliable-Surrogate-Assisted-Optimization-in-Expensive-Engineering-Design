"""Archive the zero-physical-call candidate-only tolerance refusal."""
from __future__ import annotations
import hashlib,json,shutil
from pathlib import Path
from .run_solo_cost import process_inventory
ROOT=Path(__file__).resolve().parents[1];ARCHIVE=ROOT/'results/application_cma_state_roundoff_failure_v2'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not ARCHIVE.exists()
    assert not any('resume_application_after_cma_roundoff_v5' in (p['CommandLine'] or '') or
                   'recover_interrupted_application_run_v2' in (p['CommandLine'] or '') for p in process_inventory())
    status=json.loads((ROOT/'results/application_completion_v1/status.json').read_text('utf-8'));assert status['stage']=='failed'
    cma=ROOT/'results/application_formal_v1/cma_es_DNA_r08_b500';assert cma.is_dir() and not (cma/'summary.json').exists()
    assert (cma/'recovery_physical_calls.jsonl').read_text('utf-8')==''
    assert sum((p/'summary.json').is_file() for p in (ROOT/'results/application_formal_v1').iterdir() if p.is_dir())==378
    ARCHIVE.mkdir();shutil.move(str(cma),str(ARCHIVE/cma.name));shutil.move(str(ROOT/'results/application_completion_v1'),str(ARCHIVE/'failed_completion_state'))
    for p in sorted((ROOT/'results').glob('sixteenth_application_*.log')):shutil.move(str(p),str(ARCHIVE/p.name))
    files=sorted(p for p in ARCHIVE.rglob('*') if p.is_file());m={'schema':'application_cma_state_roundoff_failure_v2',
      'physical_objective_calls':0,'candidate_only_tolerance_pairs_passed':57,'first_state_roundoff_mismatch_t':58,
      'files':{p.relative_to(ROOT).as_posix():digest(p) for p in files}}
    (ARCHIVE/'archive_manifest.json').write_text(json.dumps(m,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in m.items() if k!='files'},indent=2))
if __name__=='__main__':main()
