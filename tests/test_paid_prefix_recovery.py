import json
from pathlib import Path

import pytest

pytest.importorskip('torch',reason='GP recovery invariants require the isolated baseline environment')
from src.gp_references import run_one
from src.recover_interrupted_run import recover


@pytest.mark.parametrize('method',['gp_ei','turbo_1'])
def test_recovery_preserves_search_and_queries_only_unpaid_suffix(tmp_path,method):
    original=run_one(1,2,4,0,method,8,tmp_path/'original')
    path=tmp_path/'original'/original['runid']/'events.jsonl'
    lines=path.read_text().splitlines();archive=tmp_path/'archive';archive.mkdir()
    (archive/'events.jsonl').write_text('\n'.join(lines[:11])+'\n')
    result,record=recover('gp',1,2,4,0,method,8,tmp_path/'recovered',archive)
    assert result['best']==original['best'] and record['old_paid_calls']==5 and record['new_paid_calls']==3
    assert record['physical_total']==8 and record['replayed_calls_not_reevaluated']==5
    recovered=tmp_path/'recovered'/original['runid']
    physical=[json.loads(v) for v in (recovered/'recovery_physical_calls.jsonl').read_text().splitlines()]
    assert len(physical)==6 and [v['t'] for v in physical[::2]]==[6,7,8]
    events=[json.loads(v) for v in (recovered/'events.jsonl').read_text().splitlines()]
    original_events=[json.loads(v) for v in lines]
    for a,b in zip(events,original_events):
        a.pop('preparation_seconds',None);b.pop('preparation_seconds',None);assert a==b


def test_corrupt_prefix_stops_before_any_unpaid_objective_call(tmp_path):
    original=run_one(1,2,4,0,'gp_ei',8,tmp_path/'original')
    path=tmp_path/'original'/original['runid']/'events.jsonl'
    events=[json.loads(v) for v in path.read_text().splitlines()[:11]]
    events[1]['numpy_rng_hash']='0'*64
    archive=tmp_path/'archive';archive.mkdir()
    (archive/'events.jsonl').write_text('\n'.join(json.dumps(v) for v in events)+'\n')
    with pytest.raises(AssertionError,match='Prefix state mismatch'):
        recover('gp',1,2,4,0,'gp_ei',8,tmp_path/'recovered',archive)
    directory=tmp_path/'recovered'/original['runid']
    assert (directory/'recovery_physical_calls.jsonl').read_text()==''
    assert not (directory/'summary.json').exists()


def test_internal_recovery_preserves_original_residuals_and_candidate_arrays(tmp_path):
    import zipfile
    from src.experiment import run_one as internal
    original=internal((1,3,4,0,'PEM_ST',52,str(tmp_path/'original'),'all'))
    directory=tmp_path/'original'/original['runid']
    lines=(directory/'events.jsonl').read_text().splitlines()
    archive=tmp_path/'archive';archive.mkdir()
    (archive/'events.jsonl').write_text('\n'.join(lines[:99])+'\n')
    result,record=recover('internal',1,3,4,0,'PEM_ST',52,tmp_path/'recovered',archive)
    assert result['best']==original['best'] and record['old_paid_calls']==49 and record['new_paid_calls']==3
    restored=tmp_path/'recovered'/original['runid']
    assert (restored/'events.jsonl').read_text().splitlines()==lines
    with zipfile.ZipFile(directory/'candidate_pools.npz') as a,zipfile.ZipFile(restored/'candidate_pools.npz') as b:
        assert a.namelist()==b.namelist()
        assert all(a.read(name)==b.read(name) for name in a.namelist())
