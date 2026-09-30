"""Recover the frozen high-dimensional chain after a zero-call PID-reuse refusal."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
from time import perf_counter


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/high_extension_completion_v1"


def verify(path):
    rows = json.loads(path.read_text("utf-8"))
    assert all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
               for name, digest in rows.items())


def main():
    assert not OUT.exists(), "High extension completion record exists; refuse duplicate restart"
    verify(ROOT / "docs/frozen_high_evidence_export_v1/sha256.json")
    verify(ROOT / "docs/frozen_application_high_formal_v1/sha256.json")
    verify(ROOT / "docs/frozen_high_pid_safe_recovery_v1/sha256.json")
    OUT.mkdir(parents=True); start = perf_counter(); stage = "six_point_resource_check"; failure = None

    def save():
        def runs(path):
            return json.loads(path.read_text("utf-8"))["runs"] if path.exists() else 0
        (OUT / "status.json").write_text(json.dumps({
            "stage": stage, "pid": os.getpid(), "elapsed": perf_counter() - start,
            "failure": failure,
            "resource_point_calls": 6 if (ROOT / "results/application_high_precheck_analysis_v1/audit.json").exists() else 0,
            "full_method_resource_runs": runs(ROOT / "results/application_high_method_resource_analysis_v1/audit.json"),
            "formal_runs": runs(ROOT / "results/application_high_analysis_v1/audit.json"),
        }, indent=2), encoding="utf-8")

    def execute(python, module, log):
        result = subprocess.run([str(python), "-m", module], cwd=ROOT, capture_output=True,
                                text=True, encoding="utf-8", errors="replace")
        (OUT / log).write_text(result.stdout + result.stderr, encoding="utf-8")
        if result.returncode:
            raise RuntimeError(f"{module} exited {result.returncode}; retained {log}")

    try:
        save(); app = ROOT / ".venv-app/Scripts/python.exe"; core = ROOT / ".venv312/Scripts/python.exe"
        execute(app, "src.application_high_precheck_pid_safe", "six_point_resource.log")
        stage = "six_point_resource_audit"; save(); execute(core, "src.analyze_application_high_precheck", "six_point_audit.log")
        stage = "eight_full_method_resource_runs"; save(); execute(app, "src.run_application_high_method_resource", "method_resource.log")
        stage = "full_method_resource_audit"; save(); execute(core, "src.analyze_application_high_method_resource", "method_resource_audit.log")
        stage = "formal_160_runs"; save(); execute(app, "src.run_application_high_formal", "formal_runs.log")
        stage = "formal_raw_audit"; save(); execute(core, "src.analyze_application_high_formal", "formal_audit.log")
        stage = "complete"; save()
    except Exception as error:
        failure = {"error_type": type(error).__name__, "error": str(error)}; stage = "failed"; save(); raise


if __name__ == "__main__":
    main()
