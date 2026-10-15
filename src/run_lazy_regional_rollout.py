"""Freeze clean training inputs, then run one paired lazy-region evaluation."""
import argparse,copy,hashlib,json,time,traceback
from pathlib import Path
import numpy as np
from sklearn.gaussian_process.kernels import ConstantKernel,Matern
from threadpoolctl import threadpool_limits
from .rollout_v2_intervals import I,VERSION
from .rollout_v2_posterior import enclose
from .lazy_regional_rollout import solve,check
from .gp_action_reachability import coefficient_enclosures
from .certified_affine_envelope import coefficient_bands
from .filtered_exact_action_sets import prepare_bands
from .verify_and_benchmark_gp_envelope import future_pool

ROOT=Path(__file__).resolve().parents[1]
INPUT=ROOT/'data/lazy_regional_20261015'
OUT=ROOT/'results/lazy_regional_20261015'
CONFIG=ROOT/'configs/lazy_regional_20261015.json'
PROTOCOL='paper/engineering_optimization/contribution_closure_20261015/LAZY_REGIONAL_PROTOCOL.md'
SOURCES=['src/lazy_regional_rollout.py','src/run_lazy_regional_rollout.py','tests/test_lazy_regional_rollout.py']
BASE='58f539c2d0738b20c7d0d4889fe8d808a03a3019'
PARENT='3b3f8a5c58dfa2460afcd6034fe0d0e027bddc99'
FIELDS=['slope','intercept','slope_error','intercept_error']


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')


def snapshot():
    if CONFIG.exists() or INPUT.exists():raise FileExistsError('Preserve first freeze')
    files={}
    for p in sorted((ROOT/'data/positive_rollout_v2_20261015').glob('*.json')):
        old=json.loads(p.read_text())
        clean={k:old[k] for k in ['metadata','initial','config','pool_seed','raw_pool_sha256']}
        clean['branches']={b:{k:v[k] for k in ['eligible_pool_indices','matrix_sha256','cross_sha256','coefficients_sha256']}
                           for b,v in old['branches'].items()}
        text=json.dumps(clean,separators=(',',':'),allow_nan=False)+'\n'
        assert not any(k in text for k in ['legacy_domains','nominal_cells','trajectories','paid_outcomes'])
        dest=INPUT/p.name;dest.parent.mkdir(exist_ok=True)
        dest.write_text(text);files[str(dest.relative_to(ROOT))]=sha(dest)
    assert len(files)==43
    deps=json.loads((ROOT/'results/positive_rollout_v2_20261015/RELEASE_MANIFEST.json').read_text())['core_source_sha256']
    for p in ['src/rollout_regional_enclosure.py']:
        deps[p]=sha(ROOT/p)
    save(CONFIG,dict(scientific_baseline=BASE,parent_commit=PARENT,
        protocol=PROTOCOL,protocol_sha256=sha(ROOT/PROTOCOL),input_sha256=files,
        source_sha256={p:sha(ROOT/p) for p in SOURCES},dependency_sha256=deps,
        states=43,branches=114,metadata_states=60,aliases=17,methods=['uniform','regional'],
        max_solve_seconds=5.,max_operations=2048,max_comparison_seconds=240.,
        repetitions=1,MPFR_bits=192,MPFR_version=VERSION,window=[-8,8],
        delta_over_m0='1/1000000',independent_validation=False,
        original_data_already_observed=True,physical_evaluations=0,bound_queries=0,
        hyperparameter_fits=0,physical_retries=0,physical_replacements=0,new_independent_samples=0))
    print(json.dumps(dict(clean_input_files=len(files),clean_bytes=sum((ROOT/p).stat().st_size for p in files),source_freeze=True)))


