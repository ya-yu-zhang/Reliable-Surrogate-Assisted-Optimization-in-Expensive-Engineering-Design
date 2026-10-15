"""Read-only feasibility gate for event-bounded two-step rollout.

Ordinary floating arithmetic/quad: no rigorous probability or utility certificate.
Loads only initial plans and frozen coefficient records, never future labels.
Fixed kernel algebra is new work; no physical solver, bounds or optimizer fits.
"""
from pathlib import Path
import json,hashlib,time,math,sys
import numpy as np
from scipy.linalg import cho_solve,solve_triangular
from scipy.special import ndtr
from scipy.integrate import quad
from sklearn.gaussian_process.kernels import ConstantKernel,Matern
sys.path.insert(0,str(Path.cwd()))
from src.verify_and_benchmark_gp_envelope import locate,future_pool
from src.certified_affine_envelope import coefficient_bands
from src.filtered_exact_action_sets import integer_envelope_from_bands
root=Path.cwd();gp=root/'gp_attachment/results/engineering_optimization_gp_reachability_v1'
plan=json.loads((gp/'plan.json').read_text());status=json.loads((gp/'construction_status.json').read_text())
rows=[];inputs={};t0=time.perf_counter();diag_relative_checks=[]
for path in [gp/'plan.json',gp/'construction_status.json',root/'src/filtered_exact_action_sets.py',root/'src/certified_affine_envelope.py',root/'src/verify_and_benchmark_gp_envelope.py']:
 inputs[str(path.relative_to(root))]=hashlib.sha256(path.read_bytes()).hexdigest()
design={'status':'preflight-only; no rigorous numerical certificate', 'full_gaussian_root_posterior':True,'all_114_branches':True,'read_future_responses':False,'target_delta_over_initial':1e-6,'fixed_pair_check':'analytic conditional EI, ordinary floating quad on standardized [-12,12], split at incumbent threshold','quad_epsabs':1e-8,'quad_epsrel':1e-10,'quad_limit':200,'new_physics':0,'new_hyperparameter_fits':0,'new_independent_samples':0}
(root/'results/rollout_event_preflight_20261015/DESIGN.json').write_text(json.dumps(design,indent=2)+'\n')
def phi(x):return math.exp(-x*x/2)/math.sqrt(2*math.pi) if math.isfinite(x) and abs(x)<40 else 0.
def mass(l,u):
 if l>=0:return float(ndtr(-l)-ndtr(-u))
 return float(ndtr(u)-ndtr(l))
def abs_affine(a,b,l,u):
 if l>=u:return 0.
 cuts=[l,u]
 if b and l < -a/b < u:cuts.insert(1,-a/b)
 total=0.
 for lo,hi in zip(cuts[:-1],cuts[1:]):
  v=a*mass(lo,hi)+b*(phi(lo)-phi(hi));total+=abs(v)
 return total
