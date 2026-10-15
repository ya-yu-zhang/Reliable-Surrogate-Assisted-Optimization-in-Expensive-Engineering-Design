"""Already paid two-step engineering outcomes, only after v2 decisions freeze."""
from fractions import Fraction
import json
import math
import numpy as np
from .run_positive_rollout_v2 import ROOT,OUT,CONFIG,digest,save
from .verify_and_benchmark_gp_envelope import locate,future_pool


def run():
    frozen=json.loads((OUT/"decisions_frozen.json").read_text())
    assert not (OUT/"paid_replay.json").exists(),"Do not overwrite paid replay"
    for path,sha in frozen["output_sha256"].items():
        assert digest(OUT/path)==sha,path
    assert digest(CONFIG)==frozen["config_sha256"]
    for path,sha in frozen["source_sha256"].items():
        assert digest(ROOT/path)==sha,path
    for path,sha in frozen["case_inputs_sha256"].items():
        assert digest(ROOT/path)==sha,path
    states=json.loads((OUT/"decisions.json").read_text())
    cases={}
    for path in frozen["case_inputs_sha256"]:
        case=json.loads((ROOT/path).read_text());m=case["metadata"]
        cases[m["dataset"],m["state"]]=case
    inputs={}
    common_path=locate(ROOT,"results/engineering_optimization_common_continuation_v1/events.jsonl")
    inputs[str(common_path.relative_to(ROOT))]=digest(common_path)
    common={};pending=None;context=None
    for line in common_path.open():
        r=json.loads(line)
        if r["event"]=="meta":context=r.get("objective_context")
        elif r["event"]=="pre":pending=r
        elif r["event"]=="label":
            assert pending is not None
            if r["step"] in [0,1]:
                assert (r["state"],r["branch"],r["step"])==(pending["state"],pending["branch"],pending["step"])
                common[r["state"],r["branch"],r["step"]]={**pending,"y":r["y"]}
            pending=None
    assert context and "100x50" in context
    actual={};records=[]
    for (dataset,state),case in cases.items():
        m=case["metadata"];initial=case["initial"]
        pool,seed=future_pool(m,case["config"])
        assert seed==case["pool_seed"] and __import__("hashlib").sha256(pool.tobytes()).hexdigest()==case["raw_pool_sha256"]
        summary=None
        if dataset=="previous_holdout":
            path=locate(ROOT,f"results/engineering_optimization_budget_audit_v1/block_{m['block']}/{state}_summary.json")
            inputs[str(path.relative_to(ROOT))]=digest(path);summary=json.loads(path.read_text())
            assert all(np.array_equal(np.array(initial[k]),np.array(summary[k])) for k in ["X","y","theta"])
            assert initial["actions"]==summary["actions"]
        for b,rec in case["branches"].items():
            if dataset=="archived_common_mean":
                first,second=(common[state,b,t] for t in [0,1])
                counts=[first["observations_before"],second["observations_before"]]
            else:
                first,second=summary["trajectories"]["mean"][b][:2]
                counts=[first["training_count"],second["training_count"]]
                assert first["point_key"].startswith("default100x50:")
                assert second["point_key"].startswith("default100x50:") and second["control"]=="mean"
            assert first["step"]==0 and second["step"]==1
            assert counts==[len(initial["y"]),len(initial["y"])+1]
            assert all(math.isfinite(float(r["y"])) and r["y"]>0 for r in [first,second])
            assert np.array_equal(np.array(first["x"]),np.array(initial["actions"][b]))
            candidates=pool[np.array(rec["eligible_pool_indices"])]
            assert second["pool_sha256"]==__import__("hashlib").sha256(candidates.tobytes()).hexdigest()
            matches=np.flatnonzero(np.all(candidates==np.array(second["x"]),axis=1));assert len(matches)==1
            z=Fraction(float(first["y"]))
            eligible=[c["index"] for c in rec["nominal_cells"]
                if (c["lower"] is None or Fraction(c["lower"])<=z)
                and (c["upper"] is None or z<=Fraction(c["upper"]))]
            assert eligible
            nominal=min(eligible);native=int(matches[0])
            row=dict(dataset=dataset,state=state,branch=b,first_response=first["y"],
                second_response=second["y"],terminal=min(m["initial"],first["y"],second["y"]),
                nominal_next_index=nominal,native_next_index=native,selector_matches=nominal==native,
                first_point_matches=True,next_pool_matches=True,training_counts=counts)
            actual[dataset,state,b]=row;records.append(row)
    assert len(records)==114
    counts={k:dict(better=0,tie=0,worse=0) for k in ["raw_mean","raw_ei","positive_one_step_ei"]}
    rows=[];unresolved=[]
    for r in states:
        key=r["dataset"],r["state"];case=cases[key];m=case["metadata"]
        selected=r["methods"].get("local",{})
        if selected.get("checked_status")!="accepted":
            unresolved.append(dict(dataset=key[0],state=key[1],reason=r.get("reason","local_selection_unresolved")))
            rows.append(dict(dataset=key[0],state=key[1],status="unresolved"))
            continue
        branch=selected["selected"]
        comparator={label:next(b for b,controls in m["classes"].items() if control in controls)
                    for label,control in [("raw_mean","mean"),("raw_ei","ei")]}
        comparator["positive_one_step_ei"]=r["positive_myopic_branch"]
        chosen=actual[*key,branch]
        if not chosen["selector_matches"] or any(not actual[*key,b]["selector_matches"] for b in comparator.values()):
            unresolved.append(dict(dataset=key[0],state=key[1],reason="nominal/native_policy_mismatch"))
            rows.append(dict(dataset=key[0],state=key[1],status="policy_mismatch"));continue
        row=dict(dataset=key[0],state=key[1],status="graded",selected_branch=branch,
                 initial=m["initial"],selected_terminal=chosen["terminal"],comparators={})
        for label,b in comparator.items():
            terminal=actual[*key,b]["terminal"]
            difference=Fraction(float(chosen["terminal"]))-Fraction(float(terminal))
            delta=Fraction(float(m["initial"]))/1000000
            category="better" if difference < -delta else "worse" if difference > delta else "tie"
            counts[label][category]+=1
            row["comparators"][label]=dict(branch=b,terminal=terminal,
                difference=float(difference),relative_difference=float(difference/Fraction(float(m["initial"]))),category=category)
        rows.append(row)
    graded=[r for r in rows if r["status"]=="graded"]
    report=dict(version="new_v2",scope="Dependent already-paid two-evaluation replay; not independent policy validation",
        decision_freeze_sha256=digest(OUT/"decisions_frozen.json"),
        source_sha256=digest(__file__),inputs_sha256=inputs,states=43,graded_states=len(graded),
        unresolved_or_mismatched_states=unresolved,all_branch_records=114,
        all_first_points_and_next_pools_and_training_counts_match=True,
        nominal_native_selector_matches=sum(r["selector_matches"] for r in records),
        counts=counts,mean_relative_changes={k:float(np.mean([r["comparators"][k]["relative_difference"] for r in graded])) if graded else None for k in counts},
        median_relative_changes={k:float(np.median([r["comparators"][k]["relative_difference"] for r in graded])) if graded else None for k in counts},
        inferential_statistics=False,independent_validation=False,
        new_physical_evaluations=0,new_bound_queries=0,new_GP_constructions=0,
        new_hyperparameter_fits=0,new_independent_samples=0)
    save(OUT/"paid_outcomes.json",records)
    save(OUT/"paid_replay_states.json",rows)
    save(OUT/"paid_replay.json",report)
    print(json.dumps({k:v for k,v in report.items() if k!="inputs_sha256"},indent=2))


if __name__=="__main__":
    run()
