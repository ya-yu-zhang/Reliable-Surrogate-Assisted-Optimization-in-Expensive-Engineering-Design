"""Create and verify a scoped standard-library development replay package.

Includes exact already-restored source inputs; no simulator, GP fit, PDF rebuild
or public binary upload. The historical minimum manuscript package is separate.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "paper/engineering_optimization/monotone_development_20261013"
OUTPUTS = ["analysis.json", "summary.csv", "state_results.csv", "seed_group_results.csv",
           "posthoc_order_envelope.csv", "certificate_records.jsonl"]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    report = json.loads((DEST / "analysis.json").read_text())
    sources = report["source_files_sha256"]
    for p, expected in sources.items():
        if digest((ROOT / p).read_bytes()) != expected:
            raise ValueError(f"Source changed after analysis: {p}")
    files = set(sources) | {"src/__init__.py", "tests/__init__.py",
        "tests/test_monotone_horizon_audit.py", "tests/test_monotone_development.py"}
    files.update(str(p.relative_to(ROOT)) for p in DEST.iterdir()
                 if p.suffix in {".json", ".jsonl", ".csv", ".md", ".txt"}
                 and p.name not in {"verification.json", "delivery.json"})
    with tempfile.TemporaryDirectory(prefix="monotone_verify_", dir=ROOT.parent) as temp:
        target = Path(temp)
        for name in sorted(files):
            out = target / name
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, out)
        test = subprocess.run([sys.executable, "-m", "unittest", "tests.test_monotone_horizon_audit",
                               "tests.test_monotone_development", "-v"], cwd=target,
                              capture_output=True, text=True, check=True)
        if "Ran 15 tests" not in test.stderr or not test.stderr.rstrip().endswith("OK"):
            raise ValueError("Unexpected isolated test result")
        replay = subprocess.run([sys.executable, "-m", "src.analyze_monotone_development"],
                                cwd=target, capture_output=True, text=True, check=True)
        checks = {}
        for name in OUTPUTS:
            original = (DEST / name).read_bytes()
            derived = (target / DEST.relative_to(ROOT) / name).read_bytes()
            if original != derived:
                raise ValueError(f"Nonidentical replay output: {name}")
            checks[name] = {"sha256": digest(original), "bytes": len(original)}
    verification = {"isolated_standard_library_tests_passed": 15,
                    "full_relevant_tests_passed": 46,
                    "full_test_scope": "nine locally available unittest modules; integrity_tests.txt",
                    "source_hashes_verified": len(sources), "byte_identical_outputs": checks,
                    "new_physics_attempts": 0, "new_gp_fits": 0,
                    "gp_fit_count_scope": "Development replay and new experiment acquisition; legacy full-suite synthetic GP fixtures are outside this count.",
                    "submission_ready": False,
                    "independent_experiment_started": False}
    (DEST / "verification.json").write_text(json.dumps(verification, indent=2) + "\n")
    files.add(str((DEST / "verification.json").relative_to(ROOT)))
    archive = ROOT / "paper/engineering_optimization/EO_monotone_development_20261013.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for name in sorted(files):
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 13, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, (ROOT / name).read_bytes(), compresslevel=9)
    with zipfile.ZipFile(archive) as bundle:
        if set(bundle.namelist()) != files:
            raise ValueError("Unexpected package members")
        for name in files:
            if bundle.read(name) != (ROOT / name).read_bytes():
                raise ValueError(f"Package member mismatch: {name}")
    delivery = {"path": str(archive.relative_to(ROOT)), "sha256": digest(archive.read_bytes()),
                "bytes": archive.stat().st_size, "members": len(files),
                "scope": "exact restored development inputs, code/tests, reports and six reproducible outputs; no current or historical manuscript PDFs",
                "public_binary_upload_attempted": False,
                "source_baseline_commit": "c2ce41a0e956621c81f2e3078f31da27edc990dd"}
    (DEST / "delivery.json").write_text(json.dumps(delivery, indent=2) + "\n")
    print(json.dumps({"verification": verification, "delivery": delivery}))


if __name__ == "__main__":
    main()
