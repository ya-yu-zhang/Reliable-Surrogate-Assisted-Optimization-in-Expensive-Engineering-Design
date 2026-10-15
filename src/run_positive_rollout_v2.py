"""Snapshot, execute and freeze a single v2 development reproduction.

No objective function, bound evaluator or optimizer.fit is called. The snapshot
contains training data, fixed parameters and already-verified legacy domains.
"""
from pathlib import Path
from fractions import Fraction
import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import time
import traceback
import numpy as np
from scipy.integrate import quad
from scipy.special import ndtr
from sklearn.gaussian_process.kernels import ConstantKernel,Matern
from threadpoolctl import threadpool_limits
from .rollout_v2_intervals import I,cdf,exp_times_cdf,VERSION
from .rollout_v2_posterior import enclose
from .rollout_v2_solver import solve,check,rank_key,domain_read
from .verify_and_benchmark_gp_envelope import locate,future_pool
from .gp_action_reachability import coefficient_enclosures
from .certified_affine_envelope import coefficient_bands
from .filtered_exact_action_sets import prepare_bands

ROOT=Path(__file__).resolve().parents[1]
BASE="58f539c2d0738b20c7d0d4889fe8d808a03a3019"
OUT=ROOT/"results/positive_rollout_v2_20261015"
INPUT=ROOT/"data/positive_rollout_v2_20261015"
CONFIG=ROOT/"configs/positive_rollout_v2_20261015.json"
FIELDS=("slope","intercept","slope_error","intercept_error")
SOURCES=["src/rollout_v2_intervals.py","src/rollout_v2_posterior.py",
         "src/rollout_v2_solver.py","src/run_positive_rollout_v2.py",
         "src/replay_positive_rollout_v2.py","tests/test_rollout_v2.py",
         "src/gp_action_reachability.py","src/certified_affine_envelope.py",
         "src/filtered_exact_action_sets.py","src/verify_and_benchmark_gp_envelope.py",
         "src/reduced_compliance_bounds.py"]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path,data,compact=False):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=None if compact else 2,
        separators=(",",":") if compact else None,allow_nan=False)+"\n")


def coeff_digest(c):
    return hashlib.sha256(json.dumps([c[k] for k in FIELDS],
        separators=(",",":"),allow_nan=False).encode()).hexdigest()


def snapshot():
    assert not CONFIG.exists(),"Do not replace a frozen v2 configuration"
    gp=ROOT/"gp_attachment/results/engineering_optimization_gp_reachability_v1"
    status=json.loads((gp/"construction_status.json").read_text())
    plan=json.loads((gp/"plan.json").read_text())
    nominal=json.loads((ROOT/"results/direct_rollout_reference_20261015/conditional_models.json").read_text())
    nominal={(r["dataset"],r["state"],r["branch"]):r["nominal_cells"] for r in nominal}
    files={}
    for name,expected in sorted(status["files_sha256"].items()):
        src=gp/"construction"/name
        assert digest(src)==expected
        raw=json.loads(src.read_text());m=raw["metadata"]
        source=("results/engineering_optimization_common_continuation_v1/plans/"+m["state"]+".json"
                if m["dataset"]=="archived_common_mean" else
                f"results/engineering_optimization_budget_audit_v1/block_{m['block']}/{m['state']}_plan.json")
        source=locate(ROOT,source);initial=json.loads(source.read_text())
        assert not {"trajectories","control_curves","branch_records","calibration"}.intersection(initial)
        frozen=ROOT/"results/gp_envelope_acceleration_20261014/certificates"/name
        old=json.loads(frozen.read_text())
        case=dict(metadata={k:m[k] for k in ("dataset","block","state","source","classes","baseline","initial")},
            initial={k:initial[k] for k in ("X","y","theta","actions")},
            config=plan["pool_configs"][m["dataset"]],pool_seed=raw["pool_seed"],
            raw_pool_sha256=raw["raw_pool_sha256"],branches={},
            origin=dict(construction_sha256=expected,legacy_certificate_sha256=digest(frozen),
                        original_training_plan_sha256=digest(source)))
        for b,r in raw["branches"].items():
            domains=old["branches"][b]["nonnegative"]["exact_intervals"]
            domains={i:[str(Fraction(int(v[0][0]),int(v[0][1]))),
                None if v[1] is None else str(Fraction(int(v[1][0]),int(v[1][1])))] for i,v in domains.items()}
            case["branches"][b]=dict(eligible_pool_indices=r["eligible_pool_indices"],
                matrix_sha256=r["matrix_sha256"],cross_sha256=r["cross_sha256"],
                coefficients_sha256=coeff_digest(r["coefficients"]),
                legacy_domains=domains,nominal_cells=nominal[m["dataset"],m["state"],b])
        target=INPUT/name
        save(target,case,True);files[str(target.relative_to(ROOT))]=digest(target)
    assert len(files)==43
    config=dict(scientific_baseline=BASE,version="new_v2_not_historical_recovery",
        protocol="paper/engineering_optimization/contribution_closure_20261015/POSITIVE_ROLLOUT_V2_PROTOCOL.md",
        protocol_sha256=digest(ROOT/"paper/engineering_optimization/contribution_closure_20261015/POSITIVE_ROLLOUT_V2_PROTOCOL.md"),
        case_inputs_sha256=files,source_sha256={s:digest(ROOT/s) for s in SOURCES},
        metadata_states=60,nontrivial_states=43,branches=114,aliases=17,
        data_already_seen=True,independent_validation=False,
        repetitions=1,methods=["direct","local"],delta_over_initial="1/1000000",
        MPFR_bits=192,normal_window=[-8,8],max_method_seconds=30,
        max_refinements=32768,max_comparison_seconds=600,
        maximum_positive_root_systems=43,maximum_raw_selector_reconstructions=114,
        future_physical_response_reads_in_decision_phase=False,
        new_physical_evaluations=0,new_bound_queries=0,new_hyperparameter_fits=0,
        physical_retries=0,physical_replacements=0,new_independent_samples=0)
    save(CONFIG,config)
    print(json.dumps(dict(snapshot_cases=len(files),snapshot_bytes=sum((ROOT/f).stat().st_size for f in files),
                         source_files=len(SOURCES),new_GP_systems=0),indent=2))


