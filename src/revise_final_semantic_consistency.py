"""Remove stale phase-status claims after all prespecified evidence has been integrated."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHINESE_OLD = "证据边界还包括：没有开展BBOB主确认、CEC2017、LassoBench应用和完整外部基线；Temporal CP-SAEA、SADE-SS、BGP-SAEA部分全文/可靠代码缺口仍在。"
CHINESE_NEW = "证据边界还包括：没有开展原计划BBOB实例6–10主确认、CEC2017确认及关键SAEA可靠实现复现；LassoBench三任务应用、GP-EI/TuRBO和基础外部参照已经完成。Temporal CP-SAEA、SADE-SS、BGP-SAEA部分全文或可靠代码缺口仍在。"
FORBIDDEN = (
    "LassoBench应用和完整外部基线",
    "正式GP-EI/TuRBO完整批次尚在执行",
    "Their complete outcomes are not included until all runs and audits finish.",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def revise_text(text: str, *, chinese: bool) -> str:
    if chinese:
        assert text.count(CHINESE_OLD) == 1
        text = text.replace(CHINESE_OLD, CHINESE_NEW, 1)
    assert not any(phrase in text for phrase in FORBIDDEN)
    return text


def main() -> None:
    papers = [
        (ROOT / "paper/english_budget_complete_manuscript.md", False),
        (ROOT / "paper/论文预算完整机制稿.md", True),
    ]
    assert all(path.is_file() for path, _ in papers)
    record_path = ROOT / "paper/budget_complete_manuscripts_source_hashes.json"
    sources = json.loads(record_path.read_text("utf-8"))
    before_record = digest(record_path)
    changes = []
    for path, chinese in papers:
        relative = path.relative_to(ROOT).as_posix()
        assert sources[relative] == digest(path)
        old_hash = digest(path); old_text = path.read_text("utf-8")
        new_text = revise_text(old_text, chinese=chinese)
        path.write_text(new_text, encoding="utf-8")
        new_hash = digest(path); assert new_hash != old_hash if chinese else new_hash == old_hash
        sources[relative] = new_hash
        changes.append({"path": relative, "before_sha256": old_hash, "after_sha256": new_hash,
                        "changed": old_hash != new_hash, "scientific_results_changed": False})
    semantic = ROOT / "paper/final_semantic_consistency_revision.json"
    semantic.write_text(json.dumps({
        "schema": "final_semantic_consistency_revision_v1",
        "source_hash_record_before": before_record,
        "changes": changes,
        "removed_stale_claims": list(FORBIDDEN),
        "scientific_results_changed": False,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    sources[semantic.relative_to(ROOT).as_posix()] = digest(semantic)
    record_path.write_text(json.dumps(sources, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
