"""Invoke the frozen high-resource gate after filtering unrelated reused prerequisite PIDs."""

from . import application_high_precheck as gate
from .build_integrated_manuscripts_pid_safe import pid_safe_inventory


def main():
    original = gate.process_inventory
    gate.process_inventory = lambda: pid_safe_inventory(gate.ROOT, original())
    gate.main()


if __name__ == "__main__":
    main()
