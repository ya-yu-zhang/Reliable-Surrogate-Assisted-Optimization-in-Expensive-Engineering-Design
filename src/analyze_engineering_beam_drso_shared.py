"""Audit author-code DRSO and rebuild the complete matched-history comparison."""
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from .engineering_beam_adapter import density_field
from .engineering_beam_drso_shared import CONFIG, ROOT, adapter_hash, tree_hash
from .engineering_beam_shared_init import audit_shared_sources, shared_archive

DRSO = ROOT / "results/engineering_beam_drso_shared_init_v1"
ACQ = ROOT / "results/engineering_beam_acquisition_refs_v1"
OLD = ROOT / "results/engineering_beam_shared_init_v1"
SOURCE = ROOT / "results/engineering_beam_formal_v1"


def run_dir(base, method, rep, dim=19, budget=200):
    return Path(base) / method / f"{method}_f01_d{dim}_i1_r{rep}_b{budget}"


def events(path):
    return [json.loads(line) for line in Path(path).read_text("utf-8").splitlines() if line.strip()]


def curve(base, method, rep):
    y = [row["y"] for row in events(run_dir(base, method, rep) / "events.jsonl") if row.get("event") == "label"]
    return np.minimum.accumulate(np.asarray(y))


def holm(raw):
    raw = np.asarray(raw); order = np.argsort(raw); out = np.empty(len(raw)); running = 0.0
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (len(raw) - rank) * raw[index])); out[index] = running
    return out


