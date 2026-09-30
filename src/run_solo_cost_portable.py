"""Run the frozen solo-cost code with exact Windows manifest-key portability."""

from __future__ import annotations

import json as standard_json
from pathlib import Path

from . import run_solo_cost as frozen_runner
from .run_solo_cost_launcher_safe import refuse_overlap


ROOT = Path(__file__).resolve().parents[1]


def portable_frozen_manifest(payload: dict[str, str], sources: list[str]) -> dict[str, str]:
    source_keys = set(sources)
    corrected: dict[str, str] = {}
    for key, value in payload.items():
        slash_key = key.replace("\\", "/")
        target = slash_key if slash_key in source_keys else key
        if target in corrected:
            raise AssertionError(f"Duplicate portable manifest key: {target}")
        corrected[target] = value
    return corrected


class PortableJSON:
    def __init__(self, exact_payload: dict[str, str], portable_payload: dict[str, str]):
        self.exact_payload = exact_payload
        self.portable_payload = portable_payload

    def loads(self, text: str, *args, **kwargs):
        value = standard_json.loads(text, *args, **kwargs)
        return self.portable_payload if value == self.exact_payload else value

    def __getattr__(self, name: str):
        return getattr(standard_json, name)


def main() -> None:
    freeze_path = ROOT / "docs/frozen_solo_cost_v1/sha256.json"
    exact = standard_json.loads(freeze_path.read_text("utf-8"))
    portable = portable_frozen_manifest(exact, frozen_runner.SOURCES)
    assert set(portable) == set(frozen_runner.SOURCES) | {
        str(path.relative_to(ROOT))
        for path in sorted((ROOT / "literature/source-code/TuRBO/turbo").glob("*.py"))
    }
    frozen_runner.json = PortableJSON(exact, portable)
    frozen_runner.refuse_overlap = refuse_overlap
    frozen_runner.main()


if __name__ == "__main__":
    main()
