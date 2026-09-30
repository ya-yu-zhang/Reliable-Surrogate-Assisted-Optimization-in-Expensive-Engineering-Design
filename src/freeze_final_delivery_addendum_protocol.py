"""Freeze the final-delivery addendum protocol before its prerequisites finish."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "docs/frozen_final_delivery_addendum_protocol_v1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert not DEST.exists(), "Final-delivery addendum protocol freeze already exists"
    old_final = json.loads((ROOT / "docs/frozen_final_delivery_v1/sha256.json").read_text("utf-8"))
    third_protocol = json.loads((ROOT / "docs/frozen_third_recovery_v1/sha256.json").read_text("utf-8"))
    assert all(digest(ROOT / name) == expected for name, expected in old_final.items())
    third_root = ROOT / "docs/frozen_third_recovery_v1"
    assert all(digest(third_root / name) == expected for name, expected in third_protocol.items())

    relative = {
        "src/audit_final_delivery_addendum.py",
        "src/finish_final_delivery_addendum.py",
        "src/freeze_final_delivery_addendum_protocol.py",
        "tests/test_final_delivery_addendum.py",
        "src/audit_third_recovery.py",
        "src/freeze_third_recovery_audit.py",
        "src/finish_third_recovery_audit.py",
        "tests/test_third_recovery_audit.py",
        "docs/第三次中断恢复执行协议20260920.md",
        "docs/第三次恢复编排层启动时序记录20260920.md",
        "docs/frozen_final_delivery_v1/sha256.json",
        "docs/frozen_third_recovery_v1/sha256.json",
        "results/interruption_20260920_v3/recovery_manifest.json",
        "results/interruption_20260920_helper_race_v1/manifest.json",
    }
    hashes: dict[str, str] = {}
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
    assert all(digest(DEST / name) == expected for name, expected in check.items())
    print(json.dumps({"files": len(hashes), "manifest_sha256": digest(manifest_path)}, indent=2))


if __name__ == "__main__":
    main()
