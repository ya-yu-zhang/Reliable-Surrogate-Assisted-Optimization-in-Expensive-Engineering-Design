"""Diagnose two output contracts using frozen coefficients only.

Nominal means use the stored numerical centers, not a true-physics or exact-GP
oracle. Band outputs are read from the already verified Fraction certificates.
No GP reconstruction, proof replay, timing, bound query or physical evaluation.
"""
from pathlib import Path
from fractions import Fraction
from collections import Counter
import csv
import hashlib
import json
import statistics
from .filtered_exact_action_sets import integer_envelope_from_bands
from .h1_certificate_routing import binary

BASELINE='58f539c2d0738b20c7d0d4889fe8d808a03a3019'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def rational(value):return Fraction(int(value[0]),int(value[1]))


def encode(value):
    if isinstance(value,Fraction):return [str(value.numerator),str(value.denominator)]
    if isinstance(value,dict):return {str(k):encode(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [encode(v) for v in value]
    return value


def run(root):
    gp=root/'gp_attachment/results/engineering_optimization_gp_reachability_v1'
    out=root/'results/nominal_band_diagnostic_20261015'
    declared=out/'PREDECLARED_CASES.json'
    choices=json.loads(declared.read_text())['cases']
    status=json.loads((gp/'construction_status.json').read_text())
    counts=Counter();rows=[];details={};widenings=[];inputs=[declared,gp/'construction_status.json']
    # This phase reads no response/grade CSVs; the two examples were fixed first.
    for name,expected in sorted(status['files_sha256'].items()):
        path=gp/'construction'/name
        assert sha(path)==expected
        oldpath=root/'results/gp_envelope_acceleration_20261014/certificates'/name
        inputs.extend([path,oldpath]);data=json.loads(path.read_text());prior=json.loads(oldpath.read_text())
        meta=data['metadata'];assert not data['future_responses_exposed']
        for branch,rec in data['branches'].items():
            assert not rec['first_response_exposed']
            c=rec['coefficients'];a,b=c['slope'],c['intercept']
            for mode in ['nonnegative','trial_lower']:
                domain=0. if mode=='nonnegative' else rec['pending_lower']
                nominal=integer_envelope_from_bands(a,b,a,b,response_lower=domain)
                band_record=prior['branches'][branch][mode]
                bands={int(k):(rational(v[0]),None if v[1] is None else rational(v[1]))
                       for k,v in band_record['exact_intervals'].items()}
                center=nominal['exact_intervals'];assert set(center)<=set(bands)
                lower_changed=upper_changed=interval_changed=0
                for i,(lo,hi) in center.items():
                    blo,bhi=bands[i];assert blo<=lo
                    assert bhi is None or (hi is not None and hi<=bhi)
                    lower_changed+=blo!=lo;upper_changed+=bhi!=hi;interval_changed+=(blo,bhi)!=(lo,hi)
                    if blo!=lo:widenings.append(float((lo-blo)/max(Fraction(1),abs(lo))))
                    if hi is not None and bhi is not None and bhi!=hi:
                        widenings.append(float((bhi-hi)/max(Fraction(1),abs(hi))))
                row={'dataset':meta['dataset'],'state':meta['state'],'branch':branch,'range':mode,
                  'eligible':len(a),'nominal_kept':len(center),'band_kept':len(bands),
                  'same_indices':set(center)==set(bands),'extra_band_actions':len(set(bands)-set(center)),
                  'shared_actions':len(center),'shared_intervals_changed':interval_changed,
                  'lower_endpoints_changed':lower_changed,'upper_endpoints_changed':upper_changed}
                rows.append(row)
                for k in ['extra_band_actions','shared_actions','shared_intervals_changed','lower_endpoints_changed','upper_endpoints_changed']:counts[k]+=row[k]
                counts['same_index_cases']+=row['same_indices'];counts['changed_interval_cases']+=interval_changed>0
                selected=choices[meta['dataset']]
                if name==selected['file'] and branch==selected['branch']:
                    details[meta['dataset'],mode]={'file':name,'state':meta['state'],'branch':branch,
                      'range':mode,'initial':meta['initial'],'pending_bound':rec['pending_lower'],
                      'domain':domain,'eligible':len(a),'nominal_indices':nominal['indices'],
                      'band_indices':band_record['indices'],
                      'raw_pool_indices':[rec['eligible_pool_indices'][i] for i in band_record['indices']],
                      'nominal_exact_intervals':center,'band_exact_intervals':bands,
                      'summary':row}
    assert len(rows)==228
    # Existing paid comparator information is read only after all nominal sets.
    grades=root/'gp_attachment/paper/engineering_optimization/gp_reachability_20261013/branch_results.csv'
    inputs.append(grades)
    lookup={(r['dataset'],r['state'],r['branch'],r['range']):r for r in csv.DictReader(grades.open())}
    cases=[]
    for (dataset,mode),case in sorted(details.items()):
        r=lookup[dataset,case['state'],case['branch'],mode]
        initial=binary(r['initial']);threshold=binary(r['completed_H1_baseline'])-binary(r['margin'])*initial
        cap=min(initial,max(binary(case['pending_bound']),binary(case['domain'])))
        case.update({'dataset':dataset,'baseline_branch':r['baseline_branch']=='True',
          'completed_H1_baseline':r['completed_H1_baseline'],'margin':r['margin'],
          'threshold_exact':threshold,'threshold_float':float(threshold),'pending_cap_exact':cap,
          'cap_below_threshold':cap<threshold,'original_category':r['reachable_category'],
          'stored_next_action_included':r['actual_next_action_included']=='True'})
        cases.append(case)
    with (out/'case_results.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    (out/'engineering_cases.json').write_text(json.dumps(encode(cases),indent=2,allow_nan=False)+'\n')
    summary={'baseline':BASELINE,'cases':len(rows),'branches':114,'counts':dict(counts),
      'all_nominal_sets_and_intervals_contained_in_band_outputs':True,
      'median_normalized_finite_endpoint_widening':statistics.median(widenings) if widenings else 0.,
      'max_normalized_finite_endpoint_widening':max(widenings,default=0.),
      'normalization':'Endpoint widening divided by max(1, abs(nominal endpoint)); not a true-GP or physical error.',
      'interpretation':'Different contracts, not a same-output speed comparison; zero extra indices means no observed action rescue may be claimed.',
      'examples_selected_before_outputs':True,'selected_case_count':2,'selected_domain_case_count':4,
      'new_physical_evaluations':0,'new_bound_queries':0,'new_GP_reconstruction':0,'new_GP_hyperparameter_fits':0,
      'new_independent_optimization_samples':0,'new_independent_samples':0,'remaining_witness_attempts':0,
      'original_gates_changed':False,'existing_strong_comparison_or_proof_replay_rerun':False,
      'source_sha256':sha(Path(__file__)),
      'input_hashes':{p.relative_to(root).as_posix():sha(p) for p in inputs}}
    (out/'analysis.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='input_hashes'},indent=2))
    for case in cases:
        print(json.dumps({k:v for k,v in case.items() if k in ['dataset','state','branch','range','baseline_branch','eligible','nominal_indices','band_indices','pending_bound','completed_H1_baseline','threshold_float','cap_below_threshold','original_category']}))
    return summary


if __name__=='__main__':run(Path(__file__).resolve().parents[1])
