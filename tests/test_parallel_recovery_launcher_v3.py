from src.resume_interrupted_gp_batch_v3_parallel import matching_inventory


def test_only_same_python_module_and_configuration_is_visible():
    rows=[dict(ProcessId=1,CommandLine='"C:\\Python\\python.exe" -m src.resume_interrupted_gp_batch_v3_parallel --config configs/turbo_reference.json'),
          dict(ProcessId=2,CommandLine='"C:\\Python\\python.exe" -m src.resume_interrupted_gp_batch_v3_parallel --config configs/gp_ei_reference.json'),
          dict(ProcessId=3,CommandLine='pwsh.exe -Command ".\\python.exe -m src.resume_interrupted_gp_batch_v3_parallel --config configs/turbo_reference.json"'),
          dict(ProcessId=4,CommandLine='unrelated')]
    assert [r['ProcessId'] for r in matching_inventory(rows,'configs/turbo_reference.json')]==[1]
