from src.run_solo_cost_portable import portable_frozen_manifest


def test_only_known_source_keys_are_slash_normalized():
    frozen = {
        "src\\run_solo_cost.py": "a" * 64,
        "configs\\solo_cost.json": "b" * 64,
        "literature\\source-code\\TuRBO\\turbo\\turbo_1.py": "c" * 64,
    }
    sources = ["src/run_solo_cost.py", "configs/solo_cost.json"]
    corrected = portable_frozen_manifest(frozen, sources)
    assert corrected == {
        "src/run_solo_cost.py": "a" * 64,
        "configs/solo_cost.json": "b" * 64,
        "literature\\source-code\\TuRBO\\turbo\\turbo_1.py": "c" * 64,
    }


def test_duplicate_portable_key_is_rejected():
    frozen = {"src\\x.py": "a", "src/x.py": "b"}
    try:
        portable_frozen_manifest(frozen, ["src/x.py"])
    except AssertionError as error:
        assert "Duplicate portable manifest key" in str(error)
    else:
        raise AssertionError("duplicate key was accepted")
