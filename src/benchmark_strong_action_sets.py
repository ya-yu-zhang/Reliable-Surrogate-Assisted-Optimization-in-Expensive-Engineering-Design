"""Frozen 228-case exact-output comparison; zero new engineering evaluations.

This recovers a lost posthoc implementation. Previous unpreserved timings are
not imported as evidence. Coefficients, filtering and independent checking are
all charged; historical physical and bound acquisition are separately retained.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import importlib.metadata
import json
import statistics
import time
import numpy as np
from sklearn.gaussian_process.kernels import ConstantKernel,Matern
from .certified_affine_envelope import coefficient_bands,exact_outer_from_bands,check_exclusion
from .filtered_exact_action_sets import integer_envelope_from_bands,filtered_pairwise_from_bands
from .gp_action_reachability import coefficient_enclosures
from .verify_and_benchmark_gp_envelope import locate,future_pool,exact_json

METHODS={'fraction_envelope':exact_outer_from_bands,
         'filtered_pairwise':filtered_pairwise_from_bands,
         'integer_envelope':integer_envelope_from_bands}
BASELINE='58f539c2d0738b20c7d0d4889fe8d808a03a3019'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path,value):
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def run(root,out,repeats=3):
    out.mkdir(parents=True,exist_ok=True)
    gp=root/'gp_attachment/results/engineering_optimization_gp_reachability_v1'
    plan=json.loads((gp/'plan.json').read_text())
    status=json.loads((gp/'construction_status.json').read_text())
    witness=json.loads((gp/'witness_status.json').read_text())
    assert witness['complete'] and witness['new_physics_attempts']==2
    assert status['complete'] and status['baseline_commit']==BASELINE
    assert not status['future_responses_exposed']
    assert sha(gp/'plan.json')==status['plan_sha256']
    for n,h in {**plan['source_hashes'],**plan['witness_frozen_hashes']}.items():
        assert sha(locate(root,n))==h,n
    for n,h in status['witness_files_sha256'].items():assert sha(gp/n)==h
    design={'baseline':BASELINE,'type':'posthoc reconstruction of previously lost computational increment',
      'methods':list(METHODS),'contexts':43,'branches':114,'domains':['nonnegative','trial_lower'],
      'repeats':repeats,'order':'rotate by case index plus repeat','filtered_block_size':64,
      'previous_unpreserved_timings_used_as_evidence':False,
      'development_data_already_seen':True,'new_independent_samples':0,
      'new_physical_evaluations':0,'new_bound_queries':0,'new_GP_hyperparameter_fits':0,
      'remaining_witness_attempts':0,'source_hashes':{n:sha(root/n) for n in [
          'src/filtered_exact_action_sets.py','src/benchmark_strong_action_sets.py',
          'src/certified_affine_envelope.py','tests/test_filtered_exact_action_sets.py']},
      'construction_input_hashes':status['files_sha256'],
      'runtime':{n:importlib.metadata.version(n) for n in ['numpy','scipy','scikit-learn']},
      'cost_scope':'Coefficient reconstruction, filtering and independent proof checking; excludes I/O, grading, physics and historical bound acquisition.'}
    write(out/'DESIGN.json',design)
    rows,hashes=[],[]
    for state_index,name in enumerate(sorted(status['files_sha256'])):
        path=gp/'construction'/name
        assert sha(path)==status['files_sha256'][name]
        item=json.loads(path.read_text());meta=item['metadata']
        assert not item['future_responses_exposed']
        cfg=plan['pool_configs'][meta['dataset']];pool,seed=future_pool(meta,cfg)
        assert seed==item['pool_seed']
        assert hashlib.sha256(pool.tobytes()).hexdigest()==item['raw_pool_sha256']
        source=('results/engineering_optimization_common_continuation_v1/plans/'+meta['state']+'.json'
                if meta['dataset']=='archived_common_mean' else
                f"results/engineering_optimization_budget_audit_v1/block_{meta['block']}/{meta['state']}_plan.json")
        initial=json.loads(locate(root,source).read_text())
        assert not {'trajectories','control_curves','branch_records','calibration'}.intersection(initial)
        old=json.loads((root/'results/gp_envelope_acceleration_20261014/certificates'/name).read_text())
        for branch,rec in item['branches'].items():
            assert not rec['first_response_exposed']
            coefficient_times=[]
            for _ in range(repeats):
                begin=time.perf_counter()
                X=np.vstack((np.array(initial['X']),np.array(initial['actions'][branch])))
                kernel=(ConstantKernel(1.,(.05,20))*Matern(np.full(19,.2),(.005,2.),nu=2.5)).clone_with_theta(np.array(initial['theta']))
                matrix=kernel(X);matrix[np.diag_indices_from(matrix)]+=cfg['alpha']
                cross=kernel(pool[np.array(rec['eligible_pool_indices'])],X)
                coeff=coefficient_enclosures(matrix,cross,np.array(initial['y']))
                bands=coefficient_bands(coeff['slope'],coeff['intercept'],coeff['slope_error'],coeff['intercept_error'])
                coefficient_times.append(time.perf_counter()-begin)
            assert hashlib.sha256(matrix.tobytes()).hexdigest()==rec['matrix_sha256']
            assert hashlib.sha256(cross.tobytes()).hexdigest()==rec['cross_sha256']
            for k in ['slope','intercept','slope_error','intercept_error']:
                assert np.array_equal(coeff[k],rec['coefficients'][k]),(name,branch,k)
            for mode in ['nonnegative','trial_lower']:
                domain=0. if mode=='nonnegative' else rec['pending_lower']
                construction={m:[] for m in METHODS};checking={m:[] for m in METHODS};outputs={}
                for rep in range(repeats):
                    keys=list(METHODS);shift=(len(rows)+rep)%3;keys=keys[shift:]+keys[:shift]
                    for method in keys:
                        begin=time.perf_counter();result=METHODS[method](*bands,response_lower=domain)
                        construction[method].append(time.perf_counter()-begin)
                        begin=time.perf_counter()
                        assert all(check_exclusion(*bands,p,domain) for p in result['excluded_proofs'])
                        checking[method].append(time.perf_counter()-begin);outputs[method]=result
                reference=outputs['fraction_envelope'];prior=old['branches'][branch][mode]
                assert reference['indices']==prior['indices']
                assert exact_json(reference['exact_intervals'])==prior['exact_intervals']
                row={'dataset':meta['dataset'],'state':meta['state'],'branch':branch,'range':mode,
                     'eligible':len(bands[0]),'kept':len(reference['indices']),
                     'proofs':len(reference['excluded_proofs']),
                     'coefficient_seconds':statistics.median(coefficient_times)}
                for method,result in outputs.items():
                    assert result['indices']==reference['indices'] and result['exact_intervals']==reference['exact_intervals']
                    assert len(result['indices'])+len(result['excluded_proofs'])==len(bands[0])
                    assert all(len(p)<=3 for p in result['excluded_proofs'])
                    row[method+'_construct_seconds']=statistics.median(construction[method])
                    row[method+'_check_seconds']=statistics.median(checking[method])
                    row[method+'_workflow_seconds']=(row['coefficient_seconds']+row[method+'_construct_seconds']+row[method+'_check_seconds'])
                    core={k:result[k] for k in ['indices','exact_intervals','excluded_proofs']}
                    hashes.append({'file':name,'branch':branch,'range':mode,'method':method,
                                   'sha256':hashlib.sha256(json.dumps(exact_json(core),sort_keys=True,separators=(',',':')).encode()).hexdigest()})
                row['scaled_coefficient_bits']=outputs['integer_envelope']['scaled_coefficient_max_bits']
                rows.append(row)
        # Write a recoverable partial CSV after every context, without publishing a completion claim.
        with (out/'case_results.csv').open('w',newline='') as stream:
            w=csv.DictWriter(stream,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        write(out/'certificate_core_hashes.json',hashes)
        print(json.dumps({'contexts_complete':state_index+1,'cases_complete':len(rows),'new_physical_evaluations':0}),flush=True)
    assert len(rows)==228 and sum(r['proofs'] for r in rows)==232564
    timings={m:{part:sum(r[m+'_'+part+'_seconds'] for r in rows) for part in ['construct','check','workflow']} for m in METHODS}
    summary={'baseline':BASELINE,'complete':True,'cases':228,'contexts':43,'branches':114,
      'all_exact_sets_and_intervals_equal':True,'exclusions_per_method_per_pass':232564,
      'all_exclusions_checked_in_every_repetition':True,'timing_repetitions':repeats,
      'coefficient_seconds_sum':sum(r['coefficient_seconds'] for r in rows),'timings':timings,
      'filtered_pairwise_over_integer_construction':timings['filtered_pairwise']['construct']/timings['integer_envelope']['construct'],
      'filtered_pairwise_over_integer_workflow':timings['filtered_pairwise']['workflow']/timings['integer_envelope']['workflow'],
      'integer_workflow_faster_cases':sum(r['integer_envelope_workflow_seconds']<r['filtered_pairwise_workflow_seconds'] for r in rows),
      'coefficient_bits_range':[min(r['scaled_coefficient_bits'] for r in rows),max(r['scaled_coefficient_bits'] for r in rows)],
      'cost_scope':design['cost_scope'],'new_physical_evaluations':0,'new_bound_queries':0,
      'new_GP_hyperparameter_fits':0,'new_independent_optimization_samples':0,'remaining_witness_attempts':0,
      'H1_H5_or_independent_study_gate_changed':False,'complete_physical_deployment_savings_demonstrated':False}
    write(out/'analysis.json',summary);print(json.dumps(summary,indent=2),flush=True)
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=Path('results/gp_strong_comparison_20261015'))
    parser.add_argument('--repeats',type=int,default=3)
    args=parser.parse_args();assert args.repeats>=1
    root=Path(__file__).resolve().parents[1];run(root,root/args.out,args.repeats)
