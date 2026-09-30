"""Freeze the final original-plan delivery audit without duplicating raw logs or PDFs."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "docs/frozen_plan_delivery_bundle_v1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert not DEST.exists(), "Plan delivery bundle already frozen"
    audit_path = ROOT / "results/plan_delivery_bundle_audit_v1/audit.json"
    audit = json.loads(audit_path.read_text("utf-8"))
    assert audit["complete"] and audit["objective_calls_by_this_auditor"] == 0
    assert audit["prespecified_stop_rule_applied"]
    assert not audit["unexecuted_confirmation_claimed_complete"]
    assert audit["english_sections_verified"] == audit["chinese_sections_verified"] == 14
    assert audit["undefined_citations"] == audit["uncited_references"] == 0
    assert audit["eight_pdfs_visually_verified"]

    relative = [
        "src/audit_plan_delivery_bundle.py",
        "src/finish_plan_delivery_bundle.py",
        "src/freeze_plan_delivery_bundle.py",
        "results/plan_delivery_bundle_audit_v1/audit.json",
        "paper/plan_delivery_bundle_manifest.json",
        "docs/计划书逐项完成核查.md",
        "docs/计划书最终交付闭环协议20260920.md",
        "docs/frozen_plan_delivery_bundle_protocol_v1/sha256.json",
        "results/final_delivery_citation_v2_audit/audit.json",
        "paper/final_delivery_citation_v2_manifest.json",
        "docs/原始计划书.md",
        "docs/论文与实验范围总账20260919.md",
    ]
    hashes = {}
    for name in relative:
        source = ROOT / name
        assert source.is_file(), name
        target = DEST / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        hashes[name] = digest(source)
        assert digest(target) == hashes[name]
    manifest = DEST / "sha256.json"
    manifest.write_text(json.dumps(hashes, ensure_ascii=False, indent=2), encoding="utf-8")
    assert all(digest(DEST / name) == expected for name, expected in json.loads(manifest.read_text("utf-8")).items())
    print(json.dumps({"files": len(hashes), "manifest_sha256": digest(manifest)}, indent=2))


if __name__ == "__main__":
    main()