def prepare(case):
    began=time.perf_counter();init,m,cfg=case['initial'],case['metadata'],case['config']
    kernel=(ConstantKernel(1.,(.05,20))*Matern(np.full(19,.2),(.005,2.),nu=2.5)).clone_with_theta(np.array(init['theta']))
    X,y=np.array(init['X']),np.array(init['y']);pool,seed=future_pool(m,cfg)
    assert seed==case['pool_seed'] and hashlib.sha256(pool.tobytes()).hexdigest()==case['raw_pool_sha256']
    A=kernel(X);A[np.diag_indices_from(A)]+=cfg['alpha']
    points=[];mapping={};which={};bands={};nominal={};proofs={}
    for b,raw in case['branches'].items():
        first=np.array(init['actions'][b]);key=first.tobytes()
        if key not in mapping:mapping[key]=len(points);points.append(first)
        which[b]=mapping[key]
        aug=np.vstack((X,first));mat=kernel(aug);mat[np.diag_indices_from(mat)]+=cfg['alpha']
        cand=pool[np.array(raw['eligible_pool_indices'])];cross=kernel(cand,aug)
        assert hashlib.sha256(mat.tobytes()).hexdigest()==raw['matrix_sha256']
        assert hashlib.sha256(cross.tobytes()).hexdigest()==raw['cross_sha256']
        coef=coefficient_enclosures(mat,cross,y);coef={k:coef[k].tolist() for k in FIELDS}
        digest=hashlib.sha256(json.dumps([coef[k] for k in FIELDS],separators=(',',':'),allow_nan=False).encode()).hexdigest()
        assert digest==raw['coefficients_sha256']
        bands[b]=coefficient_bands(coef['slope'],coef['intercept'],coef['slope_error'],coef['intercept_error'])
        integers=prepare_bands(coef['slope'],coef['intercept'],coef['slope'],coef['intercept'],0.)[0]
        nominal[b]=integers[:2];proofs[b]=digest
    points=np.array(points);B=kernel(points,X);K=kernel(points)
    means,cov,record=enclose(A,B,K,y)
    models={b:dict(initial=m['initial'],first_mean=means[i].pair(),first_sd=cov[i][i].sqrt().pair(),next={}) for b,i in which.items()}
    record.update(matrix_A_sha256=hashlib.sha256(A.tobytes()).hexdigest(),
        selector_coefficient_sha256=proofs,first_models=copy.deepcopy(models),
        training_matrix_constructions=1,raw_selector_augmented_constructions=len(models),
        first_marginal_posterior_enclosures=1,shared_preparation_seconds=time.perf_counter()-began)
    def oracle_factory():
        records={}
        def query(b,j):
            key=b,str(j)
            if key in records:return records[key]['conditional']
            started=time.perf_counter();first=np.array(init['actions'][b])
            point=pool[case['branches'][b]['eligible_pool_indices'][j]]
            q=np.array([first,point]);bb=kernel(q,X);kk=kernel(q)
            mm,cc,cert=enclose(A,bb,kk,y)
            g=cc[1][0]/I(models[b]['first_sd']);v=cc[1][1]-g.square()
            if v.lo<=0:raise ArithmeticError('Bivariate conditional variance gate')
            conditional=dict(mean=mm[1].pair(),gamma=g.pair(),sd=v.sqrt().pair())
            records[key]=dict(branch=b,action=j,conditional=conditional,mean=[x.pair() for x in mm],
                covariance=[[x.pair() for x in row] for row in cc],arithmetic=cert,
                B_sha256=hashlib.sha256(bb.tobytes()).hexdigest(),K_sha256=hashlib.sha256(kk.tobytes()).hexdigest(),
                seconds=time.perf_counter()-started)
            return conditional
        return query,records
    return models,bands,nominal,record,oracle_factory


