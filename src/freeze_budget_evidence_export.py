"""Freeze the budget-evidence builder and all upstream immutable inputs."""
import hashlib
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "docs/frozen_budget_evidence_export_v1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert not DEST.exists(), "Budget-evidence freeze already exists"
    science_manifest = ROOT / "docs/frozen_budget_performance_sensitivity_v1/sha256.json"
    science = json.loads(science_manifest.read_text("utf-8"))
    assert len(science) == 172
    assert all(digest(ROOT / name) == value for name, value in science.items())

    relative = set(science)
    recovery_freeze = ROOT / "docs/frozen_second_recovery_audit_v1"
    recovery = json.loads((recovery_freeze / "sha256.json").read_text("utf-8"))
    assert len(recovery) == 80
    assert all(digest(recovery_freeze / name) == value for name, value in recovery.items())
    relative.add("docs/frozen_second_recovery_audit_v1/sha256.json")
    for name in recovery:
        relative.add("docs/frozen_second_recovery_audit_v1/" + name)
    relative.update(
        {
            "src/build_budget_sensitivity_revision.py",
            "src/finish_budget_evidence_export.py",
            "src/freeze_budget_evidence_export.py",
            "tests/test_budget_evidence_guards.py",
            "docs/预算性能证据整合与视觉门槛.md",
        }
    )

    hashes = {}
    for name in sorted(relative):
        source = ROOT / name
        assert source.is_file(), name
        target = DEST / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        hashes[name] = digest(source)
        assert digest(target) == hashes[name]
    manifest_path = DEST / "sha256.json"
    manifest_path.write_text(json.dumps(hashes, ensure_ascii=False, indent=2), encoding="utf-8")
    check = json.loads(manifest_path.read_text("utf-8"))
    assert len(check) == len(hashes)
    assert all(digest(DEST / name) == value for name, value in check.items())
    print(json.dumps({"files": len(hashes), "manifest_sha256": digest(manifest_path)}, indent=2))


if __name__ == "__main__":
    main()
