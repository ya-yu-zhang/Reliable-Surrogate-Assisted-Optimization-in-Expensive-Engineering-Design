import json
from pathlib import Path
import numpy as np

from src.engineering_beam_shared_init import CONFIG, audit_shared_sources, shared_archive


def test_all_internal_methods_have_identical_shared_archive():
    cfg = json.loads(CONFIG.read_text("utf-8"))
    audit = audit_shared_sources(cfg)
    assert len(audit) == cfg["repeats"]
    assert all(row["count"] == cfg["shared_initial_evaluations"] for row in audit)


def test_shared_archives_are_finite_and_repeat_specific():
    cfg = json.loads(CONFIG.read_text("utf-8"))
    digests = []
    for rep in range(cfg["repeats"]):
        points, values, digest, source = shared_archive(rep, cfg)
        assert points.shape == (58, 19)
        assert values.shape == (58,)
        assert np.isfinite(points).all() and np.isfinite(values).all()
        assert Path(source).exists()
        digests.append(digest)
    assert len(set(digests)) == cfg["repeats"]