def main():
    cfg = json.loads(CONFIG.read_text("utf-8")); issues=[]; rows=[]
    author_hash=tree_hash(ROOT/"literature/source-code/Relation"); adapt_hash=adapter_hash()
    for rep in range(cfg["repeats"]):
        directory=run_dir(DRSO,"drso_shared_init",rep); summary=json.loads((directory/"summary.json").read_text("utf-8"))
        stream=events(directory/"events.jsonl"); pre=[x for x in stream if x.get("event")=="pre"]; lab=[x for x in stream if x.get("event")=="label"]
        points, initial, digest, _=shared_archive(rep,cfg); x=np.asarray([e["x"] for e in pre]); y=np.asarray([e["y"] for e in lab])
        checks={"meta":sum(e.get("event")=="meta" for e in stream)==1,"pre":len(pre)==200,"labels":len(lab)==200,
                "pre_order":[e["t"] for e in pre]==list(range(1,201)),"label_order":[e["t"] for e in lab]==list(range(1,201)),
                "shared_x":np.array_equal(x[:58],points),"shared_y":np.array_equal(y[:58],initial),
                "archive_hash":summary["signature"]["source_archive_sha256"]==digest,
                "author_hash":summary["signature"]["author_tree_hash"]==author_hash,
                "adapter_hash":summary["signature"]["adapter_hash"]==adapt_hash,
                "commit":summary["signature"]["author_commit"]==cfg["author_commit"],
                "finite":np.isfinite(x).all() and np.isfinite(y).all(),"bounds":np.all((x>=0)&(x<=1)),
                "algorithm_budget":summary["algorithm_evaluations"]==200,"pymoo_budget":summary["pymoo_n_eval"]==200,
                "physical":summary["new_physical_evaluations"]==142,"duplicates":summary["exact_duplicate_calls"]==0,
                "best":summary["best"]==float(y.min()),"author_best":summary["author_result_best"]==summary["best"]}
        if not all(checks.values()): issues.append({"rep":rep,"failed":[k for k,v in checks.items() if not v]})
        pem=json.loads((run_dir(SOURCE,"PEM_T",rep)/"summary.json").read_text("utf-8"))
        rows.append({"rep":rep,"best":summary["best"],"initial_best":summary["initial_best"],
                     "improvement_fraction":1-summary["best"]/summary["initial_best"],
                     "pem_t_best":pem["best"],"difference_vs_pem_t":summary["best"]-pem["best"],
                     "elapsed_seconds":summary["elapsed"],"duplicates":summary["exact_duplicate_calls"]})
    frame=pd.DataFrame(rows); frame.to_csv(DRSO/"paired_results.csv",index=False)
    best=frame.best.to_numpy(); diff=frame.difference_vs_pem_t.to_numpy(); stat,p=wilcoxon(diff,zero_method="wilcox",alternative="two-sided")
    summary={"method":"DRSO","median":float(np.median(best)),"q25":float(np.quantile(best,.25)),"q75":float(np.quantile(best,.75)),
             "median_improvement_fraction":float(np.median(frame.improvement_fraction)),
             "median_difference_vs_pem_t":float(np.median(diff)),"wins":int(np.sum(diff<0)),"ties":int(np.sum(diff==0)),
             "losses":int(np.sum(diff>0)),"wilcoxon_statistic":float(stat),"raw_p":float(p)}
    (DRSO/"method_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")

    acq=pd.read_csv(ACQ/"paired_tests.csv"); family=pd.DataFrame([
        {"method":"GP-PI","raw_p":float(acq.loc[acq.method=="gp_pi_shared_init","p_value"].iloc[0])},
        {"method":"GP-UCB","raw_p":float(acq.loc[acq.method=="gp_ucb_shared_init","p_value"].iloc[0])},
        {"method":"DRSO","raw_p":float(p)}])
    family["holm_p"]=holm(family.raw_p.to_numpy()); family.to_csv(DRSO/"added_control_holm_family.csv",index=False)

    methods=["PEM_T","fixed01","greedy","gp_ei_shared_init","gp_pi_shared_init","gp_ucb_shared_init","drso_shared_init","turbo_1_shared_init"]
    labels={"PEM_T":"PEM-T","fixed01":"Fixed-0.1","greedy":"Greedy","gp_ei_shared_init":"GP-EI","gp_pi_shared_init":"GP-PI",
            "gp_ucb_shared_init":"GP-UCB","drso_shared_init":"DRSO","turbo_1_shared_init":"TuRBO-1"}
    colors={"PEM_T":"#c0392b","fixed01":"#2980b9","greedy":"#7f8c8d","gp_ei_shared_init":"#8e44ad","gp_pi_shared_init":"#d68910",
            "gp_ucb_shared_init":"#2471a3","drso_shared_init":"#6c3483","turbo_1_shared_init":"#16a085"}
    bases={m:(DRSO if m=="drso_shared_init" else ACQ if m in {"gp_pi_shared_init","gp_ucb_shared_init"} else OLD if "shared_init" in m else SOURCE) for m in methods}
    fig,ax=plt.subplots(figsize=(7.5,4.7)); xx=np.arange(1,201)
    for method in methods:
        data=np.asarray([curve(bases[method],method,rep) for rep in range(10)]); med=np.median(data,axis=0); q1,q3=np.quantile(data,[.25,.75],axis=0)
        ax.plot(xx,med,label=labels[method],color=colors[method],linewidth=1.65); ax.fill_between(xx,q1,q3,color=colors[method],alpha=.09,linewidth=0)
    ax.axvline(58,color="black",linestyle="--",linewidth=.9); ax.set_yscale("log"); ax.set_xlabel("Finite-element evaluations"); ax.set_ylabel("Best compliance so far")
    ax.grid(True,which="both",alpha=.2); ax.legend(frameon=False,fontsize=7.3,ncol=2); fig.tight_layout()
    fig.savefig(DRSO/"complete_shared_initialization_convergence.png",dpi=600); fig.savefig(DRSO/"complete_shared_initialization_convergence.pdf"); plt.close(fig)

    design_methods=["PEM_T","fixed01","greedy","gp_ei_shared_init","gp_pi_shared_init","gp_ucb_shared_init","drso_shared_init","turbo_1_shared_init"]
    fig,axes=plt.subplots(2,4,figsize=(10.5,5.0),constrained_layout=True)
    for ax,method in zip(axes.flat,design_methods):
        endpoints=[]
        for rep in range(10):
            stream=events(run_dir(bases[method],method,rep)/"events.jsonl"); pre={e["t"]:e for e in stream if e.get("event")=="pre"}; obs={e["t"]:e["y"] for e in stream if e.get("event")=="label"}; t=min(obs,key=obs.get); endpoints.append((obs[t],rep,pre[t]["x"]))
        endpoints.sort(key=lambda z:z[0]); value,rep,point=endpoints[len(endpoints)//2]
        image=ax.imshow(density_field(point),cmap="gray_r",vmin=0,vmax=1,aspect="auto"); ax.set_title(f"{labels[method]}\nrep {rep}; {value:.1f}",fontsize=8); ax.axis("off")
    fig.colorbar(image,ax=axes,fraction=.018,pad=.02,label="Density"); fig.savefig(DRSO/"complete_representative_designs.png",dpi=600); fig.savefig(DRSO/"complete_representative_designs.pdf"); plt.close(fig)
    audit={"status":"pass" if not issues else "fail","runs":10,"algorithm_evaluations":2000,"reused_initial_evaluations":580,
           "new_physical_evaluations":1420,"author_commit":cfg["author_commit"],"author_tree_hash":author_hash,"adapter_hash":adapt_hash,
           "shared_sources":audit_shared_sources(cfg),"issues":issues,"summary":summary,"holm_family":family.to_dict(orient="records")}
    (DRSO/"audit.json").write_text(json.dumps(audit,indent=2),encoding="utf-8"); print(json.dumps(audit,indent=2))
    if issues: raise SystemExit(1)


if __name__=="__main__": main()
