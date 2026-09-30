from src.finish_solo_cost_when_idle import retryable_cost_failure


def test_only_background_cpu_failure_is_retryable():
    status = {
        "stage": "failed",
        "completed": 7,
        "failure": {"error": "Background CPU 6.20% exceeds frozen threshold", "completed": 7},
    }
    assert retryable_cost_failure(status)
    status["failure"]["error"] = "Scientific processes still active"
    assert not retryable_cost_failure(status)


def test_completed_count_must_match():
    status = {
        "stage": "failed",
        "completed": 7,
        "failure": {"error": "Background CPU 6.20% exceeds frozen threshold", "completed": 6},
    }
    assert not retryable_cost_failure(status)
