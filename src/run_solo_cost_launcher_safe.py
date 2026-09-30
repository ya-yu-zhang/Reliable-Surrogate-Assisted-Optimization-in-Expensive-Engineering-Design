"""Launch the frozen solo-cost runner without mistaking its venv ancestor for overlap."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

from . import run_solo_cost as frozen_runner


MODULES = [
    "src.run_gp_batch",
    "src.gp_references",
    "src.gp_precheck_pipeline",
    "src.mechanism_pipeline",
    "src.experiment",
    "src.diagnostics",
    "src.basic_references",
    "src.run_solo_cost",
    "src.run_solo_cost_launcher_safe",
    "src.solo_cost",
]


def process_inventory_with_parents() -> list[dict]:
    shell = Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    command = (
        "Get-CimInstance Win32_Process | "
        "Select-Object ProcessId,ParentProcessId,CommandLine | ConvertTo-Json -Compress"
    )
    result = subprocess.run(
        [str(shell), "-NoProfile", "-NonInteractive", "-Command", command],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=subprocess.CREATE_NO_WINDOW,
        check=True,
    )
    entries = json.loads(result.stdout)
    return [entries] if isinstance(entries, dict) else entries


def ancestor_pids(entries: list[dict], current_pid: int) -> set[int]:
    parents = {int(row["ProcessId"]): int(row.get("ParentProcessId") or 0) for row in entries}
    ancestors: set[int] = set()
    cursor = parents.get(current_pid, 0)
    while cursor and cursor not in ancestors:
        ancestors.add(cursor)
        cursor = parents.get(cursor, 0)
    return ancestors


def find_overlaps(entries: list[dict], current_pid: int) -> list[dict]:
    excluded = ancestor_pids(entries, current_pid) | {current_pid}
    return [
        row
        for row in entries
        if int(row["ProcessId"]) not in excluded
        and any("-m " + module in (row.get("CommandLine") or "") for module in MODULES)
    ]


def refuse_overlap() -> None:
    active = find_overlaps(process_inventory_with_parents(), os.getpid())
    if active:
        raise RuntimeError(
            "Scientific processes still active; refusing overlap: "
            + ",".join(str(row["ProcessId"]) for row in active)
        )


def main() -> None:
    frozen_runner.refuse_overlap = refuse_overlap
    frozen_runner.main()


if __name__ == "__main__":
    main()
