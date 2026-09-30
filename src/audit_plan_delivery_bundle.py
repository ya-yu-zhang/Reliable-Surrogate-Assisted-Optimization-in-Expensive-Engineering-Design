"""Audit the final delivery against the original writing and experiment plan."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from .audit_manuscript_citations import audit_text
from .run_solo_cost import process_inventory


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/plan_delivery_bundle_audit_v1"

ENGLISH_HEADINGS = [
    "# 1 Introduction",
    "# 2 Related work and scope of comparison",
    "# 3 Problem, information, and decision events",
    "# 4 Search framework and empirical monitoring",
    "# 5 Structural audit and limitations of event reasoning",
    "# 6 Development protocol and statistical units",
    "# 7 Audited development results",
    "# 8 Independent mechanism validation",
    "# 9 Complete references, exclusive cost, and application transfer",
    "# 10 Discussion",
    "# 11 Predefined 300-D Extension",
    "# 12 Prespecified Model and Training-Cap Sensitivity",
    "# 13 Prespecified Budget-Performance Sensitivity",
    "# 14 Conclusion",
]
CHINESE_HEADINGS = [
    "# 1 引言",
    "# 2 相关工作与研究边界",
    "# 3 问题与信息可见性",
    "# 4 搜索原型与误差监测",
    "# 5 上界声明与选点作用的分析",
    "# 6 实验协议",
    "# 7 开发阶段结果",
    "# 8 独立机制验证",
    "# 9 完整参照、独占成本与应用迁移",
    "# 10 讨论",
    "# 11 预定300维扩展",
    "# 12 预定模型与训练截断敏感性",
    "# 13 预定预算性能敏感性",
    "# 14 结论",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text("utf-8"))


def validate_headings(text: str, headings: list[str]) -> None:
    positions = []
    for heading in headings:
        assert text.count(heading) == 1, heading
        positions.append(text.index(heading))
    assert positions == sorted(positions)


def verify_file_manifest(root: Path, manifest: dict[str, str]) -> None:
    assert manifest
    for name, expected in manifest.items():
        path = root / name
        assert path.is_file(), name
        assert digest(path) == expected, name


def require_final_delivery() -> tuple[dict, dict]:
    status = load(ROOT / "results/final_delivery_citation_v2_completion/status.json")
    alive = {row["ProcessId"] for row in process_inventory()}
    assert status["stage"] == "complete" and status["failure"] is None
    assert status["pid"] not in alive
    audit = load(ROOT / "results/final_delivery_citation_v2_audit/audit.json")
    assert audit["complete"] and audit["objective_calls_by_this_auditor"] == 0
    assert audit["all_required_statuses_terminal"] and audit["all_scientific_audits_verified"]
    assert audit["eight_citation_corrected_pdfs_visually_verified"]
    assert audit["undefined_citations"] == audit["uncited_references"] == 0
    manifest = load(ROOT / "paper/final_delivery_citation_v2_manifest.json")
    verify_file_manifest(ROOT, manifest)
    assert digest(ROOT / "paper/final_delivery_citation_v2_manifest.json") == audit["final_manifest_sha256"]
    return audit, manifest


def require_manuscripts() -> tuple[Path, Path, dict]:
    english = ROOT / "paper/english_budget_complete_manuscript_citation_revision.md"
    chinese = ROOT / "paper/论文预算完整机制稿.md"
    en = english.read_text("utf-8")
    zh = chinese.read_text("utf-8")
    validate_headings(en, ENGLISH_HEADINGS)
    validate_headings(zh, CHINESE_HEADINGS)
    citation = audit_text(en, "# References")
    assert citation["undefined_citations"] == citation["uncited_references"] == []
    assert "Using the COCO BBOB specification and IOHexperimenter implementation [8,9]" in en
    assert "151,201" in en and "151,201" in zh
    assert "submission-ready superiority claim" in en
    assert "投稿就绪或普遍优越性声明" in zh
    assert len(re.findall(r"^!\[", en, flags=re.MULTILINE)) >= 14
    assert len(re.findall(r"^!\[", zh, flags=re.MULTILINE)) >= 13
    for image in [
        "analysis_v1/selection_failure.png",
        "mechanism_validation_report_v1/convergence_curves.png",
        "mechanism_validation_report_v1/effective_support.png",
        "all_reference_report_v1/reference_endpoints.png",
        "integrated_paper_report_v1/objective_cost_scenarios.png",
        "application_report_v1/application_endpoints.png",
        "application_high_report_v1/high_endpoint.png",
        "model_sensitivity_report_v1/sensitivity_endpoint.png",
        "budget_performance_sensitivity_report_v1/budget_endpoints.png",
    ]:
        assert image in en and image in zh, image
    return english, chinese, citation


def require_scope_and_supplements() -> list[dict]:
    gate = load(ROOT / "results/analysis_v1/gate.json")
    assert not gate["pass_directional_gate"] and not gate["full_gate_passed"]
    assert gate["confirmation_unopened"]
    scope = (ROOT / "docs/论文与实验范围总账20260919.md").read_text("utf-8")
    for phrase in [
        "原BBOB主确认实例6–10",
        "依第十四节停止标准未启动",
        "CEC2017确认及固定500混淆检查",
        "Temporal CP-SAEA/SADE-SS/BGP-SAEA",
        "未取得可靠实现",
    ]:
        assert phrase in scope
    supplement = (ROOT / "paper/补充材料_开发阶段.md").read_text("utf-8")
    for image in ["information_flow.png", "declarations.png", "canonical_case.png"]:
        assert image in supplement
    required_pdfs = [
        ROOT / "paper/pdf/补充材料_开发阶段.pdf",
        ROOT / "paper/pdf/english_mechanism_supplement.pdf",
        ROOT / "paper/pdf/独立机制验证报告.pdf",
    ]
    assert all(path.is_file() and path.stat().st_size > 10_000 for path in required_pdfs)
    return [
        {
            "requirement": "development_and_mechanism_experiments",
            "disposition": "complete",
            "evidence": "results/analysis_v1/audit.json; results/mechanism_validation_analysis_v1/full_integrity_audit.json",
        },
        {
            "requirement": "original_bbob_instances_6_10_and_cec_confirmation",
            "disposition": "stopped_by_prespecified_scientific_gate",
            "evidence": "results/analysis_v1/gate.json; docs/论文与实验范围总账20260919.md",
        },
        {
            "requirement": "reliable_named_saea_reproductions",
            "disposition": "availability_gap_disclosed",
            "evidence": "docs/关键SAEA可获得性复核20260919.md",
        },
        {
            "requirement": "external_references_and_exclusive_cost",
            "disposition": "complete",
            "evidence": "results/basic_references_analysis_v1; results/turbo_reference_analysis_v1; results/gp_ei_reference_analysis_v1; results/solo_cost_analysis_v1",
        },
        {
            "requirement": "application_high_dimension_model_and_budget_scope",
            "disposition": "complete",
            "evidence": "results/application_analysis_v1; results/application_high_analysis_v1; results/model_sensitivity_analysis_v1; results/budget_performance_sensitivity_analysis_v1",
        },
        {
            "requirement": "bilingual_papers_figures_supplements_and_visual_review",
            "disposition": "complete",
            "evidence": "paper/final_delivery_citation_v2_manifest.json; results/all_pdf_visual_review_citation_v2/reviewed_pdf_manifest.json",
        },
        {
            "requirement": "configs_versions_seeds_raw_logs_statistics_and_failure_records",
            "disposition": "complete_and_hash_addressed",
            "evidence": "configs; docs/*environment-lock*; frozen manifests; raw source hash lists; interruption archives",
        },
    ]


def delivery_files(final_manifest: dict[str, str]) -> list[Path]:
    files = {ROOT / name for name in final_manifest}
    files.update([
        ROOT / "docs/原始计划书.md",
        ROOT / "docs/论文与实验范围总账20260919.md",
        ROOT / "docs/后续研究执行清单.md",
        ROOT / "docs/关键SAEA可获得性复核20260919.md",
        ROOT / "results/analysis_v1/gate.json",
        ROOT / "results/analysis_v1/audit.json",
        ROOT / "paper/补充材料_开发阶段.md",
        ROOT / "paper/pdf/补充材料_开发阶段.pdf",
        ROOT / "paper/english_mechanism_supplement.md",
        ROOT / "paper/pdf/english_mechanism_supplement.pdf",
        ROOT / "paper/独立机制验证报告.md",
        ROOT / "paper/pdf/独立机制验证报告.pdf",
        ROOT / "results/all_pdf_visual_review_citation_v2/reviewed_pdf_manifest.json",
        ROOT / "results/final_delivery_citation_v2_audit/audit.json",
    ])
    files.update(path for path in (ROOT / "configs").glob("*") if path.is_file())
    files.update(path for path in (ROOT / "docs").glob("*environment-lock*") if path.is_file())
    assert all(path.is_file() for path in files)
    return sorted(files)


def main() -> None:
    assert not OUT.exists(), "Plan delivery bundle audit already exists"
    protocol_root = ROOT / "docs/frozen_plan_delivery_bundle_protocol_v1"
    protocol = load(protocol_root / "sha256.json")
    verify_file_manifest(protocol_root, protocol)
    final_audit, final_manifest = require_final_delivery()
    english, chinese, citation = require_manuscripts()
    requirements = require_scope_and_supplements()
    files = delivery_files(final_manifest)

    bundle = {
        path.relative_to(ROOT).as_posix(): digest(path)
        for path in files
    }
    manifest_path = ROOT / "paper/plan_delivery_bundle_manifest.json"
    manifest_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    verify_file_manifest(ROOT, bundle)

    completion_doc = ROOT / "docs/计划书逐项完成核查.md"
    rows = "\n".join(
        f"| {row['requirement']} | {row['disposition']} | `{row['evidence']}` |"
        for row in requirements
    )
    completion_doc.write_text(
        "# 论文计划书逐项完成核查\n\n"
        "本核查以原始计划第十四节的继续/停止标准为边界。开发优化收益门槛失败后，原BBOB实例6–10与CEC确认未被伪装为已完成；当前交付完成的是经预定停止规则转向后的机制与失败研究、完整外部背景、应用和预定稳健性扩展。\n\n"
        "| 计划要求 | 处置 | 权威证据 |\n|---|---|---|\n" + rows + "\n\n"
        "最终中英文正文、补充材料、配置、环境锁、原始日志哈希、统计审计、恢复与失败记录均进入交付清单。八份权威证据PDF已经逐页检查；英文最终稿未定义引用和未引用条目均为0。该完成状态不构成普遍优化优越性或期刊录用声明。\n",
        encoding="utf-8",
    )

    OUT.mkdir(parents=True)
    result = {
        "schema": "plan_delivery_bundle_audit_v1",
        "complete": True,
        "objective_calls_by_this_auditor": 0,
        "original_plan_preserved": True,
        "prespecified_stop_rule_applied": True,
        "unexecuted_confirmation_claimed_complete": False,
        "requirement_rows": len(requirements),
        "complete_rows": sum(row["disposition"].startswith("complete") for row in requirements),
        "stopped_rows": sum(row["disposition"].startswith("stopped") for row in requirements),
        "availability_gap_rows": sum("gap" in row["disposition"] for row in requirements),
        "english_sections_verified": len(ENGLISH_HEADINGS),
        "chinese_sections_verified": len(CHINESE_HEADINGS),
        "undefined_citations": len(citation["undefined_citations"]),
        "uncited_references": len(citation["uncited_references"]),
        "eight_pdfs_visually_verified": final_audit["eight_citation_corrected_pdfs_visually_verified"],
        "bundle_files": len(bundle),
        "bundle_manifest_sha256": digest(manifest_path),
        "completion_document_sha256": digest(completion_doc),
        "frozen_protocol_files": len(protocol),
        "submission_ready_claimed": False,
        "requirements": requirements,
        "final_english": english.relative_to(ROOT).as_posix(),
        "final_chinese": chinese.relative_to(ROOT).as_posix(),
    }
    (OUT / "audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
