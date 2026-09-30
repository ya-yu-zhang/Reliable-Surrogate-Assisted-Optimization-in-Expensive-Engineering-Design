from src.run_application_batch import prerequisite


def test_safe_entry_name_does_not_prefix_match_frozen_batch_name():
    command = "python.exe -m src.application_batch_venv_entry"
    assert "-m src.run_application_batch" not in command


def test_original_entry_name_would_prefix_match():
    command = "python.exe -m src.run_application_batch"
    assert "-m src.run_application_batch" in command


def test_frozen_prerequisite_remains_importable():
    assert callable(prerequisite)
