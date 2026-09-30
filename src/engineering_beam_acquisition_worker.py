"""Run one matched-initialization GP-PI or GP-UCB beam unit."""
import argparse
import json
from pathlib import Path

from .engineering_beam_shared_init import run_one

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/engineering_beam_acquisition_refs.json"


def main():
    cfg = json.loads(CONFIG.read_text("utf-8"))
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", choices=cfg["methods"], required=True)
    parser.add_argument("--rep", type=int, choices=range(cfg["repeats"]), required=True)
    args = parser.parse_args()
    result = run_one(args.method, args.rep, cfg)
    print(json.dumps({key: result[key] for key in
                      ["runid", "algorithm_evaluations", "reused_initial_evaluations",
                       "new_physical_evaluations", "best", "elapsed"]}, indent=2))


if __name__ == "__main__":
    main()
