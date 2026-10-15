"""Reproduce into a fresh directory without replacing the recorded execution."""
import argparse
from pathlib import Path
from threadpoolctl import threadpool_limits
from . import run_positive_rollout_v2 as work


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True,help="A new output directory")
    parser.add_argument("--paid-replay",action="store_true")
    args=parser.parse_args()
    destination=Path(args.out).resolve()
    if destination.exists():
        parser.error("Output directory already exists; preserve recorded runs")
    work.OUT=destination
    with threadpool_limits(limits=1):
        work.run()
        if args.paid_replay:
            from . import replay_positive_rollout_v2 as replay
            replay.OUT=destination
            replay.run()


if __name__=="__main__":
    main()
