"""Final objective-free audit across experiments, manuscripts, and visual QA."""
import hashlib
import json
from pathlib import Path

from .run_solo_cost import process_inventory


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/final_delivery_audit_v1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(root, name):
    return json.loads((root / name).read_text("utf-8"))


def require_visual_complete(root=ROOT):
    status = load(root, "results/all_pdf_visual_review_v1/status.json")
    assert status["stage"] == "complete" and status["visual_quality_verified"]
    assert status["failure"] is None and status["expected_pdfs"] == len(status["papers"]) == 8
    reviewed = load(root, "results/all_pdf_visual_review_v1/reviewed_pdf_manifest.json")
    assert len(reviewed["papers"]) == 8
    assert reviewed["review_sha256"] == status["review_sha256"]
    assert digest(root / "results/all_pdf_visual_review_v1/reviewed_pdf_manifest.json") == status["reviewed_pdf_manifest_sha256"]
    for record in reviewed["papers"].values():
        assert record["verdict"] == "pass" and record["pages"] > 0
        assert len(record["rendered_page_sha256"]) == record["pages"]
        assert digest(root / record["pdf"]) == record["pdf_sha256"]
    return status, reviewed


def require_statuses(root, alive):
    expected = {
        "results/turbo_reference_v1/status.json": "complete",
        "results/gp_ei_reference_v1/status.json": "complete",
        "results/reference_completion_v1/status.json": "complete",
        "results/application_completion_v1/status.json": "complete",
        "results/evidence_export_v1/status.json": "compiled_pending_visual_review",
        "results/high_extension_completion_v1/status.json": "complete",
        "results/high_evidence_export_v1/status.json": "compiled_pending_visual_review",
        "results/model_sensitivity_completion_v1/status.json": "complete",
        "results/sensitivity_evidence_export_v1/status.json": "compiled_pending_visual_review",
        "results/budget_performance_sensitivity_completion_v1/status.json": "complete",
        "results/budget_evidence_export_v1/status.json": "compiled_pending_visual_review",
    }
    rows = {}
    for name, stage in expected.items():
        status = load(root, name)
        assert status["stage"] in ([stage, "complete"] if "evidence_export" in name else [stage])
        assert status.get("failure") is None
        assert status["pid"] not in alive
        rows[name] = status["stage"]
    for name in ["results/turbo_reference_v1/status.json", "results/gp_ei_reference_v1/status.json"]:
        status = load(root, name)
        assert status["completed"] == status["expected"] == 648 and status["failed"] == 0
    return rows


def require_science(root):
    mechanism = load(root, "results/mechanism_validation_analysis_v1/full_integrity_audit.json")
    assert mechanism["runs"] == 3888 and mechanism["algorithm_evaluations"] == 907200
    assert mechanism["diagnostic_evaluations"] == 1990656 and mechanism["states"] == 7776
    assert mechanism["complete_cartesian_design"] and mechanism["paid_prefix_and_pre_information_verified"]
    basic = load(root, "results/basic_references_analysis_v1/audit.json")
    assert basic["audited_runs"] == 1296 and basic["algorithm_evaluations"] == 302400 and basic["failures"] == 0
    gp = {}
    for stem in ["turbo_reference", "gp_ei_reference"]:
        audit = load(root, f"results/{stem}_analysis_v1/audit.json")
        assert audit["audited_runs"] == 648 and audit["algorithm_evaluations"] == 151200
        assert audit["failures"] == 0 and audit["all_calls_charged"] and audit["no_future_labels_in_pre"]
        gp[stem] = audit
    recovery = load(root, "results/interruption_20260919_v2/second_recovery_audit.json")
    assert recovery["redundant_recovery_validation_calls"] == 1
    assert not recovery["redundant_call_entered_optimizer_history"]
    assert recovery["all_canonical_trajectories_complete"] and recovery["objective_calls_by_this_auditor"] == 0
    solo = load(root, "results/solo_cost_analysis_v1/integrity_audit.json")
    assert solo["runs"] == 54 and solo["algorithm_evaluations"] == 12600 and solo["complete_design"]
    application = load(root, "results/application_analysis_v1/audit.json")
    assert application["runs"] == 480 and application["algorithm_evaluations"] == 240000
    assert application["cv_fold_solves"] == 1200000 and application["post_completion_test_calls"] == 480
    assert application["complete_design"] and application["statistical_family_size"] == 3
    high = load(root, "results/application_high_analysis_v1/audit.json")
    assert high["runs"] == 160 and high["algorithm_evaluations"] == 160000
    assert high["cv_fold_solves"] == 800000 and high["post_completion_test_calls"] == 160
    assert high["complete_design"] and high["statistical_tests_added"] == 0
    sensitivity = load(root, "results/model_sensitivity_analysis_v1/audit.json")
    assert sensitivity["runs"] == 450 and sensitivity["algorithm_evaluations"] == 135000
    assert sensitivity["raw_file_hashes"] == 1350 and sensitivity["statistical_tests_added"] == 0
    budget = load(root, "results/budget_performance_sensitivity_analysis_v1/audit.json")
    assert budget["runs"] == 2700 and budget["algorithm_evaluations"] == 270000
    assert budget["raw_file_hashes"] == 7020 and budget["internal_budget_prefix_invariant_runs"] == 540
    assert budget["statistical_tests_added"] == 0 and budget["not_used_for_parameter_selection"]
    return dict(
        mechanism=mechanism, basic=basic, gp=gp, recovery=recovery, solo=solo,
        application=application, high=high, sensitivity=sensitivity, budget=budget,
    )


