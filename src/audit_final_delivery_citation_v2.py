"""Final objective-free audit for the citation-corrected bilingual delivery."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .audit_final_delivery import require_science, require_statuses
from .audit_final_delivery_addendum import require_helper_race_archive, require_third_recovery, verify_hash_map
from .audit_manuscript_citations import audit_text
from .run_solo_cost import process_inventory


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/final_delivery_citation_v2_audit"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text("utf-8"))


def require_citation_visual_complete(root: Path) -> tuple[dict, dict]:
    directory = root / "results/all_pdf_visual_review_citation_v2"
    status = load(directory / "status.json")
    assert status["stage"] == "complete" and status["visual_quality_verified"]
    assert status["failure"] is None and status["expected_pdfs"] == len(status["papers"]) == 8
    reviewed_path = directory / "reviewed_pdf_manifest.json"
    reviewed = load(reviewed_path)
    assert len(reviewed["papers"]) == 8
    assert reviewed["review_sha256"] == status["review_sha256"]
    assert digest(reviewed_path) == status["reviewed_pdf_manifest_sha256"]
    assert "final_english_citation_revision" in reviewed["papers"]
    assert "final_english" not in reviewed["papers"]
    for record in reviewed["papers"].values():
        assert record["verdict"] == "pass" and record["pages"] > 0
        assert len(record["rendered_page_sha256"]) == record["pages"]
        assert digest(root / record["pdf"]) == record["pdf_sha256"]
    return status, reviewed


def require_revised_manuscripts(root: Path, reviewed: dict) -> tuple[list[Path], dict]:
    english = root / "paper/english_budget_complete_manuscript_citation_revision.md"
    chinese = root / "paper/论文预算完整机制稿.md"
    english_text = english.read_text("utf-8")
    chinese_text = chinese.read_text("utf-8")
    assert english_text.count("# 13 Prespecified Budget-Performance Sensitivity") == 1
    assert english_text.count("# 14 Conclusion") == 1
    assert chinese_text.count("# 13 预定预算性能敏感性") == 1
    assert chinese_text.count("# 14 结论") == 1
    assert "Using the COCO BBOB specification and IOHexperimenter implementation [8,9]" in english_text
    citation = audit_text(english_text, "# References")
    assert not citation["undefined_citations"] and not citation["uncited_references"]
    assert "151,201" in english_text and "151,201" in chinese_text
    assert "submission-ready superiority claim" in english_text
    assert "投稿就绪或普遍优越性声明" in chinese_text

    source_record_path = english.with_suffix(english.suffix + ".source.json")
    source_record = load(source_record_path)
    source = root / source_record["source"]
    assert source_record["source"] == "paper/english_budget_complete_manuscript.md"
    assert source_record["output"] == english.relative_to(root).as_posix()
    assert digest(source) == source_record["source_sha256"]
    assert digest(english) == source_record["output_sha256"]
    assert not source_record["scientific_results_changed"]

    source_hashes = load(root / "paper/budget_complete_manuscripts_source_hashes.json")
    assert source_hashes["verified_raw_result_hash_count"] == 7020
    assert source_hashes["verified_recovery_freeze_hash_count"] == 80
    for name, expected in source_hashes.items():
        if isinstance(expected, str) and len(expected) == 64:
            assert digest(root / name) == expected

    final_pdfs = {record["pdf"] for label, record in reviewed["papers"].items() if label.startswith("final_")}
    assert final_pdfs == {
        "paper/pdf/english_budget_complete_manuscript_citation_revision.pdf",
        "paper/pdf/论文预算完整机制稿.pdf",
    }
    return [english, chinese, source_record_path], citation


def main() -> None:
    assert not OUT.exists(), "Citation-corrected final audit exists; refuse duplicate restart"
    protocol_root = ROOT / "docs/frozen_final_delivery_citation_v2_protocol"
    protocol = load(protocol_root / "sha256.json")
    verify_hash_map(protocol_root, protocol)
    alive = {row["ProcessId"] for row in process_inventory()}
    visual_status, reviewed = require_citation_visual_complete(ROOT)
    assert visual_status["pid"] not in alive
    statuses = require_statuses(ROOT, alive)
    science = require_science(ROOT)
    third, third_frozen = require_third_recovery(ROOT)
    race = require_helper_race_archive(ROOT)
    manuscripts, citation = require_revised_manuscripts(ROOT, reviewed)
    OUT.mkdir(parents=True)

    completion_doc = ROOT / "docs/最终论文与实验完成核查_引用修订版.md"
    completion_doc.write_text(
        "# 最终论文与实验完成核查（引用修订版）\n\n"
        "全部科学状态、原始日志审计、第三次恢复逐点审计及引用修订版8份PDF的页级视觉检查均已通过。英文最终稿明确引用COCO BBOB规范与IOHexperimenter实现[8,9]，全文未定义引用和未引用参考文献均为0。\n\n"
        "该文字修订不改变算法、评价、统计、表格、图或结论。论文继续保留开发收益门槛失败、原BBOB实例6–10与CEC确认未执行、关键竞争SAEA可靠实现未取得的边界；完成表示当前失败机制研究及预定扩展证据链完整，不表示证明普遍优化优越性。\n",
        encoding="utf-8",
    )
    evidence = [
        *manuscripts,
        ROOT / "paper/english_budget_complete_manuscript_citation_revision.tex",
        ROOT / "paper/pdf/english_budget_complete_manuscript_citation_revision.pdf",
        ROOT / "paper/论文预算完整机制稿.tex",
        ROOT / "paper/pdf/论文预算完整机制稿.pdf",
        ROOT / "paper/budget_complete_manuscripts_source_hashes.json",
        ROOT / "results/all_pdf_visual_review_citation_v2/review.json",
        ROOT / "results/all_pdf_visual_review_citation_v2/reviewed_pdf_manifest.json",
        ROOT / "results/interruption_20260920_v3/third_recovery_audit.json",
        ROOT / "docs/frozen_third_recovery_audit_v1/sha256.json",
        completion_doc,
    ]
    for name in [
        "results/mechanism_validation_analysis_v1/full_integrity_audit.json",
        "results/basic_references_analysis_v1/audit.json",
        "results/turbo_reference_analysis_v1/audit.json",
        "results/gp_ei_reference_analysis_v1/audit.json",
        "results/solo_cost_analysis_v1/integrity_audit.json",
        "results/application_analysis_v1/audit.json",
        "results/application_high_analysis_v1/audit.json",
        "results/model_sensitivity_analysis_v1/audit.json",
        "results/budget_performance_sensitivity_analysis_v1/audit.json",
    ]:
        evidence.append(ROOT / name)
    assert all(path.is_file() for path in evidence)
    manifest = {path.relative_to(ROOT).as_posix(): digest(path) for path in evidence}
    manifest_path = ROOT / "paper/final_delivery_citation_v2_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    result = {
        "schema": "final_delivery_citation_v2_audit",
        "complete": True,
        "objective_calls_by_this_auditor": 0,
        "all_required_statuses_terminal": True,
        "all_scientific_audits_verified": True,
        "third_recovery_verified": third["all_canonical_trajectories_complete"],
        "third_recovery_redundant_calls": third["redundant_recovery_validation_calls"],
        "eight_citation_corrected_pdfs_visually_verified": True,
        "undefined_citations": len(citation["undefined_citations"]),
        "uncited_references": len(citation["uncited_references"]),
        "frozen_protocol_files": len(protocol),
        "third_recovery_frozen_files": len(third_frozen),
        "helper_race_archive_files": len(race["files"]),
        "scientific_results_changed_by_citation_revision": False,
        "development_gate_remains_failed": True,
        "submission_ready_claimed": False,
        "status_stages": statuses,
        "final_manifest_sha256": digest(manifest_path),
        "final_files": len(manifest),
    }
    (OUT / "audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
