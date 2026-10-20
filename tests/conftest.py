"""Environment guards for the test suite.

The CMA-ES baseline needs the cma 4.x bounds interface. A cma 3.x install (for
example the one pymoo pins) raises inside ``BoxConstraintsLinQuadTransformation``
rather than reporting a version problem, which reads like a code failure. Skip the
parametrised CMA-ES case with an actionable reason instead, and let every other test
run normally.
"""

from __future__ import annotations

import pytest


def _cma_major():
    try:
        import cma
    except Exception:
        return None
    try:
        return int(str(cma.__version__).split(".")[0])
    except Exception:
        return None


CMA_MAJOR = _cma_major()


def pytest_collection_modifyitems(config, items):
    if CMA_MAJOR is None or CMA_MAJOR >= 4:
        return
    reason = (
        "cma %s.x is installed; the CMA-ES reference needs the 4.x bounds interface. "
        "Install the pinned baselines environment (pip install -r requirements-baselines.txt, "
        "cma==4.5.0) instead of the cma that pymoo pulls in." % CMA_MAJOR
    )
    skip = pytest.mark.skip(reason=reason)
    for item in items:
        if item.nodeid.endswith("[cma_es]"):
            item.add_marker(skip)
