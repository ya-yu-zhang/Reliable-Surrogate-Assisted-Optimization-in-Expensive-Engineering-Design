"""Canonicalise the data-availability paragraph in the LaTeX sources.

The statement must match the repository's actual visibility. It now says the records
are released upon acceptance, because the repository is private while the manuscript
is under review. Older variants ("available in the public repository", "stored in the
private repository ... remains to be arranged") are replaced by the current wording so
that a regenerated source cannot resurrect a claim that is not true.

The optional cumulative-cost overlay is unchanged; it only rewrites the paid-attempt
sentence and the ledger rows.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://github.com/ya-yu-zhang/Reliable-Surrogate-Assisted-Optimization-in-Expensive-Engineering-Design'
CURRENT = (
    'The manuscript sources, the implementation, the frozen configurations, the dependency records and '
    'the released records supporting the added results will be made publicly available in the project '
    'repository \\url{' + URL + '} upon acceptance, and the same materials are available to reviewers '
    'during peer review on request.'
)
LEGACY_PUBLIC = (
    'The manuscript sources, implementation, frozen configurations, and dependency records are available '
    'in the public repository ' + URL + '.'
)
LEGACY_PRIVATE = (
    'The manuscript sources, implementation, frozen configurations, and dependency records are stored in '
    'the private repository ' + URL + '. Reviewer access to the scoped reproduction materials remains to '
    'be arranged before submission.'
)
LEGACY = (LEGACY_PUBLIC, LEGACY_PRIVATE)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--include-acquired-physical-bound-cost', action='store_true')
    args = parser.parse_args()
    for name in ['EO_manuscript.tex', 'EO_supplementary.tex']:
        path = ROOT / 'paper' / 'engineering_optimization' / name
        text = path.read_text(encoding='utf-8')
        if text.count(CURRENT) == 1:
            continue
        if sum(text.count(item) for item in LEGACY) != 1:
            raise ValueError('Unexpected availability paragraph: ' + name)
        for item in LEGACY:
            text = text.replace(item, CURRENT)
        path.write_text(text, encoding='utf-8')
    if args.include_acquired_physical_bound_cost:
        status = json.loads((ROOT / 'results/engineering_optimization_physical_bound_screen_v1/run_status.json').read_text(encoding='utf-8'))
        attempts = status['new_physics_attempts']
        total = 55305 + attempts
        path = ROOT / 'paper/engineering_optimization/EO_manuscript.tex'
        text = path.read_text(encoding='utf-8')
        old = 'The cumulative ledger including later released checks is 55,305 paid physics attempts; its stage-wise boundary is reported in the supplement.'
        new = f'The reported optimizer and audit experiments account for 55,305 paid physics attempts. Subsequent auxiliary physical-bound development used {attempts} reference solves, bringing the project total to {total:,}; the stage-wise boundary is reported in the supplement.'
        if old in text:
            text = text.replace(old, new, 1)
        elif new not in text:
            raise ValueError('Unexpected cumulative-cost sentence')
        path.write_text(text, encoding='utf-8')
        path = ROOT / 'paper/engineering_optimization/integrated_evidence/supp_records.tex'
        text = path.read_text(encoding='utf-8')
        old_row = 'Full revision cumulative paid attempts & 55305 & Earlier historical experiments outside this revision excluded \\\\'
        new_rows = (f'Auxiliary physical-bound development & {attempts} & Reference solves only; no new optimizer samples \\\\\n'
                    f'Full revision cumulative paid attempts & {total} & Includes auxiliary development; earlier historical experiments excluded \\\\')
        if old_row in text:
            text = text.replace(old_row, new_rows, 1)
        elif new_rows not in text:
            raise ValueError('Unexpected supplemental cumulative-cost row')
        path.write_text(text, encoding='utf-8')
        path = ROOT / 'paper/engineering_optimization/integrated_evidence/table_inputs.json'
        data = json.loads(path.read_text(encoding='utf-8'))
        data['reported_optimizer_audit_physics_attempts'] = 55305
        data['auxiliary_physical_bound_reference_attempts'] = attempts
        data['cumulative_physics_attempts'] = total
        path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    print('Availability paragraph canonicalised; repeated invocation preserves source bytes.')


if __name__ == '__main__':
    main()
