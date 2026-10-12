"""Zero-solver validation of amended mesh journals and fixed-design contrasts."""
import csv,json
from collections import Counter
import numpy as np
from .engineering_optimization_paired_mesh import ROOT,CONFIG,sha,write,density_field,transfer,normalized_geometry,effect_label
OUT=ROOT/'results/engineering_optimization_paired_mesh_recovery_v1'
DEST=ROOT/'paper/engineering_optimization/paired_mesh'
def main():
    cfg=json.loads(CONFIG.read_text());original=ROOT/cfg['out'];plan=json.loads((original/'plan.json').read_text())
    recovery=json.loads((OUT/'recovery_plan.json').read_text());status=json.loads((OUT/'run_status.json').read_text())
    responses=json.loads((OUT/'responses.json').read_text());raw=(OUT/'events.jsonl').read_bytes()
    assert status['complete'] and sha(raw)==status['journal_sha256']
    assert sha((original/'plan.json').read_bytes())==recovery['original_plan_sha256']
    assert sha((original/'events.jsonl').read_bytes())==recovery['original_journal_sha256']
    for p,d in {**plan['frozen_files'],**plan['source_files_sha256'],**recovery['frozen_recovery_files']}.items():assert sha((ROOT/p).read_bytes())==d,p
    cache={};pending=None;count=Counter();paid=0
    for line in (original/'events.jsonl').read_text().splitlines():
        r=json.loads(line)
        if r['event']=='pre':pending=r
        elif r['event']=='label':cache[pending['context'].split('/')[0]+':'+pending['density_sha256']]=r['y'];pending=None
    pending=None
    for line in raw.splitlines():
        r=json.loads(line)
        if r['event']=='pre':
            assert pending is None
            nx,ny=map(int,r['context'].split('/')[0].split('x'));mapping=r['context'].split('/')[1]
            x=plan['points'][r['point']]['x'];base=density_field(np.array(x))
            field=density_field(np.array(x),shape=(ny,nx)) if mapping=='native_parameter_resampling' else transfer(base,(ny,nx))
            assert sha(np.asarray(field,dtype='<f8').tobytes())==r['density_sha256']
            assert r['geometry']==normalized_geometry(nx,ny) and abs(field.mean()-.35)<=1e-12
            pending=r;count['density_and_context_replays']+=1
        elif r['event']=='label':
            assert pending and r['request']==pending['request'];key=pending['context'].split('/')[0]+':'+pending['density_sha256']
            if r['origin']=='new_physics_attempt':paid+=1
            else:assert key in cache and cache[key]==r['y'];count['exact_mesh_density_cache_reuses']+=1
            assert r['paid_attempts']==paid;cache[key]=r['y']
            value=responses[pending['context']][pending['point']]
            assert value['y']==r['y'] and value['density_sha256']==pending['density_sha256']
            old=plan['points'][pending['point']]['old_y'];coarse=pending['context'].startswith('100x50/')
            flag=coarse and not np.isclose(r['y'],old,rtol=cfg['source_prediction_tolerance'],atol=1e-8)
            assert flag==r['coarse_source_agreement_flag']==value['coarse_source_agreement_flag']
            assert value['equilibrium_flag']==(value['equilibrium_relative_residual']>cfg['equilibrium_residual_flag'])
            count['ordered_pre_label_pairs']+=1;pending=None
    assert pending is None and paid==status['new_physics_attempts']
    rows=[];cases=[]
    for c in plan['cases']:
        for context,values in responses.items():
            initial=values[c['initial_point']]['y']
            for h in [0,5]:
                for target in ['fixed_endpoint','retained_pool']:
                    if target=='fixed_endpoint':ids={n:c['fixed_endpoints'][n][str(h)] for n in ['mean',c['control']]}
                    else:ids={n:min(c['branches'][n][:h+2],key=lambda p:values[p]['y']) for n in ['mean',c['control']]}
                    mean=values[ids['mean']]['y'];alt=values[ids[c['control']]]['y'];delta=(mean-alt)/initial
                    old=effect_label(c['old_effects'][str(h)],c['relative_margin']);label=effect_label(delta,c['relative_margin'])
                    rows.append({'case':c['case'],'group':c['group'],'source':c['source'],'state':c['state'],'control':c['control'],
                        'context':context,'horizon':h,'target':target,'initial_compliance':initial,
                        'mean_design_compliance':mean,'alternative_design_compliance':alt,'relative_advantage_percent':100*delta,
                        'margin':c['relative_margin'],'original_effect':old,'effect':label,'classification_changed':label!=old,
                        'mean_point':ids['mean'],'alternative_point':ids[c['control']]})
        fixed=[r for r in rows if r['case']==c['case'] and r['horizon']==5 and r['target']=='fixed_endpoint']
        pool=[r for r in rows if r['case']==c['case'] and r['horizon']==5 and r['target']=='retained_pool']
        cases.append({'case':c['case'],'group':c['group'],'state':c['state'],'control':c['control'],
                     'original_h5_class':fixed[0]['original_effect'],'fixed_h5_all_contexts_stable':all(not r['classification_changed'] for r in fixed),
                     'fixed_h5_class_changes':sum(r['classification_changed'] for r in fixed),'retained_pool_h5_class_changes':sum(r['classification_changed'] for r in pool),
                     'distinct_fixed_h5_endpoint_designs':c['fixed_endpoints']['mean']['5']!=c['fixed_endpoints'][c['control']]['5'],
                     'native_fine_h5_class':next(r['effect'] for r in fixed if r['context']=='200x100/native_parameter_resampling'),
                     'transferred_fine_h5_class':next(r['effect'] for r in fixed if r['context']=='200x100/conservative_base_field_transfer')})
    native=responses['100x50/native_parameter_resampling'];coarse_flags=[{'point':p,'old_y':plan['points'][p]['old_y'],
                    'rechecked_y':v['y'],'relative_difference':v['source_relative_difference']} for p,v in native.items() if v['coarse_source_agreement_flag']]
    max_objective_changes={}
    for context,values in responses.items():
        max_objective_changes[context]=max(abs(v['y']-native[p]['y'])/native[p]['y'] for p,v in values.items())
    all_values=[v for values in responses.values() for v in values.values()]
    report={'complete':True,'protocol_commit':status['protocol_commit'],'initial_protocol_commit':'72a519e1bbf7e02bee451076f075a96f307ab7f5',
            'selected_contrasts':len(cases),'selected_states':len({c['state'] for c in plan['cases']}),'unique_design_points':len(plan['points']),
            'original_attempts':4,'recovery_execution_new_attempts':paid,'total_new_physics_attempts':paid+4,'recovered_missing_responses':1,
            'original_gate_passed':False,'source_agreement_tolerance_unchanged':True,'coarse_source_flagged_unique_points':len(coarse_flags),'coarse_source_flags':coarse_flags,
            'checks':dict(count),'fixed_h5_all_contexts_stable_cases':sum(c['fixed_h5_all_contexts_stable'] for c in cases),
            'distinct_fixed_h5_endpoint_pairs':sum(c['distinct_fixed_h5_endpoint_designs'] for c in cases),
            'distinct_fixed_h5_pairs_stable':sum(c['distinct_fixed_h5_endpoint_designs'] and c['fixed_h5_all_contexts_stable'] for c in cases),
            'case_summaries':cases,'max_relative_objective_changes':max_objective_changes,
            'max_equilibrium_relative_residual':max(v['equilibrium_relative_residual'] for v in all_values),
            'max_energy_work_gap':max(v['relative_energy_work_gap'] for v in all_values),'equilibrium_flagged_context_points':sum(v['equilibrium_flag'] for v in all_values),
            'extra_independent_optimization_samples':0,'fine_grid_gp_rerun':False,'all_original_training_points_refined':False,
            'mesh_convergence_certified':False,'engineering_margin_certified':False}
    DEST.mkdir(parents=True,exist_ok=True);write(DEST/'analysis.json',report)
    for name,data in [('paired_contrasts.csv',rows),('case_summary.csv',cases)]:
        with (DEST/name).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(data[0]),lineterminator='\n');w.writeheader();w.writerows(data)
    print(json.dumps(report))
if __name__=='__main__':main()
