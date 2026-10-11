"""Read-only audit and repeat-first reporting of the frozen transfer study."""
import csv
from collections import Counter
import hashlib
import json
from pathlib import Path
import numpy as np
from .engineering_optimization_transfer import CONFIG, ROOT, seed, select_policy, write_json

REPORT = ROOT / "paper/engineering_optimization/transfer_validation"


def analyze():
    cfg = json.loads(CONFIG.read_text())
    out = ROOT / cfg["out"]
    status = json.loads((out / "run_status.json").read_text())
    assert status["complete"] and status["cases_completed"] == 20
    rows, summaries, inventories = [], [], []
    for c in range(2):
        for rep in range(10):
            folder = out / f"load{c}_r{rep:02d}"
            summary = json.loads((folder / "summary.json").read_text())
            raw = (folder / "events.jsonl").read_bytes()
            assert hashlib.sha256(raw).hexdigest() == summary["journal_sha256"]
            journal = [json.loads(l) for l in raw.splitlines()]
            meta = journal[0]
            assert meta["event"] == "meta" and (meta["condition"], meta["repeat"]) == (c, rep)
            assert meta["config_sha256"] == hashlib.sha256(CONFIG.read_bytes()).hexdigest()
            assert meta["code_sha256"] == hashlib.sha256((ROOT/"src/engineering_optimization_transfer.py").read_bytes()).hexdigest()
            assert not any(r["event"] == "failure" for r in journal)
            pairs = []
            for i, event in enumerate(journal):
                if event["event"] == "pre":
                    label = journal[i+1]
                    assert label["event"] == "label" and label["call_id"] == event["call_id"]
                    assert np.isfinite(label["y"]) and label["y"] > 0
                    x = np.asarray(event["x"])
                    assert x.shape == (19,) and np.isfinite(x).all() and np.all((x>=0)&(x<=1))
                    pairs.append((event, label))
            assert [p["call_id"] for p,l in pairs] == list(range(1,907))
            assert len([r for r in journal if r["event"] == "label"]) == 906
            assert Counter(p["workflow"] for p,l in pairs) == {"audited":280, "portfolio":626}
            selections = [r for r in journal if r["event"] == "selection"]
            assert len(selections) == 1
            selection = selections[0]
            assert selection["calls_before_validation"] == 138 and selection["pilot_labels_discarded"]
            selected = select_policy(selection["pilot_endpoints"], cfg["tie_priority"])
            assert selected == summary["selected"] == selection["selected"]
            selection_position = journal.index(selection)
            assert all(journal.index(p)>selection_position for p,l in pairs if p["phase"] == "canonical")
            initial_pairs = {}
            for workflow in ["audited", "portfolio"]:
                init = [(p,l) for p,l in pairs if p["workflow"]==workflow and p["phase"]=="initial"]
                assert len(init)==58
                X0 = np.array([p["x"] for p,l in init]); y0 = np.array([l["y"] for p,l in init])
                history_hash = hashlib.sha256(X0.tobytes()+y0.tobytes()).hexdigest()
                initial_pairs[workflow] = [(p["x"],l["y"]) for p,l in init]
                starts = [r for r in journal if r["event"]=="history_start" and r["workflow"]==workflow]
                assert len(starts)==(5 if workflow=="audited" else 4)
                for start in starts:
                    assert start["initial_sha256"]==history_hash and not start["pilot_labels_in_training"]
                    phase, policy = start["phase"], start["policy"]
                    group = [(p,l) for p,l in pairs if p["workflow"]==workflow and p["phase"]==phase and p["policy"]==policy]
                    steps = 20 if phase=="pilot" else 142
                    assert [p["t"] for p,l in group] == list(range(59,59+steps))
                    curve, incumbent = [float(y0.min())], float(y0.min())
                    for k,(p,l) in enumerate(group):
                        assert p["observations_before"]==58+k and p["best_before"]==incumbent
                        assert p["pool_seed"]==seed(cfg,c,rep,55 if phase=="pilot" else 56,k)
                        incumbent=min(incumbent,l["y"]);curve.append(incumbent)
                    expected = summary["pilots"][policy] if phase=="pilot" else (
                        summary["audited"] if workflow=="audited" else summary["portfolio"][policy])
                    assert curve==expected["curve"] and incumbent==expected["best"]
                assert np.isclose(sum(l["seconds"] for p,l in pairs if p["workflow"]==workflow), summary["fe_seconds"][workflow], rtol=1e-12)
                assert np.isclose(sum(p.get("gp_seconds",0) for p,l in pairs if p["workflow"]==workflow), summary["gp_seconds"][workflow], rtol=1e-12)
            assert initial_pairs["audited"] == initial_pairs["portfolio"]
            assert summary["audited"]["curve"] == summary["portfolio"][selected]["curve"]
            initial, audited = summary["initial_best"], summary["audited"]["best"]
            best = min(v["best"] for v in summary["portfolio"].values())
            row = {"condition":c,"forcedist":cfg["forcedist"][c],"repeat":rep,"selected":selected,
                   "initial_best":initial,"audited_best":audited,"portfolio_best":best,
                   "audited_improvement_percent":100*(1-audited/initial),
                   "portfolio_gap_percent":100*(audited/best-1),
                   "audited_calls":280,"portfolio_calls":626}
            paid_best = min(audited, *(v["best"] for v in summary["pilots"].values()))
            row["all_paid_audited_best"] = paid_best
            row["all_paid_portfolio_gap_percent"] = 100*(paid_best/best-1)
            row["pilot_best_tied_policies"] = sum(v["best"]==min(z["best"] for z in summary["pilots"].values()) for v in summary["pilots"].values())
            for policy in cfg["policies"]:
                row[policy+"_best"] = summary["portfolio"][policy]["best"]
                row[policy+"_pilot_first_improvement_percent"] = 100*(1-summary["pilots"][policy]["curve"][1]/initial)
                row[policy+"_pilot_20_improvement_percent"] = 100*(1-summary["pilots"][policy]["best"]/initial)
            rows.append(row); summaries.append(summary)
            inventories.append({"case":folder.name,"journal_sha256":hashlib.sha256(raw).hexdigest(),
                                "summary_sha256":hashlib.sha256((folder/"summary.json").read_bytes()).hexdigest(),
                                "physical_calls":906,"integrity":"passed"})
    groups, comparisons, pilots = [], [], []
    for c in range(2):
        cases=[r for r in rows if r["condition"]==c]
        median=lambda k:float(np.median([r[k] for r in cases]))
        groups.append({"forcedist":cfg["forcedist"][c],"repeats":10,
                       "initial_compliance_median":median("initial_best"),
                       "audited_compliance_median":median("audited_best"),
                       "portfolio_best_compliance_median":median("portfolio_best"),
                       "audited_improvement_percent_median":median("audited_improvement_percent"),
                       "portfolio_gap_percent_median":median("portfolio_gap_percent"),
                       "portfolio_gap_percent_max":max(r["portfolio_gap_percent"] for r in cases),
                       "all_paid_gap_percent_median_secondary":median("all_paid_portfolio_gap_percent"),
                       "all_paid_compliance_median_secondary":median("all_paid_audited_best"),
                       "pilot_tied_selection_cases":sum(r["pilot_best_tied_policies"]>1 for r in cases),
                       "exact_best_matches":sum(r["portfolio_gap_percent"]==0 for r in cases),
                       "selected_counts":dict(Counter(r["selected"] for r in cases)),
                       "fe_seconds":{w:sum(s["fe_seconds"][w] for s in summaries if s["condition"]==c) for w in ["audited","portfolio"]},
                       "gp_seconds":{w:sum(s["gp_seconds"][w] for s in summaries if s["condition"]==c) for w in ["audited","portfolio"]}})
        for policy in cfg["policies"]:
            effects=[100*(r["audited_best"]/r[policy+"_best"]-1) for r in cases]
            comparisons.append({"forcedist":cfg["forcedist"][c],"policy":policy,"fixed_calls":200,
                                "fixed_compliance_median":median(policy+"_best"),
                                "audit_minus_fixed_ratio_percent_median":float(np.median(effects)),
                                "audit_wins":sum(v<0 for v in effects),"ties":sum(v==0 for v in effects),"audit_losses":sum(v>0 for v in effects)})
            pilots.append({"forcedist":cfg["forcedist"][c],"policy":policy,
                           "first_improvement_percent_median":median(policy+"_pilot_first_improvement_percent"),
                           "20_step_improvement_percent_median":median(policy+"_pilot_20_improvement_percent"),
                           "zero_first_then_positive_20":sum(r[policy+"_pilot_first_improvement_percent"]==0 and r[policy+"_pilot_20_improvement_percent"]>0 for r in cases)})
    result={"complete":True,"cases":20,"new_objective_calls_by_analysis":0,
            "groups":groups,"fixed_policy_comparisons":comparisons,"pilot_horizons":pilots,
            "workflow_costs":{"audited_per_case":280,"portfolio_per_case":626,"fixed_policy_per_case":200,
                              "audit_call_reduction_vs_portfolio_percent":100*(1-280/626),
                              "audit_extra_calls_vs_fixed_percent":40},
            "recovery_accounting":{"prior_transfer_attempts":18120,"retained_recovery_transfer_attempts":18120,
                                   "prior_gp_diagnostic_and_solver_attempts":240,"revision_attempts_including_recovery":36480},
            "inference":"Descriptive, separate conditions; no new p-values, promotion threshold, equivalence or net-savings guarantee",
            "config_sha256":hashlib.sha256(CONFIG.read_bytes()).hexdigest(),"cases_integrity":inventories}
    REPORT.mkdir(parents=True,exist_ok=True)
    write_json(REPORT/"summary.json",result)
    write_json(REPORT/"case_summaries.json",{"cases":summaries})
    for name, data in [("repeat_results.csv",rows),("fixed_policy_comparisons.csv",comparisons),("pilot_horizons.csv",pilots)]:
        with (REPORT/name).open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
    return result


if __name__=="__main__":
    print(json.dumps(analyze(),indent=2))
