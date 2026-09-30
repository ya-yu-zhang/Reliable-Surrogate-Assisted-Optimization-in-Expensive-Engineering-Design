"""Freeze the complete evidence chain for the second-recovery correction."""
import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "docs/frozen_second_recovery_audit_v1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert not DEST.exists(), "Second-recovery audit freeze already exists"
    first_path = ROOT / "results/interruption_20260918_v1/recovery_manifest.json"
    second_path = ROOT / "results/interruption_20260919_v2/recovery_manifest.json"
    first = json.loads(first_path.read_text("utf-8"))
    second = json.loads(second_path.read_text("utf-8"))
    audit_path = ROOT / "results/interruption_20260919_v2/second_recovery_audit.json"
    audit = json.loads(audit_path.read_text("utf-8"))
    assert audit["recovered_runs"] == 8
    assert audit["redundant_recovery_validation_calls"] == 1
    assert audit["objective_calls_by_this_auditor"] == 0

    relative = {
        "src/freeze_second_recovery_audit.py",
        "src/audit_second_recovery.py",
        "docs/第二次恢复冗余调用更正.md",
        first_path.relative_to(ROOT).as_posix(),
        second_path.relative_to(ROOT).as_posix(),
        audit_path.relative_to(ROOT).as_posix(),
    }
    for manifest in (first, second):
        relative.update(manifest.get("recovery_sources", {}).keys())
        for row in manifest["partial_runs"]:
            for name in row["file_sha256"]:
                relative.add(f"{row['archive']}/{name}")

    for row in audit["runs"]:
        base = f"results/{row['source']}/{row['runid']}"
        relative.update(
            {
                f"{base}/events.jsonl",
                f"{base}/summary.json",
                f"{base}/recovery_physical_calls.jsonl",
                f"{base}/recovery.json",
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
    reloaded = json.loads(manifest_path.read_text("utf-8"))
    assert len(reloaded) == len(hashes)
    assert all(digest(DEST / name) == value for name, value in reloaded.items())
    print(json.dumps({"files": len(hashes), "manifest_sha256": digest(manifest_path)}, indent=2))


if __name__ == "__main__":
    main()
