"""One deterministic conversion of saved v2 certificates; no new rollout run."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics
import time

from .rollout_v2_intervals import I, VERSION
from .rollout_v2_solver import domain_read
from .rollout_regional_enclosure import regional_enclosure, weighted_stability_radius


ROOT = Path(__file__).resolve().parents[1]
BASE = '58f539c2d0738b20c7d0d4889fe8d808a03a3019'
PARENT = '762db8114da07e8fe84c02019f84ef153e6a4478'
SOURCE = ROOT/'results/positive_rollout_v2_20261015'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, data):
    Path(path).write_text(json.dumps(data, indent=2, allow_nan=False)+'\n')


def run(out):
    out.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((SOURCE/'RELEASE_MANIFEST.json').read_text())
    inputs = {str((SOURCE/'RELEASE_MANIFEST.json').relative_to(ROOT)):sha(SOURCE/'RELEASE_MANIFEST.json')}
    hashes = manifest['result_files_sha256']
    local_files = sorted((SOURCE/'certificates').glob('*__local.json'))
    assert len(local_files) == 43
    for p in local_files:
        stem = p.name.removesuffix('__local.json')
        for target in [p, SOURCE/'posterior'/f'{stem}.json', SOURCE/'references'/f'{stem}.json']:
            rel = str(target.relative_to(ROOT))
            assert sha(target) == hashes[rel], rel
            inputs[rel] = hashes[rel]
    sources = ['src/rollout_regional_enclosure.py', 'src/postprocess_rollout_regional_enclosure.py',
               'tests/test_rollout_regional_enclosure.py',
               'paper/engineering_optimization/contribution_closure_20261015/REGIONAL_VALUE_CLOSURE_PLAN.md']
    # Record dependencies without changing the earlier freeze or its results.
    for rel in ['src/rollout_v2_intervals.py','src/rollout_v2_solver.py']:
        assert sha(ROOT/rel) == manifest['core_source_sha256'][rel]
    config = dict(scientific_baseline=BASE,parent_commit=PARENT,
        kind='post_hoc_existing_certificate_transformation_not_new_optimization_experiment',
        input_sha256=inputs,source_sha256={p:sha(ROOT/p) for p in sources},
        frozen_dependency_sha256={p:manifest['core_source_sha256'][p] for p in
            ['src/rollout_v2_intervals.py','src/rollout_v2_solver.py']},
        MPFR_version=VERSION,MPFR_bits=192,normal_window=[-8,8],
        conditional_reward_evaluations=0,GP_reconstructions=0,
        new_physical_evaluations=0,new_bound_queries=0,new_hyperparameter_fits=0,
        retries=0,replacements=0,new_independent_samples=0,
        end_to_end_solver_rerun=False,timing_comparison=False,
        original_decisions_and_times_unchanged=True)
    save(out/'input_freeze.json', config)
    began=time.perf_counter()
    states, reductions, radius_reductions = [],[],[]
    transformed_branches=retained_branches=containment_failures=0
    for p in local_files:
        stem=p.name.removesuffix('__local.json')
        record=json.loads(p.read_text())
        posterior=json.loads((SOURCE/'posterior'/f'{stem}.json').read_text())
        references=json.loads((SOURCE/'references'/f'{stem}.json').read_text())
        assert record['reader']['accepted'] and record['status']=='accepted'
        intervals,details={},{}
        for b, cert in record['certificates'].items():
            old=record['reader']['intervals'][b]
            if cert['fixed'] is None:
                intervals[b]=old
                details[b]=dict(route='unchanged_complete_projection',interval=old)
                retained_branches+=1
                continue
            model=posterior['models'][b]
            domain=domain_read(record['local_domains'][b])
            converted=regional_enclosure(model,domain,cert,old)
            intervals[b]=converted['interval']
            converted['route']='regional_conversion_of_checked_fixed_leaves'
            converted['original_interval']=old
            converted['old_event_radius']=record['event_radii'][b]
            converted['weighted_event_radius']=weighted_stability_radius(
                model,domain,record['event_radii'][b])
            old_width=I(old).width();new_width=I(intervals[b]).width()
            converted['width_reduction_fraction']=0. if old_width==0 else (old_width-new_width)/old_width
            reductions.append(converted['width_reduction_fraction'])
            if converted['old_event_radius']>0:
                radius_reductions.append((converted['old_event_radius']-converted['weighted_event_radius'])/converted['old_event_radius'])
            details[b]=converted
            transformed_branches+=1
        selected=record['selected']
        regret=max([0.]+[(I(v[1])-intervals[selected][0]).hi
                        for b,v in intervals.items() if b!=selected])
        delta=record['delta_lower']
        bad=[b for b,v in intervals.items()
             if not v[0]<=references[b]['point_parameter_value']<=v[1]]
        containment_failures+=len(bad)
        states.append(dict(state=stem,selected=selected,regret_upper=regret,
            delta_lower=delta,accepted=regret<=delta,intervals=intervals,
            ordinary_reference_failures=bad,branches=details))
    summary=dict(scientific_baseline=BASE,parent_commit=PARENT,
        analysis_status='complete',post_hoc=True,independent_validation=False,
        source_states=len(states),source_branches=transformed_branches+retained_branches,
        transformed_fixed_branches=transformed_branches,
        unchanged_complete_projection_branches=retained_branches,
        accepted_unchanged_selections=sum(s['accepted'] for s in states),
        ordinary_reference_checks=sum(len(s['intervals']) for s in states),
        ordinary_reference_containment_failures=containment_failures,
        strict_width_reduction_branches=sum(x>0 for x in reductions),
        width_reduction_fraction=dict(min=min(reductions),median=statistics.median(reductions),max=max(reductions)),
        weighted_radius_reduction_fraction=dict(min=min(radius_reductions),median=statistics.median(radius_reductions),max=max(radius_reductions)),
        elapsed_postprocessing_seconds=time.perf_counter()-began,
        counters={k:0 for k in ['new_GP_reconstructions','new_conditional_reward_evaluations',
            'new_full_projections','new_physical_evaluations','new_bound_queries',
            'new_hyperparameter_fits','physical_retries','physical_replacements','new_independent_samples']},
        prior_v2_projection_counts_and_timing_unchanged=True,
        fewer_projections_or_time_saving_demonstrated_by_postprocessing=False,
        original_v2_decisions_changed=False,engineering_policy_superiority_demonstrated=False,
        journal_acceptance_or_originality_sufficiency_certified=False,
        states=states)
    summary['all_checks_passed']=(summary['accepted_unchanged_selections']==43 and
        containment_failures==0 and transformed_branches+retained_branches==114)
    save(out/'analysis.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k!='states'},indent=2))
    if not summary['all_checks_passed']:
        raise ArithmeticError('Postprocessing failed; retain record and stop without adjustment')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    run(args.out)
