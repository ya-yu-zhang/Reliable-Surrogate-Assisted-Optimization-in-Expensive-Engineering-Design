"""Configuration-isolated launcher with strict Python module process recognition."""
import argparse
from pathlib import Path
import re
import sys
from . import resume_interrupted_gp_batch_v2 as driver

PYTHON_MODULE = re.compile(r'^\s*(?:"[^"]*python(?:\.exe)?"|\S*python(?:\.exe)?)\s+-m\s+src\.resume_interrupted_gp_batch_v(?:2|3)_parallel\b',re.I)


def matching_inventory(rows,config):
    normalized=str(Path(config)).lower().replace('/','\\');basename=Path(config).name.lower()
    selected=[]
    for row in rows:
        command=row['CommandLine'] or ''
        if PYTHON_MODULE.search(command) and (normalized in command.lower().replace('/','\\') or basename in command.lower()):
            selected.append(row)
    return selected


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',required=True);args=parser.parse_args()
    original=driver.process_inventory
    driver.process_inventory=lambda:matching_inventory(original(),args.config)
    sys.argv=[sys.argv[0],'--config',args.config]
    driver.main()


if __name__=='__main__':main()
