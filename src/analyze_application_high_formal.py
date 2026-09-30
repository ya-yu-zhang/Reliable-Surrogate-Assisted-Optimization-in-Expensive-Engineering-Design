"""Complete 160-run high extension audit; descriptive paired interval, no new test."""
import hashlib,json
from pathlib import Path
import numpy as np
import pandas as pd
from .application_journal_audit import audit_journal
from .core import METHODS

ROOT=Path(__file__).resolve().parents[1]


def main():
    config=json.loads((ROOT/'configs/application_high_formal.json').read_text('utf-8'))
    source=ROOT/config['out'];status=json.loads((source/'status.json').read_text('utf-8'))
    assert status['stage']=='complete' and status['completed']==status['expected']==160 and status['failed']==0
    assert json.loads((source/'failures.json').read_text('utf-8'))==[]
    frozen=json.loads((ROOT/config['freeze_manifest']).read_text('utf-8'))
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==v for n,v in frozen.items())
    assert json.loads((source/'manifest.json').read_text('utf-8'))['frozen_sources']==frozen
    runtime=json.loads((ROOT/config['runtime_manifest']).read_text('utf-8'))
    expected={(r,m) for r in range(20) for m in config['methods']};seen=set();rows=[];curves=[];hashes={};identity=None
    for file in sorted(source.glob('*/summary.json')):
        directory=file.parent;summary=json.loads(file.read_text('utf-8'));sig=summary['signature']
        key=(sig['rep'],sig['method']);assert key in expected and key not in seen;seen.add(key)
        assert sig==dict(dataset='synt_high',dim=300,rep=key[0],method=key[1],budget=1000,data_seed=42,
            seed=100000*300+1000*4+10*42+key[0],packages=runtime['packages'],frozen_sources=frozen)
        assert summary['algorithm_evaluations']==1000 and summary['cv_fold_solves']==5000
        assert summary['test_method_calls']==summary['post_completion_test_fits']==1
        events=audit_journal(directory,summary)
        current=(summary['data_hashes'],summary['fold_hash'])
        if identity is None:identity=current
        else:assert identity==current
        labels=[v['y'] for v in events[2::2]];index=int(np.argmin(labels))
        post=json.loads((directory/'post_completion_test.json').read_text('utf-8'))
        assert post['algorithm_evaluations']==1000 and post['selected_evaluation']==index+1
        assert post['selected_config']==summary['best_config'] and post['best_validation_loss']==labels[index]
        assert post['metrics']==summary['test_metrics'] and post['test_method_calls']==1
        assert post['optimization_labels_sha256']==hashlib.sha256((directory/'events.jsonl').read_bytes()).hexdigest()
        assert all(np.isfinite(v) for v in post['metrics'].values())
        row=dict(rep=key[0],method=key[1],best_validation_loss=summary['best_validation_loss'],
                 best_evaluation=index+1,test_mspe=post['metrics']['mspe'],test_fscore=post['metrics']['fscore'],
                 objective_seconds=summary['objective_seconds'],optimization_seconds=summary['optimization_seconds'],
                 peak_memory_gib=summary['process_peak_working_set_bytes']/2**30,
                 exact_duplicate_calls=summary['exact_duplicate_calls'])
        if key[1] in METHODS:
            selected=[];variant=METHODS[key[1]][0]
            for pre,label in zip(events[1::2],events[2::2]):
                if pre['t']>620:
                    delta=(label['y']-pre['H'])/pre['scale']
                    selected.append(dict(failure=float(label['upper_failure']),margin=pre['margin'],
                        qloss=delta*(.9-float(delta<0)),declared=float(pre['declared']),false=float(label['false_claim']),
                        exploration=float(pre['mode']=='explore'),neff=pre['neff'],fallback=float(pre['calibrator']!=variant)))
            assert len(selected)==380;table=pd.DataFrame(selected);claims=int(table.declared.sum());false=int(table.false.sum())
            row.update(selected_evaluations=380,claims=claims,false_claims=false,fdp=false/claims if claims else np.nan,
                       **{'selected_'+c:table[c].mean() for c in table.columns})
        rows.append(row);best=np.minimum.accumulate(labels)
        for fraction in np.linspace(0,1,101):
            n=max(1,int(np.ceil(fraction*1000)));curves.append(dict(rep=key[0],method=key[1],
                budget_fraction=float(fraction),evaluation=n,best_validation_loss=best[n-1]))
        for name in ['summary.json','events.jsonl','post_completion_test.json','candidate_pools.npz']:
            path=directory/name;hashes[path.relative_to(ROOT).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
    assert seen==expected and len(hashes)==640
    frame=pd.DataFrame(rows);out=ROOT/'results/application_high_analysis_v1';out.mkdir(parents=True,exist_ok=True)
    frame.to_csv(out/'runs.csv',index=False);pd.DataFrame(curves).to_csv(out/'convergence.csv',index=False)
    frame.groupby('method')[['best_validation_loss','test_mspe','test_fscore']].agg(
        ['median',lambda s:s.quantile(.25),lambda s:s.quantile(.75)]).to_csv(out/'endpoint_iqr.csv')
    a=frame[frame.method=='PEM_T'].set_index('rep').best_validation_loss
    b=frame[frame.method=='fixed01'].set_index('rep').best_validation_loss
    delta=(a-b).sort_index().to_numpy();rng=np.random.default_rng(config['bootstrap_seed']+4)
    estimates=np.median(delta[rng.integers(0,20,(config['bootstrap_replicates'],20))],axis=1)
    effect=dict(dataset='synt_high',median_raw_loss_difference=float(np.median(delta)),
                ci_low=float(np.quantile(estimates,.025)),ci_high=float(np.quantile(estimates,.975)),
                losses=int(sum(delta>0)),wins=int(sum(delta<0)),ties=int(sum(delta==0)),
                p_value=None,holm_p=None,descriptive_only=True,conditional_fixed_data_analysis=True)
    pd.DataFrame([effect]).to_csv(out/'descriptive_paired_difference.csv',index=False)
    audit=dict(runs=160,algorithm_evaluations=int(frame.shape[0]*1000),cv_fold_solves=int(frame.shape[0]*5000),
        post_completion_test_calls=160,complete_design=True,pre_information_verified=True,
        bounds_and_management_replayed=True,unknown_optimum_not_imputed=True,test_results_not_in_optimizer=True,
        statistical_tests_added=0,not_added_to_primary_three_test_family=True,conditional_fixed_data_analysis=True,
        raw_file_hashes=len(hashes),descriptive_interval_bootstrap_replicates=config['bootstrap_replicates'])
    (out/'audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    (out/'source_hashes.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
    print(json.dumps(audit,indent=2))


if __name__=='__main__':main()
