"""Restore manuscript assets from the immutable baseline and saved timings.

Run from a checkout of the contribution branch. No engineering response,
bound query, witness or optimization run is invoked.
"""
import hashlib
import json
from pathlib import Path
import shutil
from .rebuild_gp_completion_figure import rebuild


def restore(root):
    root = Path(root)
    prep = root/'submission_20261014'
    paper = prep/'source/paper/engineering_optimization'
    rebuild(root, paper)
    missing = []
    for row in json.loads((prep/'SOURCE_VERIFICATION.json').read_text())['source_files']:
        destination = prep/row['path']
        if not destination.exists():
            origin = root/Path(row['path']).relative_to('source')
            if origin.is_file() and hashlib.sha256(origin.read_bytes()).hexdigest() == row['sha256']:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(origin, destination)
            else:
                missing.append(row['path'])
                continue
        assert destination.stat().st_size == row['bytes'], row['path']
        assert hashlib.sha256(destination.read_bytes()).hexdigest() == row['sha256'], row['path']
    if missing:
        raise FileNotFoundError('Use the scoped review archive for missing assets: '+', '.join(missing))
    print('All manuscript source/figure hashes match; no solver invoked. Obtain official publisher assets separately.')


if __name__ == '__main__':
    restore(Path(__file__).resolve().parents[1])
