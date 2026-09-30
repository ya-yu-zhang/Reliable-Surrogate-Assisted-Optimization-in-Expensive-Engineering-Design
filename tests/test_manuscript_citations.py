from src.audit_manuscript_citations import audit_text, body_citations, expand_group
from src.revise_final_citations import NEW, OLD, revise


def test_numeric_groups_and_math_vectors_are_distinguished():
    assert expand_group("1–3") == {1, 2, 3}
    assert body_citations("Prior work [1–3,5]; domain [0,1] and vector [1,0].") == {1, 2, 3, 5}


def test_reference_audit_finds_orphan_without_undefined_citation():
    text = "Body [1].\n\n# References\n\n[1] One. <https://one.example>.\n\n[2] Two. DOI:10.1000/two.\n"
    result = audit_text(text, "# References")
    assert result["undefined_citations"] == []
    assert result["uncited_references"] == [2]


def test_revision_removes_final_english_orphans():
    text = (
        OLD
        + "\n\nEarlier sources [1–7].\n\n# References\n\n"
        + "\n\n".join(f"[{i}] Reference {i}. <https://example.com/{i}>." for i in range(1, 10))
        + "\n"
    )
    revised = revise(text)
    assert NEW in revised and OLD not in revised
    assert audit_text(revised, "# References")["uncited_references"] == []
