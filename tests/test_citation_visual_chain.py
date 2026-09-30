from src.finish_citation_visual_review_v2 import compose_papers


def test_corrected_english_replaces_old_final_in_eight_pdf_set():
    original = {"final_english": {"pdf": "old.pdf"}, "final_chinese": {"pdf": "zh.pdf"}}
    original.update({f"intermediate_{index}": {"pdf": f"{index}.pdf"} for index in range(6)})
    revised = {"pdf": "revised.pdf"}
    result = compose_papers(original, revised)
    assert len(result) == 8
    assert "final_english" not in result
    assert result["final_english_citation_revision"] == revised
