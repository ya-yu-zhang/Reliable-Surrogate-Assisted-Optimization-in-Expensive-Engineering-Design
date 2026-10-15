"""Reproduce the frozen algorithm in a fresh directory without physical calls."""
import argparse
from pathlib import Path
from threadpoolctl import threadpool_limits
from . import run_lazy_regional_rollout as frozen


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();frozen.OUT=args.out.resolve()
    with threadpool_limits(limits=1):frozen.run()
