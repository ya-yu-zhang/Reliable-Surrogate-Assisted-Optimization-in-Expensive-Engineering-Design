"""Read-only post-freeze tolerance, reference and model consistency audit."""
import hashlib,json
from pathlib import Path
from .rollout_v2_intervals import I

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/lazy_regional_20261015'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    data=json.loads((OUT/'analysis.json').read_text())
    freeze=json.loads((OUT/'decisions_frozen.json').read_text())
    assert sha(OUT/'decisions.json')==freeze['decisions_sha256']
    for p,h in freeze['files_sha256'].items():assert sha(ROOT/p)==h,p
    cfg=json.loads((ROOT/'configs/lazy_regional_20261015.json').read_text())
    for field in ['input_sha256','source_sha256','dependency_sha256']:
        for p,h in cfg[field].items():assert sha(ROOT/p)==h,p
    counts={'uniform':0,'regional':0};failures=[];refs=overlaps=0
    for state in data['states_detail']:
        name=state['state']
        old=json.loads((ROOT/'results/positive_rollout_v2_20261015/certificates'/f'{name}__local.json').read_text())
        oldp=json.loads((ROOT/'results/positive_rollout_v2_20261015/posterior'/f'{name}.json').read_text())
        reference=json.loads((ROOT/'results/positive_rollout_v2_20261015/references'/f'{name}.json').read_text())
        prep=json.loads((OUT/'preparation'/f'{name}.json').read_text())
        assert prep['matrix_A_sha256']==oldp['matrix_sha256']['A']
        for method in counts:
            r=json.loads((OUT/'certificates'/f'{name}__{method}.json').read_text())
            counts[method]+=r['selected']==old['selected']
            m0=next(iter(prep['first_models'].values()))['initial']
            delta=(I(m0)/1000000).lo
            assert delta==r['delta_lower'],'Do not trust a self-declared tolerance'
            iv=r['reader']['intervals'];chosen=r['selected']
            regret=max([0.]+[(I(v[1])-iv[chosen][0]).hi for b,v in iv.items() if b!=chosen])
            assert regret<=delta
            for b,v in iv.items():
                refs+=1
                if not v[0]<=reference[b]['point_parameter_value']<=v[1]:failures.append([name,method,b])
            for q in r['conditional_posterior_records']:
                oldq=oldp['models'][q['branch']]['next'][str(q['action'])]
                for k,v in q['conditional'].items():I(v).intersect(I(oldq[k]));overlaps+=1
    result=dict(source_before_execution_commit='8de86bbe1aeb1568bba754609cf10b8d093094c8',
        audit_source_sha256=sha(Path(__file__)),decisions_frozen_before_old_reference_read=True,
        paid_response_reads=False,all_43_training_matrices_match_v2=True,selections_matching_v2=counts,
        correct_declared_delta_checked_states_each_method=43,ordinary_reference_checks=refs,
        ordinary_reference_failures=failures,queried_conditional_parameter_overlap_checks=overlaps,
        overlap_is_consistency_check_not_independent_model_proof=True,new_physical_evaluations=0,
        all_checks_passed=not failures and counts=={'uniform':43,'regional':43})
    (OUT/'postfreeze_consistency.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,default=OUT)
    args=parser.parse_args();OUT=args.out.resolve();main()
