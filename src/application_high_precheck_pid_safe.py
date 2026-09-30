"""Run the frozen high-dimensional resource precheck with PID identity filtering."""

from . import application_high_precheck as precheck
from .build_integrated_manuscripts_pid_safe import pid_safe_inventory


def main():
    original = precheck.process_inventory
    precheck.process_inventory = lambda: pid_safe_inventory(precheck.ROOT, original())
    precheck.main()


if __name__ == "__main__":
    main()