def make_models(case,counters):
    began=time.perf_counter()
    initial,m,cfg=case["initial"],case["metadata"],case["config"]
    X,y=np.asarray(initial["X"]),np.asarray(initial["y"])
    kernel=(ConstantKernel(1.,(.05,20))*Matern(np.full(19,.2),(.005,2.),nu=2.5)).clone_with_theta(np.array(initial["theta"]))
    pool,seed=future_pool(m,cfg)
    assert seed==case["pool_seed"] and hashlib.sha256(pool.tobytes()).hexdigest()==case["raw_pool_sha256"]
    bands,legacy,refs,descriptor,points={},{},{},{},[]
    unique={}
    def point_index(x):
        key=np.asarray(x,dtype=float).tobytes()
        if key not in unique:
            unique[key]=len(points);points.append(np.asarray(x,dtype=float))
        return unique[key]
    # Raw continuation is reconstructed, not refitted. This work is charged.
    for b,rec in case["branches"].items():
        augmented=np.vstack((X,np.asarray(initial["actions"][b])))
        counters["raw_selector_kernel_systems"]+=1
        matrix=kernel(augmented);matrix[np.diag_indices_from(matrix)]+=cfg["alpha"]
        candidates=pool[np.array(rec["eligible_pool_indices"])]
        cross=kernel(candidates,augmented)
        assert hashlib.sha256(matrix.tobytes()).hexdigest()==rec["matrix_sha256"]
        assert hashlib.sha256(cross.tobytes()).hexdigest()==rec["cross_sha256"]
        coef=coefficient_enclosures(matrix,cross,y)
        coef={k:coef[k].tolist() for k in FIELDS}
        assert coeff_digest(coef)==rec["coefficients_sha256"],"Frozen continuation coefficients differ"
        bands[b]=coefficient_bands(coef["slope"],coef["intercept"],coef["slope_error"],coef["intercept_error"])
        legacy[b]={int(i):domain_read(v) for i,v in rec["legacy_domains"].items()}
        a,bias,_,_=prepare_bands(coef["slope"],coef["intercept"],coef["slope"],coef["intercept"],0.)[0]
        descriptor[b]=dict(first=point_index(initial["actions"][b]),
                          next={i:point_index(candidates[i]) for i in legacy[b]},
                          nominal_integer_slopes=a,nominal_integer_intercepts=bias)
    counters["positive_root_kernel_systems"]+=1
    A=kernel(X);A[np.diag_indices_from(A)]+=cfg["alpha"]
    points=np.array(points);B=kernel(points,X);K=kernel(points)
    means,cov,record=enclose(A,B,K,y)
    models,myopic={},{}
    for b,d in descriptor.items():
        i=d["first"];sd=cov[i][i].sqrt()
        if sd.lo<=0:raise ArithmeticError("Nonpositive first-response variance")
        central=float(math.exp(means[i].mid()))
        num,den=central.as_integer_ratio()
        refs[b]=min(range(len(d["nominal_integer_slopes"])),
            key=lambda j:(d["nominal_integer_slopes"][j]*num+d["nominal_integer_intercepts"][j]*den,j))
        assert refs[b] in legacy[b]
        model=dict(initial=m["initial"],first_mean=means[i].pair(),first_sd=sd.pair(),next={})
        for index,j in d["next"].items():
            g=cov[j][i]/sd
            var=cov[j][j]-g.square()
            if var.lo<=0:raise ArithmeticError("Conditional variance gate failed")
            model["next"][str(index)]=dict(mean=means[j].pair(),gamma=g.pair(),sd=var.sqrt().pair())
        models[b]=model
        k=(I(m["initial"]).log()-means[i])/sd
        ei=(I(m["initial"])*cdf(k)-exp_times_cdf(means[i]+sd.square()/2,k-sd)).clipped(0,m["initial"])
        myopic[b]=ei.pair()
    counters["conditional_systems"]+=len(models)
    record.update(matrix_sha256={key:hashlib.sha256(value.tobytes()).hexdigest() for key,value in [("A",A),("B",B),("K",K)]},
        finite_target_count=len(points),models=models,reference_indices=refs,
        mean_intervals=[x.pair() for x in means],covariance_intervals=[[x.pair() for x in row] for row in cov],
        shared_preparation_seconds=time.perf_counter()-began)
    positive_ei=min(myopic,key=lambda b:(-I(myopic[b]).mid(),rank_key(b)))
    record["positive_myopic_value_intervals"]=myopic
    record["positive_myopic_branch"]=positive_ei
    return models,bands,legacy,refs,record


