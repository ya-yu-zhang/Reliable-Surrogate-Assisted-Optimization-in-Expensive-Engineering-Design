"""Idempotent factual availability fix after source regeneration.

Supply freshly verified visibility; scientific tables/claims are not rewritten.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://github.com/ya-yu-zhang/Reliable-Surrogate-Assisted-Optimization-in-Expensive-Engineering-Design'
OLD = 'The manuscript sources, implementation, frozen configurations, and dependency records are available in the public repository ' + URL + '.'
PRIVATE = 'The manuscript sources, implementation, frozen configurations, and dependency records are stored in the private repository ' + URL + '. Reviewer access to the scoped reproduction materials remains to be arranged before submission.'

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--verified-visibility', required=True, choices=['private', 'public'])
    p.add_argument('--include-acquired-physical-bound-cost', action='store_true')
    args = p.parse_args()
    for name in ['EO_manuscript.tex', 'EO_supplementary.tex']:
        path = ROOT / 'paper/engineering_optimization' / name
        text = path.read_text()
        if text.count(OLD) + text.count(PRIVATE) != 1:
            raise ValueError('Unexpected availability paragraph: ' + name)
        result = text.replace(OLD, PRIVATE) if args.verified_visibility == 'private' else text.replace(PRIVATE, OLD)
        result = result.replace('Public visibility should not be interpreted as an open-source license;',
                                'Access to these materials does not grant an open-source license;')
        if name == 'EO_manuscript.tex':
            result = result.replace('Sections 6.3-6.4 provide the additional GP evidence.',
                                    'Sections 6.3-6.5 provide the additional GP evidence.')
        if result != text:
            path.write_text(result)
    if args.include_acquired_physical_bound_cost:
        status = json.loads((ROOT / 'results/engineering_optimization_physical_bound_screen_v1/run_status.json').read_text())
        attempts = status['new_physics_attempts']
        total = 55305 + attempts
        path = ROOT / 'paper/engineering_optimization/EO_manuscript.tex'
        text = path.read_text()
        old = 'The cumulative ledger including later released checks is 55,305 paid physics attempts; its stage-wise boundary is reported in the supplement.'
        new = f'The reported optimizer and audit experiments account for 55,305 paid physics attempts. Subsequent auxiliary physical-bound development used {attempts} reference solves, bringing the project total to {total:,}; the stage-wise boundary is reported in the supplement.'
        if old in text:
            text = text.replace(old, new, 1)
        elif new not in text:
            raise ValueError('Unexpected cumulative-cost sentence')
        path.write_text(text)
        path = ROOT / 'paper/engineering_optimization/integrated_evidence/supp_records.tex'
        text = path.read_text()
        old_row = 'Full revision cumulative paid attempts & 55305 & Earlier historical experiments outside this revision excluded \\\\'
        new_rows = f'Auxiliary physical-bound development & {attempts} & Reference solves only; no new optimizer samples \\\\\nFull revision cumulative paid attempts & {total} & Includes auxiliary development; earlier historical experiments excluded \\\\'
        if old_row in text:
            text = text.replace(old_row, new_rows, 1)
        elif new_rows not in text:
            raise ValueError('Unexpected supplemental cumulative-cost row')
        path.write_text(text)
        path = ROOT / 'paper/engineering_optimization/integrated_evidence/table_inputs.json'
        data = json.loads(path.read_text())
        data['reported_optimizer_audit_physics_attempts'] = 55305
        data['auxiliary_physical_bound_reference_attempts'] = attempts
        data['cumulative_physics_attempts'] = total
        path.write_text(json.dumps(data, indent=2) + '\n')
    print('Verified-visibility overlay applied; repeated invocation preserves source bytes.')

if __name__ == '__main__':
    main()
