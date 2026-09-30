"""PID-safe entry for one frozen high-dimensional resource worker."""
import argparse
from . import application_high_method_resource as worker
from . import application_high_precheck as gate
from .build_integrated_manuscripts_pid_safe import pid_safe_inventory

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--method",required=True);args=parser.parse_args()
    original=gate.process_inventory;gate.process_inventory=lambda:pid_safe_inventory(gate.ROOT,original())
    worker.prerequisite=gate.prerequisite;worker.run(args.method)
if __name__=="__main__":main()