def quadrature_reference(model,cells):
    m,s=I(model["first_mean"]).mid(),I(model["first_sd"]).mid()
    m0=model["initial"];total=err=0.
    for cell in cells:
        lo=None if cell["lower"] is None else Fraction(cell["lower"])
        hi=None if cell["upper"] is None else Fraction(cell["upper"])
        if hi is not None and hi<=0:continue
        l=-8. if lo is None or lo<=0 else max(-8.,(math.log(float(lo))-m)/s)
        u=8. if hi is None else min(8.,(math.log(float(hi))-m)/s)
        if l>=u:continue
        j=str(cell["index"]);p=model["next"][j]
        mu,g,sd=(I(p[k]).mid() for k in ["mean","gamma","sd"])
        def f(x):
            logh=min(math.log(m0),m+s*x);h=math.exp(logh)
            c=mu+g*x;k=(logh-c)/sd
            q=m0-h*ndtr(-k)-math.exp(c+sd*sd/2)*ndtr(k-sd)
            return q/m0*math.exp(-x*x/2)/math.sqrt(2*math.pi)
        cut=(math.log(m0)-m)/s
        v,e=quad(f,l,u,epsabs=1e-11,epsrel=1e-11,points=[cut] if l<cut<u else None)
        total+=v*m0;err+=e*m0
    return dict(point_parameter_value=total,ordinary_error_estimate=err,rigorous=False)


