from src.run_solo_cost_launcher_safe import ancestor_pids, find_overlaps


def row(pid, parent, command):
    return {"ProcessId": pid, "ParentProcessId": parent, "CommandLine": command}


def test_excludes_current_venv_ancestor_only():
    entries = [
        row(10, 0, "shell"),
        row(20, 10, "python.exe -m src.run_solo_cost_launcher_safe"),
        row(30, 20, "python.exe -m src.run_solo_cost_launcher_safe"),
    ]
    assert ancestor_pids(entries, 30) == {10, 20}
    assert find_overlaps(entries, 30) == []


def test_rejects_sibling_safe_launcher_and_scientific_worker():
    entries = [
        row(20, 0, "python.exe -m src.run_solo_cost_launcher_safe"),
        row(30, 20, "python.exe -m src.run_solo_cost_launcher_safe"),
        row(40, 0, "python.exe -m src.run_solo_cost_launcher_safe"),
        row(50, 0, "python.exe -m src.gp_references --method gp_ei"),
        row(60, 0, "python.exe -m unrelated.module"),
    ]
    assert [item["ProcessId"] for item in find_overlaps(entries, 30)] == [40, 50]


def test_parent_cycle_is_bounded():
    entries = [row(10, 20, "a"), row(20, 10, "b")]
    assert ancestor_pids(entries, 10) == {10, 20}
