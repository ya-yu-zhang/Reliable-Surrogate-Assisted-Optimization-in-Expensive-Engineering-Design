"""Run one matched-initialization engineering beam unit."""
import argparse
import json
from .engineering_beam_shared_init import CONFIG, run_one


def main():
    cfg = json.loads(CONFIG.read_text("utf-8"))
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", choices=cfg["methods"], required=True)
    parser.add_argument("--rep", type=int, choices=range(cfg["repeats"]), required=True)
    args = parser.parse_args()
    result = run_one(args.method, args.rep, cfg)
    print(json.dumps({k: result[k] for k in ["runid", "algorithm_evaluations",
                                             "reused_initial_evaluations",
                                             "new_physical_evaluations", "elapsed"]}, indent=2))


if __name__ == "__main__":
    main()
