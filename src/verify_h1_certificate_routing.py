"""Read-only verification of domain-cover saturation and scalar routing.

No coefficient reconstruction, bound query, physical solve or new optimization
sample. The already verified complete interval sets are the coverage evidence.
"""
from pathlib import Path
import csv
from fractions import Fraction
import hashlib
import json
from .h1_certificate_routing import binary,no_better_certificate
from .certified_affine_envelope import coefficient_bands
from .filtered_exact_action_sets import integer_envelope_from_bands


def run(root):
    gp=root/'gp_attachment/results/engineering_optimization_gp_reachability_v1'
    csvpath=root/'gp_attachment/paper/engineering_optimization/gp_reachability_20261013/branch_results.csv'
    records=list(csv.DictReader(csvpath.open()))
    source={(r['dataset'],r['state'],r['branch'],r['range']):r for r in records}
    checkpath=root/'results/gp_envelope_acceleration_20261014/H1_recheck.csv'
    check={(r['dataset'],r['state'],r['branch'],r['range']):r for r in csv.DictReader(checkpath.open())}
    rows=[];inputs=[csvpath,checkpath]
    for path in sorted((root/'results/gp_envelope_acceleration_20261014/certificates').glob('*.json')):
        original=gp/'construction'/path.name
        item=json.loads(path.read_text());prior=json.loads(original.read_text());meta=item['metadata']
        inputs.extend([path,original])
        for branch,modes in item['branches'].items():
            rec=prior['branches'][branch]
            for mode,result in modes.items():
                key=(meta['dataset'],meta['state'],branch,mode);r=source[key]
                domain=Fraction(0) if mode=='nonnegative' else binary(rec['pending_lower'])
                initial=binary(r['initial']);pending=binary(rec['pending_lower'])
                threshold=binary(r['completed_H1_baseline'])-binary(r['margin'])*initial
                intervals={int(k):(Fraction(int(v[0][0]),int(v[0][1])),
                                  None if v[1] is None else Fraction(int(v[1][0]),int(v[1][1])))
                           for k,v in result['exact_intervals'].items()}
                assert min(lo for lo,_ in intervals.values())==domain
                covered_to=domain
                for lo,hi in sorted(intervals.values(),key=lambda pair:pair[0]):
                    if covered_to is None:break
                    assert lo<=covered_to,'Gap in closed-domain coverage'
                    covered_to=None if hi is None else max(covered_to,hi)
                assert covered_to is None,'Missing unbounded domain tail'
                next_values=[binary(prior['raw_pool_lowers'][rec['eligible_pool_indices'][i]]) for i in result['indices']]
                original_joint=min(initial,*(min(max(pending,intervals[i][0]),value)
                                       for i,value in zip(result['indices'],next_values)))
                saturated=min(initial,max(pending,domain),min(next_values))
                assert original_joint==saturated
                assert float(saturated)==float(check[key]['exact_joint_lower_float'])
                calls=[]
                def reader():
                    # The oracle above is verification overhead, not work
                    # attributed to routing. The lazy production callback
                    # really contains the action-set operation it can avoid.
                    calls.append(1)
                    c=rec['coefficients']
                    bands=coefficient_bands(c['slope'],c['intercept'],c['slope_error'],c['intercept_error'])
                    actions=integer_envelope_from_bands(*bands,response_lower=float(domain))
                    return min(binary(prior['raw_pool_lowers'][rec['eligible_pool_indices'][i]])
                               for i in actions['indices'])
                routed=no_better_certificate(initial,threshold,pending,domain,reader)
                assert routed['certified']==(original_joint>=threshold)
                rows.append({'dataset':meta['dataset'],'state':meta['state'],'branch':branch,'range':mode,
                             'baseline_branch':r['baseline_branch']=='True',
                             'domain_endpoint_covered':True,'saturation_identity_exact':True,
                             'scalar_predicate_unchanged':True,'action_set_callback_calls':len(calls),
                             'certified':routed['certified'],'route':routed['route']})
    assert len(rows)==228
    out=root/'results/h1_certificate_routing_20261015';out.mkdir(parents=True,exist_ok=True)
    with (out/'case_results.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    nonbaseline=[r for r in rows if not r['baseline_branch']]
    summary={'baseline':'58f539c2d0738b20c7d0d4889fe8d808a03a3019',
      'all_case_count':len(rows),'nonbaseline_case_count':len(nonbaseline),
      'domain_cover_and_saturation_identity_exact_in_all_cases':True,
      'scalar_predicate_equal_in_all_cases':True,
      'nonbaseline_scalar_requests_early_rejected':sum(not r['action_set_callback_calls'] for r in nonbaseline),
      'all_scalar_requests_early_rejected':sum(not r['action_set_callback_calls'] for r in rows),
      'nonbaseline_action_set_callback_calls':sum(r['action_set_callback_calls'] for r in nonbaseline),
      'new_H1_positive_judgments':0,'H5_or_independent_gate_changed':False,
      'new_physical_evaluations':0,'new_bound_queries':0,'new_GP_hyperparameter_fits':0,
      'new_independent_optimization_samples':0,'remaining_witness_attempts':0,
      'scope':'Scalar no-better certificate predicate only; cannot replace requested full sets or infer actual inferiority, tie, better or optimizer-performance benefit.',
      'cost_interpretation':'Executed routing calls no action-set callback in rejected cases. Historical bound/physics cost is not refunded; no complete deployment or physical savings measured.',
      'source_hashes':{n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in [
        'src/h1_certificate_routing.py','src/verify_h1_certificate_routing.py','tests/test_h1_certificate_routing.py']},
      'input_hashes':{p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}}
    (out/'analysis.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ['input_hashes','source_hashes']},indent=2))
    return summary


if __name__=='__main__':run(Path(__file__).resolve().parents[1])
