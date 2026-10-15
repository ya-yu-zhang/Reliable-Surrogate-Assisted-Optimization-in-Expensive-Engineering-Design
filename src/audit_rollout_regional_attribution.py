"""Arithmetic attribution using the saved transformation only; no integrals."""
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import statistics

ROOT=Path(__file__).resolve().parents[1]
DIRECTORY=ROOT/'results/regional_value_closure_20261015'


def main():
    source=DIRECTORY/'analysis.json'
    target=DIRECTORY/'mechanism_attribution.json'
    if target.exists():
        raise FileExistsError('Preserve the first attribution record')
    data=json.loads(source.read_text())
    rows=[]
    for state in data['states']:
        for branch,row in state['branches'].items():
            if row['route']=='unchanged_complete_projection':
                continue
            old=list(map(Fraction,row['original_interval']))
            new=list(map(Fraction,row['interval']))
            base_low=max(old[0],Fraction(row['baseline'][0]))
            original_width=old[1]-old[0]
            baseline_width=old[1]-base_low
            regional_width=new[1]-new[0]
            assert 0<=regional_width<=baseline_width<=original_width
            rows.append(dict(state=state['state'],branch=branch,
                baseline_alone_tightens=baseline_width<original_width,
                regional_addition_tightens=regional_width<baseline_width,
                extra_fraction_of_original_width=float((baseline_width-regional_width)/original_width),
                extra_fraction_of_baseline_width=float((baseline_width-regional_width)/baseline_width)
                    if baseline_width else 0.))
    def stats(key):
        v=[r[key] for r in rows]
        return dict(min=min(v),median=statistics.median(v),max=max(v))
    result=dict(analysis_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        audit_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        operation='exact_rational_width_comparison_of_saved_binary_endpoints',
        rows=len(rows),baseline_alone_tightens=sum(r['baseline_alone_tightens'] for r in rows),
        regional_addition_tightens=sum(r['regional_addition_tightens'] for r in rows),
        extra_fraction_of_original_width=stats('extra_fraction_of_original_width'),
        extra_fraction_of_baseline_width=stats('extra_fraction_of_baseline_width'),
        no_new_integrals_or_GP_or_physics=True,branches=rows)
    target.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='branches'},indent=2))


if __name__=='__main__':
    main()
