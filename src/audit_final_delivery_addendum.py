"""Objective-free addendum audit for evidence created after final-audit v1 was frozen."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/final_delivery_addendum_audit_v1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text("utf-8"))


def verify_hash_map(base: Path, manifest: dict[str, str]) -> None:
    for name, expected in manifest.items():
        path = base / name
        assert path.is_file(), name
        assert digest(path) == expected, name


def require_original_delivery(root: Path) -> dict[str, Any]:
    status = load(root / "results/final_delivery_completion_v1/status.json")
    assert status["stage"] == "complete" and status["failure"] is None
    audit = load(root / "results/final_delivery_audit_v1/audit.json")
    assert audit["complete"] and audit["objective_calls_by_this_auditor"] == 0
    manifest_path = root / "paper/final_delivery_manifest.json"
    assert digest(manifest_path) == audit["final_delivery_manifest_sha256"]
    manifest = load(manifest_path)
    assert len(manifest) == audit["final_delivery_files"]
    verify_hash_map(root, manifest)
    return audit


def require_third_recovery(root: Path) -> tuple[dict[str, Any], dict[str, str]]:
    status = load(root / "results/third_recovery_audit_completion_v1/status.json")
    assert status["stage"] == "complete" and status["failure"] is None
    audit = load(root / "results/interruption_20260920_v3/third_recovery_audit.json")
    assert audit["schema"] == "third_recovery_audit_v1"
    assert audit["objective_calls_by_this_auditor"] == 0
    assert audit["recovered_runs"] == 8
    assert audit["canonical_algorithm_evaluations"] == 3200
    assert audit["third_generation_saved_labels"] == 2514
    assert audit["third_generation_new_physical_calls"] == 686
    assert audit["redundant_recovery_validation_calls"] == 0
    assert audit["all_archived_prefixes_exactly_equal"]
    assert audit["all_physical_suffixes_exactly_equal"]
    assert audit["all_canonical_trajectories_complete"]

    frozen_root = root / "docs/frozen_third_recovery_audit_v1"
    frozen = load(frozen_root / "sha256.json")
    verify_hash_map(frozen_root, frozen)
    return audit, frozen


def require_helper_race_archive(root: Path) -> dict[str, Any]:
    archive = root / "results/interruption_20260920_helper_race_v1"
    manifest = load(archive / "manifest.json")
    assert manifest["schema"] == "helper_relaunch_race_archive_v1"
    assert len(manifest["moved_state_dirs"]) == 12
    assert len(manifest["moved_logs"]) == 24
    assert len(manifest["files"]) == 36
    assert "no scientific objective evaluation" in manifest["reason"]
    for row in manifest["files"]:
        path = archive / row["path"]
        assert path.is_file(), row["path"]
        assert path.stat().st_size == row["bytes"]
        assert digest(path) == row["sha256"]
    return manifest


def main() -> None:
    assert not OUT.exists(), "Final-delivery addendum audit exists; refuse duplicate restart"
    protocol_root = ROOT / "docs/frozen_final_delivery_addendum_protocol_v1"
    protocol = load(protocol_root / "sha256.json")
    verify_hash_map(protocol_root, protocol)
    original = require_original_delivery(ROOT)
    third, frozen = require_third_recovery(ROOT)
    race = require_helper_race_archive(ROOT)
    OUT.mkdir(parents=True)

    completion_doc = ROOT / "docs/最终论文与实验完成补充核查20260920.md"
    completion_doc.write_text(
        "# 最终论文与实验完成补充核查（2026-09-20）\n\n"
        "原冻结最终交付审计保持不变并再次通过其交付清单逐文件哈希核对。第三次中断恢复另以独立只读审计补入证据链：8条轨迹的2,514个已付费标签与冻结前缀逐条一致，686个新物理后缀调用与最终日志逐条一致，最终规范轨迹共3,200步，跨前两代恢复没有同名任务，因此本次冗余恢复调用为0。\n\n"
        "下游等待器首次同时启动产生的编排时序失败已完整归档；它没有运行科学目标函数。顺序重启后的科学与表示链仍由原门槛控制。原论文对第二次恢复中1次已公开冗余物理调用的披露保持不变；第三次恢复没有改变任何规范算法评价数、统计输入、图表或论文结论。\n",
        encoding="utf-8",
    )

    evidence = {
        "paper/final_delivery_manifest.json": digest(ROOT / "paper/final_delivery_manifest.json"),
        "results/final_delivery_audit_v1/audit.json": digest(ROOT / "results/final_delivery_audit_v1/audit.json"),
        "results/interruption_20260920_v3/third_recovery_audit.json": digest(
            ROOT / "results/interruption_20260920_v3/third_recovery_audit.json"
        ),
        "docs/frozen_third_recovery_audit_v1/sha256.json": digest(
            ROOT / "docs/frozen_third_recovery_audit_v1/sha256.json"
        ),
        "results/interruption_20260920_helper_race_v1/manifest.json": digest(
            ROOT / "results/interruption_20260920_helper_race_v1/manifest.json"
        ),
        "docs/frozen_final_delivery_addendum_protocol_v1/sha256.json": digest(
            ROOT / "docs/frozen_final_delivery_addendum_protocol_v1/sha256.json"
        ),
        "docs/最终论文与实验完成补充核查20260920.md": digest(completion_doc),
    }
    manifest_path = ROOT / "paper/final_delivery_addendum_manifest.json"
    manifest_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    verify_hash_map(ROOT, evidence)

    result = {
        "schema": "final_delivery_addendum_audit_v1",
        "complete": True,
        "objective_calls_by_this_auditor": 0,
        "original_final_delivery_verified": original["complete"],
        "third_recovery_verified": True,
        "third_recovery_redundant_calls": third["redundant_recovery_validation_calls"],
        "third_recovery_frozen_files": len(frozen),
        "addendum_protocol_frozen_files": len(protocol),
        "helper_race_archive_files": len(race["files"]),
        "scientific_results_changed_by_addendum": False,
        "addendum_manifest_sha256": digest(manifest_path),
        "addendum_files": len(evidence),
    }
    (OUT / "audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