def run():
    config=json.loads(CONFIG.read_text())
    for field in ['input_sha256','source_sha256','dependency_sha256']:
        for p,h in config[field].items():assert sha(ROOT/p)==h,p
    assert sha(ROOT/config['protocol'])==config['protocol_sha256']
    OUT.mkdir(exist_ok=False)
    save(OUT/'RUN_STARTED.json',dict(config_sha256=sha(CONFIG),parent=PARENT))
    started=time.perf_counter();states=[];filehashes={};prep_seconds=0.
    for order,rel in enumerate(config['input_sha256']):
        stem=Path(rel).stem;case=json.loads((ROOT/rel).read_text());row=dict(state=stem,methods={})
        if time.perf_counter()-started>=config['max_comparison_seconds']:
            row['status']='not_started_total_budget';states.append(row);continue
        try:
            models,bands,nominal,preparation,factory=prepare(case)
            prep_seconds+=preparation['shared_preparation_seconds']
            path=OUT/'preparation'/f'{stem}.json';save(path,preparation);filehashes[str(path.relative_to(ROOT))]=sha(path)
            row['preparation_seconds']=preparation['shared_preparation_seconds'];row['status']='processed'
            methods=config['methods'] if order%2==0 else list(reversed(config['methods']))
            for method in methods:
                oracle,queries=factory()
                try:
                    model=copy.deepcopy(models)
                    result=solve(model,bands,nominal,oracle,method,config['max_solve_seconds'],config['max_operations'])
                    reader=check(result,copy.deepcopy(models),bands,queries)
                    result['reader']=reader;result['checked_seconds']=result['solve_seconds']+reader['checker_seconds']
                    result['conditional_posterior_records']=[v for v in queries.values()]
                    result['conditional_posterior_enclosure_calls']=len(queries)
                    row['methods'][method]={k:result[k] for k in ['status','selected','checked_seconds','counters','conditional_posterior_enclosure_calls','reader']}
                except Exception as exc:
                    result=dict(status='unresolved_exception',error=repr(exc),traceback=traceback.format_exc(),
                        conditional_posterior_records=list(queries.values()),conditional_posterior_enclosure_calls=len(queries))
                    row['methods'][method]={k:result[k] for k in ['status','error','conditional_posterior_enclosure_calls']}
                path=OUT/'certificates'/f'{stem}__{method}.json';save(path,result);filehashes[str(path.relative_to(ROOT))]=sha(path)
        except Exception as exc:row.update(status='unresolved_preparation',error=repr(exc),traceback=traceback.format_exc())
        states.append(row)
        save(OUT/'progress.json',dict(completed_states=len(states),elapsed_seconds=time.perf_counter()-started))
    decision=dict(states=[dict(state=s['state'],methods={m:dict(status=r['status'],selected=r.get('selected')) for m,r in s['methods'].items()}) for s in states])
    save(OUT/'decisions.json',decision)
    save(OUT/'decisions_frozen.json',dict(decisions_sha256=sha(OUT/'decisions.json'),files_sha256=filehashes,
        future_response_reads=False,old_v2_decision_reads=False))
    summary=dict(states=43,metadata_states=60,aliases=17,branches=114,independent_validation=False,
        processed_states=sum(s['status']=='processed' for s in states),shared_preparation_seconds=prep_seconds,
        methods={},states_detail=states,elapsed_seconds=time.perf_counter()-started,
        physical_evaluations=0,bound_queries=0,hyperparameter_fits=0,physical_retries=0,
        physical_replacements=0,new_independent_samples=0,complete_projections=0,
        historical_domain_reads=False,old_posterior_or_leaf_reads=False,full_joint_SPD_certified=False)
    for m in config['methods']:
        rs=[s['methods'][m] for s in states if m in s['methods']]
        summary['methods'][m]=dict(attempted=len(rs),accepted=sum(r.get('reader',{}).get('accepted',False) for r in rs),
            checked_seconds=sum(r.get('checked_seconds',0.) for r in rs),
            conditional_posterior_enclosure_calls=sum(r['conditional_posterior_enclosure_calls'] for r in rs),
            counters={k:sum(r.get('counters',{}).get(k,0) for r in rs) for k in ['cell_operations','dominance_scans','producer_dominance_checks','conditional_reward_endpoint_evaluations']},
            reader_endpoint_evaluations=sum(r.get('reader',{}).get('conditional_reward_endpoint_evaluations',0) for r in rs))
    save(OUT/'analysis.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k!='states_detail'},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--snapshot',action='store_true');parser.add_argument('--run',action='store_true')
    args=parser.parse_args()
    with threadpool_limits(limits=1):
        if args.snapshot:snapshot()
        elif args.run:run()
