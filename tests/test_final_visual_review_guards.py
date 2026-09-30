from pathlib import Path

from PIL import Image
import pytest

from src import finish_final_visual_review as reviewer


def test_page_count_parser():
    assert reviewer.page_count("Title: example\nPages:          17\nPage size: A4") == 17
    with pytest.raises(AssertionError):
        reviewer.page_count("Pages: 0")


def test_contact_sheets_cover_every_page(tmp_path):
    pages = []
    for number in range(7):
        path = tmp_path / f"page-{number + 1}.png"
        Image.new("RGB", (100, 140), (255, 255 - number, 255)).save(path)
        pages.append(path)
    outputs = reviewer.contact_sheets(pages, tmp_path / "contacts", columns=2, rows=3, thumb_width=50)
    assert len(outputs) == 2 and all(path.stat().st_size > 0 for path in outputs)


def test_existing_visual_record_refuses_duplicate(tmp_path, monkeypatch):
    monkeypatch.setattr(reviewer, "ROOT", tmp_path)
    monkeypatch.setattr(reviewer, "OUT", tmp_path / "results/final_visual_review_v1")
    reviewer.OUT.mkdir(parents=True)
    with pytest.raises(AssertionError, match="duplicate"):
        reviewer.main()
