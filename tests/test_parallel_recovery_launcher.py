from src.resume_interrupted_gp_batch_v2_parallel import matching_inventory


def test_only_same_configuration_process_is_visible():
    rows=[dict(ProcessId=1,CommandLine='python -m src.resume_interrupted_gp_batch_v2_parallel --config configs/turbo_reference.json'),
          dict(ProcessId=2,CommandLine='python -m src.resume_interrupted_gp_batch_v2_parallel --config configs/gp_ei_reference.json'),
          dict(ProcessId=3,CommandLine='unrelated')]
    assert [r['ProcessId'] for r in matching_inventory(rows,'configs/turbo_reference.json')]==[1]