def require_manuscripts(root, reviewed):
    english = root / "paper/english_budget_complete_manuscript.md"
    chinese = root / "paper/论文预算完整机制稿.md"
    texts = [english.read_text("utf-8"), chinese.read_text("utf-8")]
    assert texts[0].count("# 13 Prespecified Budget-Performance Sensitivity") == 1
    assert texts[0].count("# 14 Conclusion") == 1
    assert texts[1].count("# 13 预定预算性能敏感性") == 1
    assert texts[1].count("# 14 结论") == 1
    assert "151,201" in texts[0] and "151,201" in texts[1]
    assert "one disclosed recovery-validation call" in texts[0]
    assert "1次公开的恢复验证调用" in texts[1]
    assert "submission-ready superiority claim" in texts[0]
    assert "投稿就绪或普遍优越性声明" in texts[1]
    assert "Their complete outcomes are not included until all runs and audits finish." not in texts[0]
    assert "正式GP-EI/TuRBO完整批次尚在执行" not in texts[1]
    sources = load(root, "paper/budget_complete_manuscripts_source_hashes.json")
    assert sources["verified_raw_result_hash_count"] == 7020
    assert sources["verified_recovery_freeze_hash_count"] == 80
    for name, value in sources.items():
        if isinstance(value, str) and len(value) == 64:
            assert digest(root / name) == value
    final_pdf_names = {record["pdf"] for record in reviewed["papers"].values() if "budget_complete" in record["pdf"] or "预算完整" in record["pdf"]}
    assert final_pdf_names == {
        "paper/pdf/english_budget_complete_manuscript.pdf",
        "paper/pdf/论文预算完整机制稿.pdf",
    }
    return [english, chinese]


def main():
    assert not OUT.exists(), "Final delivery audit exists; refuse duplicate restart"
    frozen = load(ROOT, "docs/frozen_final_delivery_v1/sha256.json")
    assert all(digest(ROOT / name) == value for name, value in frozen.items())
    alive = {process["ProcessId"] for process in process_inventory()}
    visual_status, reviewed = require_visual_complete(ROOT)
    assert visual_status["pid"] not in alive
    statuses = require_statuses(ROOT, alive)
    science = require_science(ROOT)
    manuscripts = require_manuscripts(ROOT, reviewed)
    OUT.mkdir(parents=True)

    completion_doc = ROOT / "docs/最终论文与实验完成核查.md"
    completion_doc.write_text(
        "# 最终论文与实验完成核查\n\n"
        "完整证据链已经通过机器审计及八份PDF逐页视觉检查。机制验证为3,888运行/907,200次算法评价及1,990,656次独立诊断评价；Sobol/CMA-ES为1,296运行/302,400评价；GP-EI与TuRBO各648运行/151,200规范评价。GP-EI恢复总账另含1次不进入优化历史的冗余物理验证调用。\n\n"
        "独占成本为54运行/12,600评价；主要LassoBench为480运行/240,000验证评价、1,200,000折求解及480次完成后测试；300维扩展为160运行/160,000验证评价、800,000折求解及160次完成后测试；模型敏感性为450运行/135,000评价；预算敏感性为2,700运行/270,000评价。各自全量原始审计均通过。\n\n"
        "最终中英文工作稿包含预算第13节和第14节结论，全部证据阶段8份PDF均有页级图像哈希与通过记录。论文仍如实保留开发优化收益门槛失败、原BBOB实例6–10与CEC确认未执行、Temporal CP-SAEA/SADE-SS/BGP-SAEA等可靠实现未取得的边界；完成表示当前失败机制研究稿及其预定扩展证据完整，不表示已经证明新优化方法普遍优越或自动达到投稿接收标准。\n",
        encoding="utf-8",
    )
    evidence = [
        *manuscripts,
        ROOT / "paper/english_budget_complete_manuscript.tex",
        ROOT / "paper/论文预算完整机制稿.tex",
        ROOT / "paper/pdf/english_budget_complete_manuscript.pdf",
        ROOT / "paper/pdf/论文预算完整机制稿.pdf",
        ROOT / "paper/budget_complete_manuscripts_source_hashes.json",
        ROOT / "results/all_pdf_visual_review_v1/review.json",
        ROOT / "results/all_pdf_visual_review_v1/reviewed_pdf_manifest.json",
        ROOT / "results/interruption_20260919_v2/second_recovery_audit.json",
        completion_doc,
    ]
    audits = [
        "results/mechanism_validation_analysis_v1/full_integrity_audit.json",
        "results/basic_references_analysis_v1/audit.json",
        "results/turbo_reference_analysis_v1/audit.json",
        "results/gp_ei_reference_analysis_v1/audit.json",
        "results/solo_cost_analysis_v1/integrity_audit.json",
        "results/application_analysis_v1/audit.json",
        "results/application_high_analysis_v1/audit.json",
        "results/model_sensitivity_analysis_v1/audit.json",
        "results/budget_performance_sensitivity_analysis_v1/audit.json",
    ]
    evidence += [ROOT / name for name in audits]
    assert all(path.is_file() for path in evidence)
    manifest = {path.relative_to(ROOT).as_posix(): digest(path) for path in evidence}
    manifest_path = ROOT / "paper/final_delivery_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    audit = dict(
        complete=True,
        objective_calls_by_this_auditor=0,
        all_required_statuses_terminal=True,
        all_scientific_audits_verified=True,
        eight_pdfs_visually_verified=True,
        final_bilingual_manuscripts_verified=True,
        recovery_extra_physical_calls=1,
        development_gate_remains_failed=True,
        original_bbob_confirmation_and_cec_not_claimed=True,
        reliable_key_saea_gap_disclosed=True,
        submission_ready_claimed=False,
        status_stages=statuses,
        final_delivery_manifest_sha256=digest(manifest_path),
        final_delivery_files=len(manifest),
    )
    (OUT / "audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
