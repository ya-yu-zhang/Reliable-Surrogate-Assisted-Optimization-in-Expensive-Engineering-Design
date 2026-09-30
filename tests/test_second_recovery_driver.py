import json
from pathlib import Path
from src import resume_interrupted_gp_batch_v2 as driver


def signature(method='gp_ei'):
    return dict(fid=1,dim=10,instance=11,rep=0,method=method,budget=100,seed=10001110,
                code_hash='x',packages={'x':'1'})


def test_cached_validation_never_touches_console(tmp_path):
    directory=tmp_path/'run';directory.mkdir();sig=signature()
    (directory/'summary.json').write_text(json.dumps(dict(signature=sig,algorithm_evaluations=100,diagnostic_evaluations=0)))
    log=tmp_path/'run.log';log.write_bytes(b'original console bytes')
    assert driver.validate_cached(directory,sig)['algorithm_evaluations']==100
    assert log.read_bytes()==b'original console bytes'


def test_wrong_cached_signature_rejected(tmp_path):
    directory=tmp_path/'run';directory.mkdir();sig=signature()
    bad=dict(sig);bad['rep']=1
    (directory/'summary.json').write_text(json.dumps(dict(signature=bad,algorithm_evaluations=100,diagnostic_evaluations=0)))
    try:driver.validate_cached(directory,sig)
    except AssertionError:pass
    else:raise AssertionError('wrong signature accepted')
