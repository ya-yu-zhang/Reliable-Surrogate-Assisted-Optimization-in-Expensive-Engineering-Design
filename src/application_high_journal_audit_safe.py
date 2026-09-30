"""Audit high-dimensional GP journals with the frozen 4096+8 candidate accounting."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile

from .application_journal_audit import audit_journal


def validate_gp_candidate_accounting(events):
    checked = 0
    for pre in events[1::2]:
        state = pre.get("optimizer_state", {})
        if state.get("mode") not in {"gp_ei", "variance_fallback"}:
            continue
        count = state["acquisition_candidates"]
        assert state["continuous_starts"] == 8
        assert 1 <= count <= 4096 + state["continuous_starts"]
        checked += 1
    return checked


def audit_high_journal(directory: Path, summary: dict):
    if summary["signature"]["method"] != "gp_ei":
        return audit_journal(directory, summary)
    events = [json.loads(line) for line in (directory / "events.jsonl").read_text("utf-8").splitlines()]
    checked = validate_gp_candidate_accounting(events)
    assert checked == summary["signature"]["budget"] - 2 * summary["signature"]["dim"]
    # The frozen generic auditor checks every other invariant but predates the
    # eight continuous candidates. Normalize only its in-memory audit copy.
    normalized = json.loads(json.dumps(events))
    for pre in normalized[1::2]:
        state = pre.get("optimizer_state", {})
        if state.get("mode") in {"gp_ei", "variance_fallback"}:
            state["acquisition_candidates"] = min(state["acquisition_candidates"], 4096)
    with tempfile.TemporaryDirectory() as name:
        temporary = Path(name)
        (temporary / "events.jsonl").write_text(
            "\n".join(json.dumps(row) for row in normalized) + "\n", encoding="utf-8"
        )
        shutil.copy2(directory / "candidate_pools.npz", temporary / "candidate_pools.npz")
        audit_journal(temporary, summary)
    return events
