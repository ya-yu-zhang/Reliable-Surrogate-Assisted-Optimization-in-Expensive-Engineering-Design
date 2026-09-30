import hashlib
import importlib.metadata
import json
import sys
import types

import numpy as np
import pytest
from sklearn.model_selection import KFold

pytest.importorskip('torch', reason='Full application worker checks use the isolated application environment')
from src import application_experiment as worker
from src import analyze_application as analyzer


def test_unknown_optimum_and_postcompletion_test_are_separate(tmp_path,monkeypatch):
    config=dict(datasets=['synt_simple'],methods=['greedy'],dimensions={'synt_simple':2},
        budgets={'synt_simple':30},data_seed=42,dataset_ids={'synt_simple':1},repeats=1,
        n_splits=5,tol_level=1e-4,test_size=.15,capture='checkpoints',out='results',
        runtime_manifest='runtime.json')
    path=tmp_path/'config.json';path.write_text(json.dumps(config))
    (tmp_path/'runtime.json').write_text(json.dumps(dict(python_version=sys.version.split()[0],
        packages={'numpy':importlib.metadata.version('numpy')})))
    frozen=tmp_path/'docs/frozen_application_formal_v1';frozen.mkdir(parents=True)
    (frozen/'sha256.json').write_text(json.dumps({'config.json':hashlib.sha256(path.read_bytes()).hexdigest()}))
    calls=[];tests=[]

    class Benchmark:
        def __init__(self,**kwargs):
            assert kwargs['seed']==42 and kwargs['noise'] is False
            self.n_features=2;self.alpha_min=.1;self.alpha_max=1.
            self.X_train=np.ones((10,2));self.y_train=np.zeros(10)
            self.X_test=np.ones((2,2));self.y_test=np.zeros(2)
            self.kf=KFold(5,shuffle=True,random_state=42)
        def evaluate(self,point):
            assert not tests;calls.append(point.copy())
            return .37+float(np.sum(np.asarray(point)**2))
        def test(self,point):
            assert len(calls)==30
            journal=tmp_path/'results/greedy_synt_simple_r00_b30/events.jsonl'
            events=[json.loads(v) for v in journal.read_text().splitlines()]
            assert len(events)==61 and events[-1]['event']=='label'
            tests.append(point.copy())
            return {'mspe':1000037.,'fscore':.25}

    monkeypatch.setattr(worker,'ROOT',tmp_path)
    monkeypatch.setitem(sys.modules,'LassoBench',types.SimpleNamespace(SyntheticBenchmark=Benchmark,RealBenchmark=Benchmark))
    result=worker.run_one('config.json','synt_simple',0,'greedy')
    assert len(calls)==30 and len(tests)==1
    assert result['optimum_known'] is False and 'error' not in result and 'optimum' not in result
    assert result['best_validation_loss']==min(.37+np.sum(point**2) for point in calls)
    np.testing.assert_array_equal(tests[0],result['best_config'])
    assert result['cv_fold_solves']==150 and result['test_method_calls']==1
    file=tmp_path/'results'/result['runid']/'post_completion_test.json'
    record=json.loads(file.read_text())
    assert record['algorithm_evaluations']==30 and record['metrics']==result['test_metrics']
    assert record['optimization_labels_sha256']==hashlib.sha256((file.parent/'events.jsonl').read_bytes()).hexdigest()
    assert worker.run_one('config.json','synt_simple',0,'greedy')==result
    assert len(calls)==30 and len(tests)==1


def test_complete_raw_audit_replays_feedback_without_objective_calls(tmp_path,monkeypatch):
    config=dict(datasets=['synt_simple'],methods=['greedy','fixed01','PEM_T','PEM_ST'],
        dimensions={'synt_simple':2},budgets={'synt_simple':30},data_seed=42,
        dataset_ids={'synt_simple':1},repeats=1,n_splits=5,tol_level=1e-4,test_size=.15,
        capture='checkpoints',out='results',runtime_manifest='runtime.json',
        bootstrap_seed=923701,bootstrap_replicates=4000)
    directory=tmp_path/'configs';directory.mkdir()
    path=directory/'application_formal.json';path.write_text(json.dumps(config))
    (tmp_path/'runtime.json').write_text(json.dumps(dict(python_version=sys.version.split()[0],
        packages={'numpy':importlib.metadata.version('numpy')})))
    frozen_dir=tmp_path/'docs/frozen_application_formal_v1';frozen_dir.mkdir(parents=True)
    frozen={'configs/application_formal.json':hashlib.sha256(path.read_bytes()).hexdigest()}
    (frozen_dir/'sha256.json').write_text(json.dumps(frozen))
    total=[]
    class Benchmark:
        def __init__(self,**kwargs):
            self.n_features=2;self.alpha_min=.1;self.alpha_max=1.
            self.X_train=np.ones((10,2));self.y_train=np.zeros(10)
            self.X_test=np.ones((2,2));self.y_test=np.zeros(2)
            self.kf=KFold(5,shuffle=True,random_state=42)
        def evaluate(self,point):
            total.append(point.copy());return .37+float(np.sum(np.asarray(point)**2))
        def test(self,point):return {'mspe':1000037.,'fscore':.25}
    monkeypatch.setattr(worker,'ROOT',tmp_path);monkeypatch.setattr(analyzer,'ROOT',tmp_path)
    monkeypatch.setitem(sys.modules,'LassoBench',types.SimpleNamespace(SyntheticBenchmark=Benchmark,RealBenchmark=Benchmark))
    for method in config['methods']:worker.run_one('configs/application_formal.json','synt_simple',0,method)
    out=tmp_path/'results'
    (out/'manifest.json').write_text(json.dumps(dict(config=config,frozen_sources=frozen)))
    (out/'status.json').write_text(json.dumps(dict(stage='complete',completed=4,expected=4,failed=0)))
    (out/'failures.json').write_text('[]')
    before=len(total);analyzer.main();assert len(total)==before==120
    audit=json.loads((tmp_path/'results/application_analysis_v1/audit.json').read_text())
    assert audit['runs']==4 and audit['algorithm_evaluations']==120 and audit['bounds_and_management_replayed']
    # Changing a stored prediction is rejected; the auditor never evaluates it.
    journal=out/'PEM_T_synt_simple_r00_b30/events.jsonl'
    events=[json.loads(v) for v in journal.read_text().splitlines()]
    events[2*20-1]['H']+=1.
    journal.write_text('\n'.join(json.dumps(v) for v in events)+'\n')
    with pytest.raises(AssertionError):analyzer.main()
    assert len(total)==before


def test_formal_start_refuses_live_cost_prerequisite_before_output(tmp_path,monkeypatch):
    from src import run_application_batch as batch
    path=tmp_path/'results/reference_completion_v1';path.mkdir(parents=True)
    (path/'status.json').write_text(json.dumps(dict(stage='serial_cost_measurement',failure=None,pid=1)))
    monkeypatch.setattr(batch,'ROOT',tmp_path)
    with pytest.raises(AssertionError):batch.main()
    assert not (tmp_path/'results/application_formal_v1').exists()
    (path/'status.json').write_text(json.dumps(dict(stage='complete',failure=None,pid=1)))
    monkeypatch.setattr(batch,'process_inventory',lambda:[dict(ProcessId=1,CommandLine='-m src.finish_reference_batch')])
    with pytest.raises(AssertionError,match='has not exited'):batch.main()
    assert not (tmp_path/'results/application_formal_v1').exists()
