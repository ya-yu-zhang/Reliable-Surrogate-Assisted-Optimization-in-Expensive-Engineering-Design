from src.audit_final_provenance_bundle import classify_issues, collect_provenance_files


def test_issue_classifier_only_accepts_documented_history():
    live = [
        {"freeze": "frozen_plan_delivery_bundle_protocol_v1", "path": "docs/论文与实验范围总账20260919.md"},
        {"freeze": "other", "path": "src/drift.py"},
    ]
    copies = [
        {"freeze": "frozen_v1", "path": "configs/development.json", "expected_copy": "missing"},
        {"freeze": "other", "path": "src/lost.py", "expected_copy": "missing"},
    ]
    allowed, unexpected_live, known, unexpected_copy = classify_issues(live, copies)
    assert allowed == live[:1] and unexpected_live == live[1:]
    assert known == copies[:1] and unexpected_copy == copies[1:]


def test_provenance_collection_includes_code_config_locks_and_hash_indexes(tmp_path):
    for name in [
        "src/a.py", "tests/test_a.py", "configs/a.json", "docs/core-environment-lock.txt",
        "results/x/source_hashes.json", "paper/plan_delivery_bundle_manifest.json",
        "paper/final_delivery_citation_v2_manifest.json", "results/final_delivery_citation_v2_audit/audit.json",
        "results/plan_delivery_bundle_audit_v1/audit.json", "docs/原始计划书.md",
        "docs/论文与实验范围总账20260919.md", "docs/计划书逐项完成核查.md",
    ]:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")
    freeze = tmp_path / "docs/frozen_x/sha256.json"
    freeze.parent.mkdir(parents=True)
    freeze.write_text("{}", encoding="utf-8")
    found = {path.relative_to(tmp_path).as_posix() for path in collect_provenance_files(tmp_path, [freeze])}
    assert {"src/a.py", "tests/test_a.py", "configs/a.json", "docs/core-environment-lock.txt"} <= found
    assert "results/x/source_hashes.json" in found and "docs/frozen_x/sha256.json" in found
