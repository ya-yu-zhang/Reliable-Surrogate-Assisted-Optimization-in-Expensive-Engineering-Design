"""Independent budget-prefix integrity fixtures; never benchmark performance evidence."""
import os
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:
    os.environ[key]='1'
import hashlib
import json
from pathlib import Path
from time import perf_counter
import zipfile

from .core import METHODS
from .experiment import run_one,code_hash

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/budget_prefix_integrity_v1'
EXPECTED_HASH='dca9908b6cdec3c00842052de29b6cd5c8e5b7633ef01d305fcf40c1c89e08d2'
CASES=[(method,10) for method in METHODS if method not in ['explore_only','pool_random']]+[('PEM_T',40),('PEM_ST',40)]


def read_events(directory):
    events=[json.loads(v) for v in (directory/'events.jsonl').read_text('utf-8').splitlines()]
    assert events[0]['event']=='meta'
    return events[1:]


def main():
    assert code_hash()==EXPECTED_HASH
    if 'PEM_FIXED_P' in os.environ:raise RuntimeError('Prefix fixtures require the original explicit T_fixed default .3')
    assert len(CASES)==15
    # The design is fixed before any fixture labels; instance4 is not a benchmark instance.
    expected_calls=sum(30*dim for _,dim in CASES)
    assert expected_calls==6300
    manifest=dict(cases=CASES,fid=1,instance=4,rep=0,budget_multipliers=[5,10,15],
        capture='all',expected_calls=expected_calls,source_hash=EXPECTED_HASH,
        performance_sample=False,source_files={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
            for name in ['src/core.py','src/experiment.py','src/audit_budget_prefix.py']})
    OUT.mkdir(parents=True,exist_ok=True)
    file=OUT/'manifest.json'
    if file.exists():assert json.loads(file.read_text('utf-8'))==json.loads(json.dumps(manifest))
    file.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    start=perf_counter();records=[];failure=None;charged=0
    def save(stage):
        (OUT/'status.json').write_text(json.dumps(dict(stage=stage,pid=os.getpid(),cases=len(records),
            expected_cases=len(CASES),algorithm_fixture_calls=charged,expected_calls=expected_calls,
            elapsed=perf_counter()-start,failure=failure),indent=2),encoding='utf-8')
    save('running')
    try:
        for method,dim in CASES:
            runs=[];directories=[]
            for multiplier in [5,10,15]:
                assert code_hash()==EXPECTED_HASH
                budget=multiplier*dim;directory=OUT/f'budget_{multiplier}D'
                summary=run_one((1,dim,4,0,method,budget,str(directory),'all'))
                assert summary['algorithm_evaluations']==budget
                path=directory/summary['runid'];runs.append(summary);directories.append(path)
                charged+=budget;save('running')
            events=[read_events(path) for path in directories]
            assert [len(v) for v in events]==[10*dim,20*dim,30*dim]
            assert events[0]==events[1][:len(events[0])]==events[2][:len(events[0])]
            assert events[1]==events[2][:len(events[1])]
            assert all(v['n0']==2*dim+20 for v in runs)
            archives_compared=0
            with zipfile.ZipFile(directories[2]/'candidate_pools.npz') as long:
                for directory in directories[:2]:
                    with zipfile.ZipFile(directory/'candidate_pools.npz') as short:
                        assert set(short.namelist()).issubset(long.namelist())
                        for name in short.namelist():
                            assert short.read(name)==long.read(name);archives_compared+=1
            capped=sum(len(pre.get('train_indices',[]))==256 and pre['n_observed']>256
                for pre in events[1][::2])
            if dim==40:assert capped>0
            records.append(dict(method=method,dim=dim,prefix_5D_10D_15D_equal=True,
                all_pre_and_label_records_compared=True,arrays_compared_bytewise=archives_compared,
                truncated_fits_in_compared_10D_prefix=capped,fixture_calls=30*dim))
            save('running');print(f'{len(records)}/15 prefix fixtures complete; paid calls {charged}',flush=True)
        assert charged==expected_calls
        (OUT/'audit.json').write_text(json.dumps(dict(cases=records,complete=True,
            algorithm_fixture_calls=charged,diagnostic_calls=0,original_sources_unchanged=True,
            all_three_budget_prefixes_equal=True,performance_sample=False),indent=2),encoding='utf-8')
        hashes={path.relative_to(ROOT).as_posix():hashlib.sha256(path.read_bytes()).hexdigest()
            for path in OUT.glob('budget_*D/*/*') if path.name in ['summary.json','events.jsonl','candidate_pools.npz']}
        assert len(hashes)==135
        (OUT/'source_hashes.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
        save('complete')
    except Exception as error:
        failure=dict(error=str(error));save('failed');raise


if __name__=='__main__':main()