def run():
    config=json.loads(CONFIG.read_text())
    assert config["scientific_baseline"]==BASE
    assert digest(ROOT/config["protocol"])==config["protocol_sha256"]
    for source,expected in config["source_sha256"].items():
        assert digest(ROOT/source)==expected,source
    for path,expected in config["case_inputs_sha256"].items():
        assert digest(ROOT/path)==expected,path
    OUT.mkdir(parents=True,exist_ok=True)
    with (OUT/"RUN_STARTED.json").open("x") as stream:
        json.dump(dict(config_sha256=digest(CONFIG),physical_calls=0,version="v2"),stream)
    began=time.perf_counter()
    counters=dict(positive_root_kernel_systems=0,raw_selector_kernel_systems=0,
                  conditional_systems=0,method_runs=0,new_physical_evaluations=0,
                  new_bound_queries=0,new_hyperparameter_fits=0,new_independent_samples=0)
    states=[]
    for number,path in enumerate(sorted(config["case_inputs_sha256"])):
        case=json.loads((ROOT/path).read_text());m=case["metadata"];slug=Path(path).stem
        row=dict(dataset=m["dataset"],state=m["state"],initial=m["initial"],
                 status="unresolved",methods={},positive_myopic_branch=None)
        if time.perf_counter()-began>=config["max_comparison_seconds"]:
            row["reason"]="global_time_limit"
        else:
            try:
                models,bands,legacy,refs,posterior=make_models(case,counters)
                save(OUT/"posterior"/(slug+".json"),posterior)
                row["positive_myopic_branch"]=posterior["positive_myopic_branch"]
                row["shared_preparation_seconds"]=posterior["shared_preparation_seconds"]
                for method in (["direct","local"] if number%2==0 else ["local","direct"]):
                    if time.perf_counter()-began>=config["max_comparison_seconds"]:
                        row["methods"][method]=dict(status="unresolved",reason="global_time_limit")
                        continue
                    counters["method_runs"]+=1
                    record=solve(models,bands,legacy,refs,method,
                                 config["max_method_seconds"],config["max_refinements"])
                    verification=check(record,models,bands,legacy,refs)
                    record["reader"]=verification
                    record["checked_seconds"]=record["solve_seconds"]+verification["checker_seconds"]
                    record["checked_status"]=("accepted" if record["status"]=="accepted"
                        and verification["accepted"] and record["checked_seconds"]<=config["max_method_seconds"] else "unresolved")
                    save(OUT/"certificates"/(slug+"__"+method+".json"),record)
                    row["methods"][method]={k:record[k] for k in
                        ["status","checked_status","selected","full_projections","refinements","endpoint_evaluations","checked_seconds"]}
                    row["methods"][method]["checked_regret_upper"]=verification["regret_upper"]
                references={b:quadrature_reference(models[b],case["branches"][b]["nominal_cells"]) for b in models}
                save(OUT/"references"/(slug+".json"),references)
                row["reference_containment"]={method:{b:
                    I(recorded["reader"]["intervals"][b]).lo<=v["point_parameter_value"]<=I(recorded["reader"]["intervals"][b]).hi
                    for b,v in references.items()} for method in row["methods"]
                    if (OUT/"certificates"/(slug+"__"+method+".json")).exists()
                    for recorded in [json.loads((OUT/"certificates"/(slug+"__"+method+".json")).read_text())]}
                row["status"]="completed"
            except Exception as exc:
                row["reason"]=type(exc).__name__+": "+str(exc)
                row["traceback"]=traceback.format_exc()
        states.append(row)
        save(OUT/"states"/(slug+".json"),row)
        save(OUT/"progress.json",dict(states=states,counters=counters,elapsed_seconds=time.perf_counter()-began))
        print(json.dumps(dict(done=len(states),state=row["state"],status=row["status"],
             accepted={k:v.get("checked_status") for k,v in row["methods"].items()},reason=row.get("reason"))),flush=True)
    assert len(states)==43
    summary=dict(version="new_v2_not_historical_recovery",scientific_baseline=BASE,
        states=43,metadata_states=60,aliases=17,branches=114,data_already_seen=True,independent_validation=False,
        accepted_states={method:sum(r["methods"].get(method,{}).get("checked_status")=="accepted" for r in states) for method in ["direct","local"]},
        both_accepted_same_choice=sum(all(r["methods"].get(k,{}).get("checked_status")=="accepted" for k in ["direct","local"])
            and r["methods"]["direct"]["selected"]==r["methods"]["local"]["selected"] for r in states),
        complete_projections={k:sum(r["methods"].get(k,{}).get("full_projections",0) for r in states) for k in ["direct","local"]},
        checked_seconds={k:sum(r["methods"].get(k,{}).get("checked_seconds",0) for r in states) for k in ["direct","local"]},
        shared_preparation_seconds=sum(r.get("shared_preparation_seconds",0) for r in states),
        reference_checks=sum(len(vals) for r in states for vals in r.get("reference_containment",{}).values()),
        reference_containment_failures=sum(not value for r in states for vals in r.get("reference_containment",{}).values() for value in vals.values()),
        unresolved_or_failed_states=[dict(dataset=r["dataset"],state=r["state"],reason=r.get("reason")) for r in states
             if r["status"]!="completed" or any(r["methods"].get(k,{}).get("checked_status")!="accepted" for k in ["direct","local"])],
        counters=counters,elapsed_seconds=time.perf_counter()-began,
        runtime=dict(MPFR=VERSION,MPFR_bits=192,**{n:importlib.metadata.version(n) for n in ["numpy","scipy","scikit-learn"]}),
        timing_scope="One alternating-order paired pass; numerical solver plus fresh reader; common preparation separate; not an inferential benchmark or deployment measurement",
        original_positive_files_recovered=False,new_PDF_or_ZIP=False,final_submit_ready=False)
    save(OUT/"analysis.json",summary)
    save(OUT/"decisions.json",states)
    hashes={str(p.relative_to(OUT)):digest(p) for p in OUT.rglob("*.json") if p.name not in ["RUN_STARTED.json","decisions_frozen.json"]}
    save(OUT/"decisions_frozen.json",dict(output_sha256=hashes,config_sha256=digest(CONFIG),
        source_sha256=config["source_sha256"],case_inputs_sha256=config["case_inputs_sha256"],
        future_physical_responses_read=False,new_physical_evaluations=0))
    print(json.dumps(summary,indent=2),flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("action",choices=["snapshot","run"])
    action=parser.parse_args().action
    with threadpool_limits(limits=1):
        snapshot() if action=="snapshot" else run()
