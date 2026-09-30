"""Run one strict-budget EngiBench Beams2D optimization unit."""
import argparse
import json
from pathlib import Path
from .engineering_beam_adapter import make_problem

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/engineering_beam_formal.json"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", required=True)
    parser.add_argument("--rep", type=int, required=True)
    parser.add_argument("--budget", type=int)
    parser.add_argument("--out")
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text("utf-8"))
    assert args.method in config["methods"] and 0 <= args.rep < config["repeats"]
    budget = args.budget or config["budget"]
    out = ROOT / (args.out or config["out"]) / args.method
    dim, fid, instance = config["dimension"], 1, 1

    if args.method in {"greedy", "fixed01", "PEM_T"}:
        from . import experiment
        experiment.problem = lambda fid, dim, instance: make_problem()
        summary = experiment.run_one((fid, dim, instance, args.rep, args.method,
                                      budget, str(out), config["capture"]))
    else:
        from . import gp_references
        gp_references.ioh.get_problem = make_problem
        summary = gp_references.run_one(fid, dim, instance, args.rep, args.method, budget, out)
    assert summary["algorithm_evaluations"] == budget
    print(json.dumps({"runid": summary["runid"], "method": args.method,
                      "budget": budget, "benchmark": config["benchmark"]}))


if __name__ == "__main__":
    main()
