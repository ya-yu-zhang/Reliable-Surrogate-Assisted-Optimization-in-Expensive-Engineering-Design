import json

from src.build_integrated_manuscripts_pid_safe import pid_safe_inventory


def statuses(root):
    for stem, pid in (("reference_completion_v1", 17), ("application_completion_v1", 23)):
        path = root / "results" / stem
        path.mkdir(parents=True)
        (path / "status.json").write_text(json.dumps({"stage": "complete", "failure": None, "pid": pid}))


def test_pid_reuse_by_unrelated_process_is_filtered(tmp_path):
    statuses(tmp_path)
    inventory = [
        {"ProcessId": 17, "CommandLine": "blender-mcp.exe"},
        {"ProcessId": 23, "CommandLine": "node_repl.exe"},
        {"ProcessId": 31, "CommandLine": "python -m unrelated"},
    ]
    assert pid_safe_inventory(tmp_path, inventory) == [inventory[2]]


def test_identity_matched_live_pipeline_is_retained(tmp_path):
    statuses(tmp_path)
    inventory = [
        {"ProcessId": 17, "CommandLine": "python -m src.finish_reference_batch"},
        {"ProcessId": 23, "CommandLine": "python -m src.finish_application_after_recovery_v3"},
    ]
    assert pid_safe_inventory(tmp_path, inventory) == inventory