for name in sorted(status['files_sha256']):
 path=gp/'construction'/name;raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==status['files_sha256'][name];inputs[str(path.relative_to(root))]=hashlib.sha256(raw).hexdigest();item=json.loads(raw);meta=item['metadata'];cfg=plan['pool_configs'][meta['dataset']]
 source=('results/engineering_optimization_common_continuation_v1/plans/'+meta['state']+'.json' if meta['dataset']=='archived_common_mean' else f"results/engineering_optimization_budget_audit_v1/block_{meta['block']}/{meta['state']}_plan.json")
 p=locate(root,source);initial=json.loads(p.read_text());assert not {'trajectories','control_curves','branch_records','calibration'}.intersection(initial)
 inputs[str(p.relative_to(root))]=hashlib.sha256(p.read_bytes()).hexdigest()
 X=np.array(initial['X']);y=np.array(initial['y']);normal_mean=float(y.mean());scale=float(y.std());target=(y-normal_mean)/scale
 kernel=(ConstantKernel(1.,(.05,20))*Matern(np.full(19,.2),(.005,2.),nu=2.5)).clone_with_theta(np.array(initial['theta']))
 A=kernel(X);A[np.diag_indices_from(A)]+=cfg['alpha'];L=np.linalg.cholesky(A);P=cho_solve((L,True),np.eye(len(A)));alpha=cho_solve((L,True),target)
 pool,seed=future_pool(meta,cfg);assert hashlib.sha256(pool.tobytes()).hexdigest()==item['raw_pool_sha256']
 for branch,rec in item['branches'].items():
  c=rec['coefficients'];bands=coefficient_bands(c['slope'],c['intercept'],c['slope_error'],c['intercept_error'])
  pos=integer_envelope_from_bands(*bands,response_lower=0.)
  la,lb,ua,ub=bands;neg=integer_envelope_from_bands([-x for x in ua],lb,[-x for x in la],ub,response_lower=0.)
  ids=sorted(set(pos['indices'])|set(neg['indices']));eligible=pool[np.array(rec['eligible_pool_indices'])]
  first=np.array(initial['actions'][branch]);test=np.vstack((first,eligible[ids]));B=kernel(test,X)
  mean=normal_mean+scale*(B@alpha);C=(kernel(test)-B@cho_solve((L,True),B.T))*scale**2;C=(C+C.T)/2
  projected=solve_triangular(L,B.T,lower=True)
  alternate=(kernel.diag(test)-np.einsum('ij,ij->j',projected,projected))*scale**2
  relative=float(np.max(np.abs(np.diag(C)-alternate)/np.maximum(np.abs(alternate),1.)))
  assert relative<1e-8
  diag_relative_checks.append(relative)
  sz=math.sqrt(C[0,0]);anchor=int(np.argmin(np.array(c['slope'])*mean[0]+np.array(c['intercept'])));assert anchor in ids;j0=ids.index(anchor)+1
  gam=C[1:,0]/sz;sig2=np.diag(C)[1:]-gam**2;assert np.all(sig2>0),(name,branch,sig2)
  sig=np.sqrt(sig2);eta=0.;switch_mass=0.;intervals=[]
  for result,flip in [(pos,False),(neg,True)]:
   for i in result['indices']:
    low,up=result['exact_intervals'][i]
    zl=(-math.inf if up is None else -float(up)) if flip else float(low)
    zu=-float(low) if flip else (math.inf if up is None else float(up))
    lo,hi=(zl-mean[0])/sz,(zu-mean[0])/sz
    if i != anchor:
     k=ids.index(i);Pmass=mass(lo,hi);switch_mass+=Pmass
     eta+=abs_affine(mean[k+1]-mean[j0],gam[k]-gam[j0-1],lo,hi)+math.sqrt(2/math.pi)*abs(sig[k]-sig[j0-1])*Pmass
    intervals.append({'index':i,'z_lo':None if not math.isfinite(zl) else zl,'z_hi':None if not math.isfinite(zu) else zu,'side':'negative' if flip else 'nonnegative'})
  def ei(t,mu,sd):
   d=t-mu;v=d/sd
   return max(0.,d*float(ndtr(v))+sd*phi(v))
  def integrand(x):
   z=mean[0]+sz*x
   return ei(min(meta['initial'],z),mean[j0]+gam[j0-1]*x,sig[j0-1])*phi(x)
  split=(meta['initial']-mean[0])/sz
  cuts=sorted(set([-12.,12.]+([float(split)] if -12.<split<12. else [])))
  integral=sum(quad(integrand,l,u,epsabs=1e-8,epsrel=1e-10,limit=200)[0] for l,u in zip(cuts[:-1],cuts[1:]))
  G=ei(meta['initial'],mean[0],sz)+integral
  rows.append({'dataset':meta['dataset'],'state':meta['state'],'block':meta['block'],'branch':branch,'initial':meta['initial'],'root_mean':float(mean[0]),'root_sd':sz,'reference_next_index':anchor,'whole_line_retained':len(ids),'provisional_switch_mass_sum':switch_mass,'provisional_eta':float(eta),'provisional_fixed_pair_value':float(G),'provisional_value_lower':float(max(0,G-eta)),'provisional_value_upper':float(G+eta),'root_negative_probability_float':float(ndtr(-mean[0]/sz)),'provisional_eta_over_initial':eta/meta['initial'],'root_inverse_residual_float':float(np.linalg.norm(np.eye(len(A))-A@P,ord=np.inf)),'minimum_conditional_variance_float':float(min(sig2)),'intervals':intervals})
