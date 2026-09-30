import json

import pytest

from src import audit_final_delivery as auditor
from src import finish_final_delivery as finisher


def test_visual_incomplete_refuses_final_audit(tmp_path):
    path = tmp_path / "results/all_pdf_visual_review_v1"
    path.mkdir(parents=True)
    (path / "status.json").write_text(
        json.dumps(dict(stage="rendered_pending_visual_inspection", visual_quality_verified=False, failure=None, expected_pdfs=8, papers={})),
        encoding="utf-8",
    )
    with pytest.raises(AssertionError):
        auditor.require_visual_complete(tmp_path)


def test_existing_final_completion_refuses_duplicate(tmp_path, monkeypatch):
    monkeypatch.setattr(finisher, "ROOT", tmp_path)
    monkeypatch.setattr(finisher, "OUT", tmp_path / "results/final_delivery_completion_v1")
    finisher.OUT.mkdir(parents=True)
    with pytest.raises(AssertionError, match="duplicate"):
        finisher.main()
