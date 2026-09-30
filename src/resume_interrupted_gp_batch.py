"""Original frozen scheduler; route only archived partial runs through verified replay."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch

from . import run_gp_batch as original
from .run_solo_cost import process_inventory

ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=ROOT/'results/interruption_20260918_v1'


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',required=True);args=ap.parse_args()
    manifest=json.loads((ARCHIVE/'recovery_manifest.json').read_text('utf-8'))
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest for name,digest in manifest['recovery_sources'].items())
    config=json.loads((ROOT/args.config).read_text('utf-8'));out=ROOT/config['out']
    status=json.loads((out/'status.json').read_text('utf-8'))
    assert not any(p['ProcessId']==status['pid'] and any(name in (p['CommandLine'] or '')
        for name in ['src.run_gp_batch','src.resume_interrupted_gp_batch']) for p in process_inventory()), 'Batch already live'
    eligible={row['runid']:row for row in manifest['partial_runs'] if row['source']==Path(config['out']).name}
    saved_run=original.subprocess.run
    def route(command,*a,**kw):
        if len(command)>3 and command[1:3]==['-m','src.gp_references']:
            values=dict(zip(command[3::2],command[4::2]))
            dim=int(values['--dim']);method=values['--method'];fid=int(values['--fid'])
            instance=int(values['--instance']);rep=int(values['--rep']);budget=10*dim
            runid=f'{method}_f{fid:02}_d{dim}_i{instance}_r{rep}_b{budget}'
            if runid in eligible and not (out/runid/'summary.json').exists():
                command=list(command);command[2]='src.recover_interrupted_run'
                command+=['--archive',str(ROOT/eligible[runid]['archive']),'--kind','gp']
        return saved_run(command,*a,**kw)
    (out/'recovery_driver.json').write_text(json.dumps(dict(driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        original_scheduler_sha256=hashlib.sha256((ROOT/'src/run_gp_batch.py').read_bytes()).hexdigest(),
        interruption_archive=ARCHIVE.relative_to(ROOT).as_posix(),replayed_runids=sorted(eligible),
        optimization_parameters_unchanged=True),indent=2),encoding='utf-8')
    sys.argv=[sys.argv[0],'--config',str(ROOT/args.config)]
    with patch.object(original.subprocess,'run',route):original.main()


if __name__=='__main__':main()
