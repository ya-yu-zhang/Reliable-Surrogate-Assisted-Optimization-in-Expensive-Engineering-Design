"""Final objective-free provenance audit after the original-plan delivery closes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .audit_global_freezes_v3 import audit_manifest
from .run_solo_cost import process_inventory


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/final_provenance_bundle_audit_v1"
SELF_FREEZE = "frozen_final_provenance_bundle_v1"
AUTHORIZED_LIVE_DRIFT = {
    ("frozen_plan_delivery_bundle_protocol_v1", "docs/论文与实验范围总账20260919.md"),
}
KNOWN_MISSING_COPIES = {
    ("frozen_v1", "configs/development.json"),
    ("frozen_v1", "configs/mechanism.json"),
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text("utf-8"))


def classify_issues(live_issues: list[dict], copy_issues: list[dict]) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    allowed_live = [
        row for row in live_issues
        if (row.get("freeze"), row.get("path")) in AUTHORIZED_LIVE_DRIFT
    ]
    unexpected_live = [row for row in live_issues if row not in allowed_live]
    known_missing = [
        row for row in copy_issues
        if (row.get("freeze"), row.get("path")) in KNOWN_MISSING_COPIES
        and "expected_copy" in row
    ]
    unexpected_copy = [row for row in copy_issues if row not in known_missing]
    return allowed_live, unexpected_live, known_missing, unexpected_copy


def collect_provenance_files(root: Path, freeze_manifests: list[Path]) -> list[Path]:
    files: set[Path] = set(freeze_manifests)
    for directory, pattern in [
        (root / "src", "*.py"),
        (root / "tests", "*.py"),
        (root / "configs", "*"),
    ]:
        files.update(path for path in directory.rglob(pattern) if path.is_file())
    files.update(path for path in (root / "docs").glob("*environment-lock*") if path.is_file())
    for directory in [root / "results", root / "paper"]:
        for path in directory.rglob("*.json"):
            lowered = path.name.lower()
            if any(token in lowered for token in ["source_hash", "journal_hash", "manifest"]):
                files.add(path)
    files.update([
        root / "docs/原始计划书.md",
        root / "docs/论文与实验范围总账20260919.md",
        root / "docs/计划书逐项完成核查.md",
        root / "paper/final_delivery_citation_v2_manifest.json",
        root / "paper/plan_delivery_bundle_manifest.json",
        root / "results/final_delivery_citation_v2_audit/audit.json",
        root / "results/plan_delivery_bundle_audit_v1/audit.json",
    ])
    assert all(path.is_file() for path in files)
    return sorted(files)


def require_upstream() -> dict:
    status = load(ROOT / "results/plan_delivery_bundle_completion_v1/status.json")
    alive = {row["ProcessId"] for row in process_inventory()}
    assert status["stage"] == "complete" and status["failure"] is None
    assert status["pid"] not in alive
    audit = load(ROOT / "results/plan_delivery_bundle_audit_v1/audit.json")
    assert audit["complete"] and audit["objective_calls_by_this_auditor"] == 0
    assert audit["prespecified_stop_rule_applied"]
    assert not audit["unexecuted_confirmation_claimed_complete"]
    assert audit["eight_pdfs_visually_verified"]
    bundle = load(ROOT / "paper/plan_delivery_bundle_manifest.json")
    assert digest(ROOT / "paper/plan_delivery_bundle_manifest.json") == audit["bundle_manifest_sha256"]
    for name, expected in bundle.items():
        assert digest(ROOT / name) == expected, name
    return audit


def main() -> None:
    assert not OUT.exists(), "Final provenance bundle audit already exists"
    protocol_root = ROOT / "docs/frozen_final_provenance_bundle_protocol_v1"
    protocol = load(protocol_root / "sha256.json")
    assert all(digest(protocol_root / name) == expected for name, expected in protocol.items())
    upstream = require_upstream()

    freeze_dirs = sorted(
        directory for directory in (ROOT / "docs").glob("frozen_*")
        if directory.name != SELF_FREEZE and (directory / "sha256.json").is_file()
    )
    rows = []
    live_issues: list[dict] = []
    copy_issues: list[dict] = []
    for directory in freeze_dirs:
        row, live, copies, _ = audit_manifest(ROOT, directory)
        rows.append(row)
        live_issues.extend(live)
        copy_issues.extend(copies)
    allowed_live, unexpected_live, known_missing, unexpected_copy = classify_issues(live_issues, copy_issues)
    assert not unexpected_live and not unexpected_copy
    assert len(allowed_live) == 1 and len(known_missing) == 2
    names = {directory.name for directory in freeze_dirs}
    for required in [
        "frozen_gp_ei_terminal_checkpoint_v1",
        "frozen_third_recovery_audit_v1",
        "frozen_plan_delivery_bundle_v1",
        "frozen_final_delivery_citation_v2_protocol",
    ]:
        assert required in names

    freeze_manifests = [directory / "sha256.json" for directory in freeze_dirs]
    files = collect_provenance_files(ROOT, freeze_manifests)
    provenance = {path.relative_to(ROOT).as_posix(): digest(path) for path in files}
    manifest_path = ROOT / "paper/final_provenance_manifest.json"
    manifest_path.write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8")
    assert all(digest(ROOT / name) == expected for name, expected in provenance.items())

    completion_doc = ROOT / "docs/最终来源与冻结完整性核查.md"
    completion_doc.write_text(
        "# 最终来源与冻结完整性核查\n\n"
        f"最终审计读取{len(freeze_dirs)}份顶层冻结清单、{sum(row['files'] for row in rows):,}个冻结条目；所有现存冻结副本哈希一致。最早`frozen_v1`仍保留两份已知未复制配置的历史事实。\n\n"
        "唯一允许的工作区原件差异来自计划书闭环协议冻结后对动态范围总账追加该闭环步骤；协议内冻结副本未改变，后续最终计划书冻结保存了更新后的总账。除此之外没有未解释的原件或副本偏差。\n\n"
        f"最终来源清单包含{len(provenance)}个文件，覆盖当前源码、测试、配置、环境锁、全部冻结清单、科学原始日志哈希清单、恢复清单以及最终论文交付清单。大体积原始日志和PDF保留在原目录，通过已审计哈希索引寻址，不重复复制。该核查调用目标函数0次。\n",
        encoding="utf-8",
    )

    OUT.mkdir(parents=True)
    result = {
        "schema": "final_provenance_bundle_audit_v1",
        "complete": True,
        "objective_calls_by_this_auditor": 0,
        "upstream_plan_delivery_complete": upstream["complete"],
        "freeze_manifests": len(freeze_dirs),
        "freeze_manifest_entries": sum(row["files"] for row in rows),
        "all_present_frozen_copies_match": not any("actual" in row for row in copy_issues),
        "authorized_dynamic_live_drift": allowed_live,
        "unexpected_live_mismatches": unexpected_live,
        "known_missing_old_flat_copies": known_missing,
        "unexpected_copy_issues": unexpected_copy,
        "provenance_files": len(provenance),
        "source_files": sum(name.startswith("src/") for name in provenance),
        "test_files": sum(name.startswith("tests/") for name in provenance),
        "config_files": sum(name.startswith("configs/") for name in provenance),
        "hash_or_manifest_files": sum("hash" in Path(name).name.lower() or "manifest" in Path(name).name.lower() for name in provenance),
        "provenance_manifest_sha256": digest(manifest_path),
        "completion_document_sha256": digest(completion_doc),
        "frozen_protocol_files": len(protocol),
        "submission_ready_claimed": False,
        "rows": rows,
    }
    (OUT / "audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "rows"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
