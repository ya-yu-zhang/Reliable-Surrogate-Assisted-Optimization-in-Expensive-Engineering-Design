import pytest
from src.revise_final_semantic_consistency import CHINESE_OLD,CHINESE_NEW,revise_text

def test_stale_lassobench_claim_is_replaced_once():
    text="前文\n"+CHINESE_OLD+" 后文"
    result=revise_text(text,chinese=True)
    assert CHINESE_OLD not in result and result.count(CHINESE_NEW)==1

def test_missing_expected_stale_claim_refuses_silent_rewrite():
    with pytest.raises(AssertionError):revise_text("没有预期原句",chinese=True)

def test_english_is_unchanged_when_no_stale_claim_exists():
    text="Complete application evidence is reported."
    assert revise_text(text,chinese=False)==text
