"""Source-isolated launcher allowing the two already-independent frozen batches concurrently."""
import argparse
from pathlib import Path
import sys
from . import resume_interrupted_gp_batch_v2 as driver


def matching_inventory(rows, config):
    normalized=str(Path(config)).lower().replace('/','\\')
    basename=Path(config).name.lower()
    return [row for row in rows if normalized in (row['CommandLine'] or '').lower().replace('/','\\')
            or basename in (row['CommandLine'] or '').lower()]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',required=True);args=parser.parse_args()
    original=driver.process_inventory
    driver.process_inventory=lambda:matching_inventory(original(),args.config)
    sys.argv=[sys.argv[0],'--config',args.config]
    driver.main()


if __name__=='__main__':main()
