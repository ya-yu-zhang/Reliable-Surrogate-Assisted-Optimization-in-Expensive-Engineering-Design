"""Generate scientific figures from validated per-repeat records, without FE calls."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from .engineering_optimization_transfer import ROOT


def plot():
    report=ROOT/"paper/engineering_optimization/transfer_validation"
    data=json.loads((report/"case_summaries.json").read_text())["cases"]
    out=ROOT/"paper/engineering_optimization/figures";out.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({"font.size":9,"axes.spines.top":False,"axes.spines.right":False})
    fig, axes=plt.subplots(1,2,figsize=(10,3.4),layout="constrained")
    methods=["mean","ei","pi","lcb","audited","portfolio"]
    labels=["Mean\n200","EI\n200","PI\n200","LCB\n200","Selected\n280","Portfolio\n626"]
    for cond,ax in enumerate(axes):
        cases=[s for s in data if s["condition"]==cond]
        arrays=[]
        for m in methods:
            arrays.append([100*(1-(s["audited"]["best"] if m=="audited" else
                                   min(v["best"] for v in s["portfolio"].values()) if m=="portfolio" else
                                   s["portfolio"][m]["best"])/s["initial_best"]) for s in cases])
        for i,arr in enumerate(arrays):
            q=np.quantile(arr,[.25,.5,.75]);ax.errorbar(i,q[1],yerr=[[q[1]-q[0]],[q[2]-q[1]]],
                fmt="o",capsize=4,color="#075985" if i<4 else "#c2410c" if i==4 else "#166534")
        ax.set_xticks(range(6),labels);ax.set_title(f"Force position {cases[0]['forcedist']:.2f}; n=10")
        ax.set_ylim(-5,100);ax.grid(axis="y",alpha=.2);ax.set_xlabel("Workflow / physical FE calls per repeat")
    axes[0].set_ylabel("Improvement from initial incumbent (%)")
    for extension in ["png","svg"]:fig.savefig(out/f"transfer_cost_performance.{extension}",dpi=300)
    plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(9,3.3),layout="constrained")
    for cond,ax in enumerate(axes):
        cases=[s for s in data if s["condition"]==cond]
        for policy in methods[:4]:
            a=np.array([[100*(1-v/s["initial_best"]) for v in s["pilots"][policy]["curve"]] for s in cases])
            ax.plot(range(21),np.median(a,axis=0),label=policy.upper())
        ax.set_title(f"Force position {cases[0]['forcedist']:.2f}");ax.set_xlim(0,20);ax.set_ylim(0,65)
        ax.set_xlabel("Postinitial pilot steps");ax.grid(alpha=.2)
    axes[0].set_ylabel("Median incumbent improvement (%)");axes[1].legend(frameon=False)
    for extension in ["png","svg"]:fig.savefig(out/f"transfer_pilot_horizons.{extension}",dpi=300)
    plt.close(fig)
    return {"figures":2,"new_objective_calls":0,"sources":"validated case_summaries.json"}


if __name__=="__main__":print(json.dumps(plot()))
