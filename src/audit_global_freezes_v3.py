"""Read-only integrity audit of every top-level freeze manifest as of 2026-09-20."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/freeze_integrity_20260920_v3"
SELF_FREEZE = "frozen_global_freeze_audit_20260920_v3"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def audit_manifest(root: Path, freeze_dir: Path) -> tuple[dict[str, Any], list[dict], list[dict], set[Path]]:
    manifest_path = freeze_dir / "sha256.json"
    payload = json.loads(manifest_path.read_text("utf-8"))
    live_mismatches: list[dict] = []
    copy_mismatches: list[dict] = []
    missing_copies: list[dict] = []
    hashed: set[Path] = {manifest_path.resolve()}

    if isinstance(payload, list):
        schema = "flat-list"
        entries = []
        for item in payload:
            live = Path(item["Path"])
            if not live.is_absolute():
                live = root / live
            expected = item.get("Hash", item.get("SHA256"))
            assert isinstance(expected, str), item
            expected = expected.lower()
            assert inside(live, root), live
            copy = freeze_dir / live.name
            entries.append((live, copy, expected, live.relative_to(root).as_posix()))
    elif isinstance(payload, dict):
        schema = "nested-dict"
        entries = []
        for name, expected in payload.items():
            live = root / name
            assert inside(live, root), name
            copy = freeze_dir / name
            entries.append((live, copy, expected.lower(), name))
    else:
        raise AssertionError(f"Unsupported manifest schema: {manifest_path}")

    for live, copy, expected, name in entries:
        if not live.is_file():
            live_mismatches.append({"freeze": freeze_dir.name, "scope": "live", "path": name, "reason": "missing"})
        else:
            hashed.add(live.resolve())
            actual = digest(live)
            if actual != expected:
                live_mismatches.append(
                    {"freeze": freeze_dir.name, "scope": "live", "path": name, "expected": expected, "actual": actual}
                )
        if not copy.is_file():
            missing_copies.append(
                {
                    "freeze": freeze_dir.name,
                    "scope": "copy",
                    "path": name,
                    "expected_copy": copy.relative_to(root).as_posix(),
                }
            )
        else:
            hashed.add(copy.resolve())
            actual = digest(copy)
            if actual != expected:
                copy_mismatches.append(
                    {
                        "freeze": freeze_dir.name,
                        "scope": "copy",
                        "path": name,
                        "copy": copy.relative_to(root).as_posix(),
                        "expected": expected,
                        "actual": actual,
                    }
                )

    row = {
        "freeze": freeze_dir.name,
        "schema": schema,
        "files": len(entries),
        "manifest_sha256": digest(manifest_path),
        "live_mismatches": len(live_mismatches),
        "copy_mismatches": len(copy_mismatches),
        "missing": len(missing_copies),
    }
    return row, live_mismatches, copy_mismatches + missing_copies, hashed


def audit(root: Path = ROOT, *, write: bool = True) -> dict[str, Any]:
    manifests = sorted(
        directory
        for directory in (root / "docs").glob("frozen_*")
        if directory.name != SELF_FREEZE and (directory / "sha256.json").is_file()
    )
    rows = []
    live_mismatches = []
    copy_issues = []
    hashed: set[Path] = set()
    for directory in manifests:
        row, live, copies, files = audit_manifest(root, directory)
        rows.append(row)
        live_mismatches.extend(live)
        copy_issues.extend(copies)
        hashed.update(files)

    known_missing = [
        issue
        for issue in copy_issues
        if issue.get("freeze") == "frozen_v1"
        and issue.get("path") in {"configs/development.json", "configs/mechanism.json"}
        and "expected_copy" in issue
    ]
    unexpected_copy_issues = [issue for issue in copy_issues if issue not in known_missing]
    assert not live_mismatches
    assert not unexpected_copy_issues
    assert len(known_missing) == 2

    result = {
        "timestamp_shanghai": datetime.now(timezone(timedelta(hours=8))).isoformat(),
        "objective_calls": 0,
        "manifests": len(manifests),
        "manifest_entries": sum(row["files"] for row in rows),
        "unique_files_hashed": len(hashed),
        "all_live_originals_match": not live_mismatches,
        "all_present_frozen_copies_match": not any("actual" in issue for issue in copy_issues),
        "known_missing_old_flat_copies": known_missing,
        "rows": rows,
        "live_mismatches": live_mismatches,
        "unexpected_copy_issues": unexpected_copy_issues,
    }
    if write:
        OUT.mkdir(parents=True, exist_ok=False)
        (OUT / "audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main() -> None:
    result = audit()
    print(json.dumps({key: value for key, value in result.items() if key != "rows"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