assert len(rows)==114
smoke=[]
for a,b,lo,hi in [(0.,1.,-math.inf,math.inf),(3.,0.,-math.inf,math.inf),(1.,-2.,-3.,4.),(-2.,3.,.5,math.inf)]:
 cuts=[lo,hi]
 if b and lo < -a/b < hi:cuts.insert(1,-a/b)
 oracle=sum(quad(lambda x:abs(a+b*x)*phi(x),l,u,epsabs=1e-10,epsrel=1e-10)[0] for l,u in zip(cuts[:-1],cuts[1:]))
 actual=abs_affine(a,b,lo,hi);assert math.isclose(actual,oracle,rel_tol=1e-10,abs_tol=1e-10)
 smoke.append({'analytic':actual,'quadrature':oracle,'absolute_difference':abs(actual-oracle)})
scales=[]
for meta in plan['mean_states']:
 name=('results/engineering_optimization_common_continuation_v1/plans/'+meta['state']+'.json' if meta['dataset']=='archived_common_mean' else f"results/engineering_optimization_budget_audit_v1/block_{meta['block']}/{meta['state']}_plan.json")
 p=locate(root,name);initial=json.loads(p.read_text());assert not {'trajectories','control_curves','branch_records','calibration'}.intersection(initial)
 inputs[str(p.relative_to(root))]=hashlib.sha256(p.read_bytes()).hexdigest();y=np.array(initial['y'])
 scales.append({'dataset':meta['dataset'],'state':meta['state'],'n':len(y),'minimum_observed':float(y.min()),'maximum_observed':float(y.max()),'target_scale':float(y.std())})
assert len(scales)==60
crosscheck=max(abs(r['root_negative_probability_float']-.5*math.erfc(r['root_mean']/r['root_sd']/math.sqrt(2))) for r in rows)
assert crosscheck<1e-14
(root/'results/rollout_event_preflight_20261015/initial_scale_diagnostic.json').write_text(json.dumps({'scope':'initial observed responses only; no future journals','states':scales,'negative_probability_float_crosscheck_abs_max':crosscheck},indent=2)+'\n')
out=root/'results/rollout_event_preflight_20261015'
groups={}
for r in rows:groups.setdefault((r['dataset'],r['state']),[]).append(r)
checks=[]
for (dataset,state),group in groups.items():
 chosen=max(group,key=lambda r:(r['provisional_value_lower'],-int(r['branch'].lstrip('b'))))
 gap=max(r['provisional_value_upper'] for r in group)-chosen['provisional_value_lower']
 checks.append({'dataset':dataset,'state':state,'branches':len(group),'provisional_gap':gap,'delta':group[0]['initial']*1e-6,'provisional_shortcut_resolves':bool(gap<=group[0]['initial']*1e-6)})
(out/'selection_feasibility.json').write_text(json.dumps(checks,indent=2)+'\n')
report={'type':'feasibility-only floating diagnostic; not a rigorous probability or utility certificate','baseline':'58f539c2d0738b20c7d0d4889fe8d808a03a3019','contexts':43,'branches':len(rows),'all_60_metadata_states_retained':len(plan['mean_states'])==60,'alias_states':17,'new_fixed_kernel_root_systems':43,'new_physical_evaluations':0,'new_bound_queries':0,'new_hyperparameter_fits':0,'new_independent_optimization_samples':0,'future_response_journals_or_grading_tables_read':False,'root_inverse_residual_float_max':max(r['root_inverse_residual_float'] for r in rows),'minimum_conditional_variance_float':min(r['minimum_conditional_variance_float'] for r in rows),'provisional_eta_below_planned_delta':int(sum(r['provisional_eta_over_initial']<=1e-6 for r in rows)),'provisional_switch_mass_sum_max':max(r['provisional_switch_mass_sum'] for r in rows),'provisional_eta_over_initial_max':max(r['provisional_eta_over_initial'] for r in rows),'elapsed_seconds':time.perf_counter()-t0,'provisional_shortcut_resolved_states':sum(r['provisional_shortcut_resolves'] for r in checks),'root_negative_probability_float_min':min(r['root_negative_probability_float'] for r in rows),'root_negative_probability_float_median':float(np.median([r['root_negative_probability_float'] for r in rows])),'root_negative_probability_float_max':max(r['root_negative_probability_float'] for r in rows),'all_initial_plans_available':len(scales),'covariance_diagonal_relative_crosscheck_max':max(diag_relative_checks),'normal_moment_smoke_checks':smoke,'negative_probability_cdf_crosscheck_abs_max':crosscheck,'initial_input_hashes':inputs,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(out/'analysis.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n');(out/'branches.json').write_text(json.dumps(rows,indent=2,allow_nan=False)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='initial_input_hashes'},indent=2))
