import json
import pytest
from src.core import Settings
from src.experiment import run_one
from src.analyze_model_sensitivity import audit_run


def test_actual_internal_journal_and_future_index_rejection(tmp_path):
    summary=run_one((1,3,4,0,'PEM_T',52,str(tmp_path),'checkpoints'));directory=tmp_path/summary['runid']
    audit_run(directory,summary,Settings())
    path=directory/'events.jsonl';events=[json.loads(v) for v in path.read_text().splitlines()]
    for pre in events[1::2]:
        if pre.get('train_indices'):
            pre['train_indices'][0]=pre['t'];break
    path.write_text('\n'.join(json.dumps(v) for v in events)+'\n')
    with pytest.raises(AssertionError):audit_run(directory,summary,Settings())
