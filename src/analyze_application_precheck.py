"""Verify the complete resource-only journals; do not generate labels."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main():
    source = ROOT/'results/application_precheck_v1'
    manifest = json.loads((source/'manifest.json').read_text('utf-8'))
    config = manifest['config'];frozen = manifest['frozen_sources']
    status = json.loads((source/'status.json').read_text('utf-8'))
    assert status['stage']=='complete' and status['completed']==status['expected']==3 and status['failed']==0
    assert not json.loads((source/'failures.json').read_text('utf-8'))
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest for name,digest in frozen.items())
    rows = []; hashes = {}
    for dataset in config['datasets']:
        directory = source/dataset
        summary = json.loads((directory/'summary.json').read_text('utf-8'))
        events = [json.loads(line) for line in (directory/'events.jsonl').read_text('utf-8').splitlines()]
        assert len(events)==13 and events[0]['event']=='meta'
        assert events[0]['dataset']==summary['dataset']==dataset
        assert events[0]['config']==config and events[0]['frozen_sources']==summary['frozen_sources']==frozen
        assert events[0]['data_hashes']==summary['data_hashes'] and events[0]['fold_hash']==summary['fold_hash']
        assert events[0]['dimension']==summary['dimension']==config['dimensions'][dataset]
        assert events[0]['data_seed']==summary['data_seed']==config['data_seed']
        labels = []; durations = []
        for t,(pre,label,level) in enumerate(zip(events[1::2],events[2::2],config['points']),1):
            assert pre['event']=='pre' and label['event']=='label' and pre['t']==label['t']==t
            assert pre['n_observed']==t-1 and 'y' not in pre and 'evaluation_seconds' not in pre
            point = np.asarray(pre['x']); assert point.shape==(summary['dimension'],)
            assert np.isfinite(point).all() and np.all(point==level) and np.all((point>=-1)&(point<=1))
            assert np.isfinite(label['y']) and label['evaluation_seconds']>=0
            labels.append(label['y']);durations.append(label['evaluation_seconds'])
        assert labels[2]==labels[5] and summary['deterministic_repeated_point']
        assert summary['evaluation_seconds']==durations and summary['objective_calls']==6
        assert summary['cv_fold_solves']==30 and summary['test_method_calls']==0
        assert summary['formal_application_result'] is False and summary['shared_load_timing_not_exclusive']
        assert np.isclose(summary['subsequent_evaluation_seconds_median'],np.median(durations[1:]))
        assert summary['process_peak_working_set_bytes']>0 and 2*summary['dimension']+20<=500
        rows.append(dict(dataset=dataset,dimension=summary['dimension'],objective_calls=6,
            construction_seconds=summary['construction_seconds'],first_evaluation_seconds=durations[0],
            subsequent_median_seconds=summary['subsequent_evaluation_seconds_median'],
            peak_memory_gib=summary['process_peak_working_set_bytes']/2**30,
            repeated_zero_configuration_identical=True,
            recorded_warning_count=sum(summary['warning_counts'].values())))
        for name in ['summary.json','events.jsonl']:
            file = directory/name;hashes[str(file.relative_to(ROOT))]=hashlib.sha256(file.read_bytes()).hexdigest()
    provenance = json.loads((ROOT/'literature/downloads/dna_cache_provenance.json').read_text('utf-8'))
    assert provenance['source_matrix_shape']==[2000,180] and provenance['tls_verified'] and provenance['original_library_parser_used']
    assert provenance['raw_sha256']=='03d39477c5e48415e9cd18e006efc8f7a3b5c3deaee8289a72511c35070e3cfe'
    raw = ROOT/'literature/downloads/dna.scale';assert hashlib.sha256(raw.read_bytes()).hexdigest()==provenance['raw_sha256']
    for name,digest in provenance['cache_files_sha256'].items():
        file = ROOT/'literature/downloads/libsvm-cache/libsvm'/name
        assert hashlib.sha256(file.read_bytes()).hexdigest()==digest
    first = json.loads((source/'first_attempt/failures.json').read_text('utf-8'))
    assert len(first)==1 and first[0]['dataset']=='DNA'
    assert 'CERTIFICATE_VERIFY_FAILED' in (source/'first_attempt/DNA.log').read_text('utf-8')
    out = ROOT/'results/application_precheck_analysis_v1';out.mkdir(parents=True,exist_ok=True)
    table = pd.DataFrame(rows);table.to_csv(out/'resources.csv',index=False)
    audit = dict(datasets=3,objective_calls=18,cv_fold_solves=90,test_method_calls=0,
        all_prescribed_points_paid=True,repeated_point_deterministic_in_all_tasks=True,
        sources_and_journals_verified=True,formal_application_labels=0,
        initial_data_transport_failure_preserved=True,no_solver_or_data_substitution=True,
        shared_timing_not_exclusive=True)
    (out/'audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    (out/'source_hashes.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
    text = '# LassoBench资源与确定性预检结果\n\n三个原任务的预定18次配置评价均已完成，90个默认CV折求解，0次test调用。重复全0配置的两个目标值在三任务均逐位相同。未产生正式应用优化标签。\n\n'
    text += table.round(6).to_markdown()+'\n\nDNA首次因Python默认证书链无法下载而停止，未产生DNA目标标签。原错误完整归档在first_attempt。随后使用certifi官方信任根且保持TLS验证，从原LIBSVM官方地址取得相同dna.scale文件；未修改目标、容差、划分或替代数据。原库解码产生2000×180矩阵，原始字节与缓存均核对SHA256。\n\n'
    text += '这些耗时与正式GP/TuRBO共享负载，不是独占应用成本，也不能用18次预检代替20重复×500应用优化。60/100/180维的2D+20启动可纳入500预算；300维扩展启动620次，需要另行预定预算。应用最优未知，最终报告原验证损失。作者合成构造器预计算固定测试oracle常数，但优化目标不使用测试表现；这一实现边界继续披露。\n'
    text += '下一步在当前独占成本流程结束后，冻结完整应用机制问题与运行实现，保留原任务、重复和预算；不得根据预检目标值删减任务或调整参数。\n'
    (ROOT/'docs/LassoBench资源预检结果.md').write_text(text,encoding='utf-8')
    print(json.dumps(audit,indent=2))


if __name__=='__main__':main()
