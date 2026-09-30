"""Run one independently budgeted CEC2017 confirmation unit."""
import argparse
import json
from pathlib import Path

from .cec2017_adapter import make_problem

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/cec2017_confirmation.json"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", required=True)
    parser.add_argument("--fid", type=int, required=True)
    parser.add_argument("--dim", type=int, required=True)
    parser.add_argument("--rep", type=int, required=True)
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text("utf-8"))
    assert args.method in config["methods"]
    assert args.fid in config["functions"] and args.dim in config["dimensions"]
    assert 0 <= args.rep < config["repeats"]
    budget = config["budget_multiplier"] * args.dim
    out = ROOT / config["out"] / args.method

    if args.method in {"fixed01", "PEM_T"}:
        from . import experiment
        experiment.problem = lambda fid, dim, instance: make_problem(fid, dimension=dim)
        summary = experiment.run_one((args.fid, args.dim, 1, args.rep, args.method,
                                      budget, str(out), config["capture"]))
    elif args.method in {"sobol", "cma_es"}:
        from . import budget_sensitivity_worker as worker
        worker.ioh.get_problem = make_problem
        summary = worker.basic(args.fid, args.dim, 1, args.rep, args.method, budget, out)
    else:
        from . import gp_references
        gp_references.ioh.get_problem = make_problem
        summary = gp_references.run_one(args.fid, args.dim, 1, args.rep,
                                        args.method, budget, out)
    assert summary["algorithm_evaluations"] == budget
    print(json.dumps({"runid": summary["runid"], "benchmark": "CEC2017",
                      "method": args.method, "budget": budget}))


if __name__ == "__main__":
    main()
