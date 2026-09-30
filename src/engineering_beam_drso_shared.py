"""Matched-initialization adapter for the frozen author-code DRSO baseline."""
import argparse
from collections import Counter
import hashlib
import importlib.metadata
import json
from pathlib import Path
import random
import sys
from time import perf_counter
import warnings

import numpy as np

from .engineering_beam_adapter import make_problem
from .engineering_beam_shared_init import (ROOT, file_sha256, inject_shared_archive,
                                           memory_peak, shared_archive)
from .gp_references import BudgetJournal

CONFIG = ROOT / "configs/engineering_beam_drso_shared_init.json"
AUTHOR = ROOT / "literature/source-code/Relation"
COMPAT = ROOT / "compat"


def tree_hash(path):
    digest = hashlib.sha256()
    for item in sorted(Path(path).rglob("*")):
        if item.is_file() and ".git" not in item.parts and "__pycache__" not in item.parts:
            digest.update(item.relative_to(path).as_posix().encode())
            digest.update(item.read_bytes())
    return digest.hexdigest()


def adapter_hash():
    digest = hashlib.sha256()
    for path in [Path(__file__), CONFIG, ROOT / "compat/imp.py",
                 ROOT / "compat/savedata/__init__.py", ROOT / "compat/savedata/call_back.py",
                 ROOT / "src/engineering_beam_shared_init.py",
                 ROOT / "src/engineering_beam_adapter.py"]:
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def run_one(rep, cfg=None):
    cfg = cfg or json.loads(CONFIG.read_text("utf-8"))
    method = "drso_shared_init"
    dim, budget = cfg["dimension"], cfg["budget"]
    seed = 100000 * dim + 1000 + 10 + rep
    runid = f"{method}_f01_d{dim}_i1_r{rep}_b{budget}"
    directory = ROOT / cfg["out"] / method / runid
    directory.mkdir(parents=True, exist_ok=True)
    points, values, archive_digest, source_log = shared_archive(rep, cfg)
    author_hash = tree_hash(AUTHOR)
    signature = {"fid": 1, "dim": dim, "instance": 1, "rep": rep,
                 "method": method, "budget": budget, "seed": seed,
                 "adapter_hash": adapter_hash(), "author_tree_hash": author_hash,
                 "author_commit": cfg["author_commit"],
                 "source_archive_sha256": archive_digest,
                 "source_log_sha256": file_sha256(source_log),
                 "shared_initial_evaluations": len(values), "population_size": cfg["population_size"],
                 "tao": cfg["tao"], "packages": {name: importlib.metadata.version(name) for name in
                 ["numpy", "scipy", "scikit-learn", "pymoo", "pyDOE2", "xgboost"]}}
    summary_path = directory / "summary.json"
    if summary_path.exists():
        result = json.loads(summary_path.read_text("utf-8"))
        if result["signature"] != signature:
            raise RuntimeError(f"stale result: {directory}")
        return result

    # The compatibility path supplies only the removed Python 3.12 imp name.
    # The author repository itself is imported without source modifications.
    sys.path.insert(0, str(COMPAT)); sys.path.insert(0, str(AUTHOR))
    from loguru import logger
    from pymoo.core.problem import Problem
    from pymoo.optimize import minimize
    from algorithm.saea.drso import DRSO
    logger.remove()

    objective = make_problem()
    random.seed(seed); np.random.seed(seed)
    warning_counts = Counter(); started = perf_counter()
    with (directory / "events.jsonl").open("w", encoding="utf-8") as journal, warnings.catch_warnings():
        warnings.simplefilter("always")
        oracle = BudgetJournal(objective, budget, objective.bounds.lb, objective.bounds.ub, journal)
        oracle.write({"event": "meta", **signature, "schema": 1})
        inject_shared_archive(oracle, points, values, archive_digest)

        class BeamProblem(Problem):
            def __init__(self):
                super().__init__(n_var=dim, n_obj=1, xl=np.zeros(dim), xu=np.ones(dim))
                self.initial_pending = True

            def _evaluate(self, x, out, *args, **kwargs):
                x = np.atleast_2d(np.asarray(x, dtype=float))
                if self.initial_pending:
                    if x.shape != points.shape or not np.array_equal(x, points):
                        raise AssertionError("DRSO initial population differs from shared archive")
                    self.initial_pending = False
                    out["F"] = values[:, None]
                else:
                    out["F"] = np.asarray([oracle(row) for row in x], dtype=float)[:, None]

        algorithm = DRSO(pop_size=cfg["population_size"], tao=cfg["tao"], sample=points)
        result = minimize(BeamProblem(), algorithm, ("n_evals", budget), seed=seed,
                          verbose=False, copy_algorithm=False)
    if algorithm.evaluator.n_eval != budget or len(oracle.values) != budget:
        raise AssertionError("algorithm budget mismatch")
    expected_physical = budget - len(values)
    if objective.state.evaluations != expected_physical:
        raise AssertionError("physical objective counter mismatch")
    observed = np.asarray(oracle.values)
    payload = {"signature": signature, "runid": runid, "algorithm_evaluations": budget,
               "reused_initial_evaluations": len(values),
               "new_physical_evaluations": objective.state.evaluations,
               "best": float(observed.min()), "error": float(observed.min()),
               "initial_best": float(values.min()),
               "normalized_error": float(observed.min() / values.min()),
               "elapsed": perf_counter() - started, "objective_seconds": oracle.objective_seconds,
               "preparation_seconds": oracle.prepare_seconds,
               "process_peak_working_set_bytes": memory_peak(),
               "exact_duplicate_calls": budget - len(np.unique(np.asarray(oracle.points), axis=0)),
               "warning_counts": dict(warning_counts), "pymoo_n_eval": algorithm.evaluator.n_eval,
               "author_result_best": float(np.asarray(result.F).reshape(-1)[0])}
    summary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def main():
    cfg = json.loads(CONFIG.read_text("utf-8"))
    parser = argparse.ArgumentParser(); parser.add_argument("--rep", type=int, choices=range(cfg["repeats"]), required=True)
    args = parser.parse_args(); result = run_one(args.rep, cfg)
    print(json.dumps({key: result[key] for key in ["runid", "best", "elapsed",
          "algorithm_evaluations", "new_physical_evaluations"]}, indent=2))


if __name__ == "__main__":
    main()
