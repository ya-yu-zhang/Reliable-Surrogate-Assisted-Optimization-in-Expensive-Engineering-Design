"""Launch the fifth-interruption manifest-driven GP-EI recovery."""

from __future__ import annotations

import argparse

from .resume_manifest_gp_batch import run


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    run(
        args.config,
        "results/interruption_20260921_v5",
        "src.resume_interrupted_gp_batch_v6_parallel",
        "recovery_driver_v6.json",
        ".recovery-v6",
    )


if __name__ == "__main__":
    main()
