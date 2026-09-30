"""Run one frozen Settings perturbation through the unchanged experiment loop."""
import argparse,hashlib,json
from dataclasses import asdict
from pathlib import Path
from .core import Settings
from . import experiment

ROOT=Path(__file__).resolve().parents[1];CONFIG='configs/model_sensitivity.json'


def main():
    p=argparse.ArgumentParser();p.add_argument('--variant',required=True);p.add_argument('--fid',type=int,required=True)
    p.add_argument('--dim',type=int,required=True);p.add_argument('--instance',type=int,required=True);p.add_argument('--rep',type=int,required=True)
    a=p.parse_args();config=json.loads((ROOT/CONFIG).read_text('utf-8'))
    frozen=json.loads((ROOT/config['freeze_manifest']).read_text('utf-8'))
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==v for n,v in frozen.items())
    assert a.variant in config['variants'] and a.fid in config['functions'] and a.dim in config['dimensions']
    assert a.instance in config['instances'] and 0<=a.rep<config['repeats']
    values=config['variants'][a.variant];settings=Settings(kernel_scale=values['kernel_scale'],max_train=values['max_train'])
    assert settings.elite_train<=settings.max_train
    original=experiment.Settings;experiment.Settings=lambda:settings
    try:
        summary=experiment.run_one((a.fid,a.dim,a.instance,a.rep,config['method'],10*a.dim,
            str(ROOT/config['out']/a.variant),config['capture']))
    finally:experiment.Settings=original
    assert summary['signature']['settings']==asdict(settings) and summary['algorithm_evaluations']==10*a.dim
    print(json.dumps(dict(runid=summary['runid'],variant=a.variant,evaluations=summary['algorithm_evaluations'])))


if __name__=='__main__':main()
