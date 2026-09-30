"""Replay a numerically equivalent CMA-ES paid prefix and query only its suffix."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from time import perf_counter
from unittest.mock import patch

import numpy as np


ROOT = Path(__file__).resolve().parents[1]


def parse_paid_prefix(path: Path) -> tuple[dict, list[dict], list[dict], dict | None, bytes]:
    raw = path.read_bytes()
    events = [json.loads(line) for line in raw.decode("utf-8").splitlines()]
    assert events and events[0]["event"] == "meta"
    payload = events[1:]
    dangling = None
    if len(payload) % 2:
        dangling = payload[-1]
        assert dangling["event"] == "pre"
        payload = payload[:-1]
    pre = payload[0::2]
    labels = payload[1::2]
    assert len(pre) == len(labels) and 0 < len(labels) < events[0]["budget"]
    for t, (proposal, label) in enumerate(zip(pre, labels), 1):
        assert proposal["event"] == "pre" and label["event"] == "label"
        assert proposal["t"] == label["t"] == t and proposal["n_observed"] == t - 1
        assert "y" not in proposal and np.isfinite(label["y"])
    if dangling is not None:
        assert dangling["t"] == len(labels) + 1 and dangling["n_observed"] == len(labels)
    return events[0], pre, labels, dangling, raw


def comparable(event: dict) -> dict:
    result = dict(event)
    result.pop("preparation_seconds", None)
    return result


def equivalent(left: dict, right: dict) -> bool:
    a = comparable(left)
    b = comparable(right)
    assert set(a) == set(b)
    for key in a:
        if key in {"x", "x_unit"}:
            if not np.allclose(np.asarray(a[key]), np.asarray(b[key]), rtol=0, atol=2e-12):
                return False
        elif a[key] != b[key]:
            return False
    return True


def tail_events(path: Path) -> list[dict]:
    with path.open("rb") as stream:
        stream.seek(0, 2)
        end = stream.tell()
        stream.seek(max(0, end - 131072))
        lines = stream.read().splitlines()
    return [json.loads(line) for line in lines[-2:]]


def recover(config_path: str, dataset: str, rep: int, method: str, archive: Path) -> dict:
    config = json.loads((ROOT / config_path).read_text("utf-8"))
    budget = config["budgets"][dataset]
    runid = f"{method}_{dataset}_r{rep:02}_b{budget}"
    meta, old_pre, old_labels, dangling, original_bytes = parse_paid_prefix(archive / "events.jsonl")
    paid = len(old_labels)
    assert all(meta[key] == value for key, value in {
        "dataset": dataset,
        "rep": rep,
        "method": method,
        "budget": budget,
    }.items())
    directory = ROOT / config["out"] / runid
    assert not directory.exists(), "Partial directory must be archived before recovery"
    directory.mkdir(parents=True)
    physical_path = directory / "recovery_physical_calls.jsonl"
    instances = []

    from . import application_experiment as worker
    from .application_methods import PaidObjective

    with physical_path.open("w", encoding="utf-8") as physical:
        class ReplayObjective:
            def __init__(self, function, lb, ub, requested_budget):
                assert requested_budget == budget and not instances
                self.real = PaidObjective(function, lb, ub, requested_budget)
                self.lb = self.real.lb
                self.ub = self.real.ub
                self.budget = requested_budget
                self.calls = 0
                self.points = []
                self.values = []
                self.objective_seconds = 0.0
                self.replayed = 0
                self.new_calls = 0
                instances.append(self)

            def __call__(self, point):
                point = np.asarray(point, dtype=float)
                index = self.calls
                assert index < self.budget
                prior, current = tail_events(directory / "events.jsonl")
                assert current["event"] == "pre" and current["t"] == index + 1
                if index == 0:
                    assert prior == meta
                if index < paid:
                    assert equivalent(current, old_pre[index])
                    np.testing.assert_allclose(point, np.asarray(old_pre[index]["x"]), rtol=0, atol=2e-12)
                    value = float(old_labels[index]["y"])
                    self.replayed += 1
                else:
                    if index == paid and dangling is not None:
                        assert equivalent(current, dangling)
                    assert self.replayed == paid
                    physical.write(json.dumps({
                        "event": "pre", "t": index + 1, "old_paid_calls": paid,
                        "new_paid_calls": self.new_calls, "x": point.tolist(),
                    }) + "\n")
                    physical.flush()
                    tick = perf_counter()
                    value = float(self.real.function(point.copy()))
                    self.objective_seconds += perf_counter() - tick
                    assert np.isfinite(value)
                    self.new_calls += 1
                    physical.write(json.dumps({
                        "event": "label", "t": index + 1, "y": value,
                        "new_paid_calls": self.new_calls,
                    }) + "\n")
                    physical.flush()
                self.calls += 1
                self.points.append(point.copy())
                self.values.append(value)
                return value

        with patch.object(worker, "PaidObjective", ReplayObjective):
            summary = worker.run_one(config_path, dataset, rep, method)
        oracle = instances[0]
        assert oracle.calls == budget and oracle.replayed == paid
        assert oracle.new_calls == budget - paid

    regenerated = [json.loads(line) for line in (directory / "events.jsonl").read_text("utf-8").splitlines()]
    assert regenerated[0] == meta
    old_prefix = [item for pair in zip(old_pre, old_labels) for item in pair]
    for left, right in zip(regenerated[1:1 + 2 * paid], old_prefix):
        assert equivalent(left, right)
    if dangling is not None:
        assert equivalent(regenerated[1 + 2 * paid], dangling)
    record = {
        "schema": "application_paid_prefix_recovery_v2",
        "runid": runid,
        "archive": archive.relative_to(ROOT).as_posix(),
        "original_journal_sha256": hashlib.sha256(original_bytes).hexdigest(),
        "old_paid_calls": paid,
        "new_paid_calls": budget - paid,
        "dangling_unpaid_pre_reproduced": dangling is not None,
        "complete_prefix_states_and_labels_numerically_equivalent": True,
        "candidate_absolute_tolerance": 2e-12,
        "optimizer_source_unchanged": True,
        "post_completion_test_calls": summary["test_method_calls"],
        "objective_timing_scope": "new_suffix_only",
        "optimization_timing_scope": "full_deterministic_replay_plus_new_suffix",
    }
    (directory / "recovery.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/application_formal.json")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--rep", type=int, required=True)
    parser.add_argument("--method", required=True)
    parser.add_argument("--archive", required=True)
    args = parser.parse_args()
    print(json.dumps(recover(args.config, args.dataset, args.rep, args.method, Path(args.archive)), indent=2))


if __name__ == "__main__":
    main()

