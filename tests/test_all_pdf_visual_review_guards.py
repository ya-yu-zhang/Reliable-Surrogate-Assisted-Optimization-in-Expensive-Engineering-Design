import pytest

from src import finish_all_pdf_visual_review as reviewer


def test_visual_scope_contains_six_intermediate_and_two_final_pdfs():
    assert len(reviewer.INTERMEDIATE) == 6
    assert len({name for name, _ in reviewer.INTERMEDIATE}) == 6
    assert len({label for _, label in reviewer.INTERMEDIATE}) == 6


def test_existing_all_pdf_record_refuses_duplicate(tmp_path, monkeypatch):
    monkeypatch.setattr(reviewer, "ROOT", tmp_path)
    monkeypatch.setattr(reviewer, "OUT", tmp_path / "results/all_pdf_visual_review_v1")
    reviewer.OUT.mkdir(parents=True)
    with pytest.raises(AssertionError, match="duplicate"):
        reviewer.main()
