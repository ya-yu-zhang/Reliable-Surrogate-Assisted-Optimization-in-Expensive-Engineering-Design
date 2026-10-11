"""Fixed pre-optimization grid verification; reject >5% relative 24/96 drift."""
import hashlib, importlib.metadata, json, platform
from pathlib import Path
import numpy as np
from .engineering_thermal_adapter import ThermalDesign
from .engineering_optimization_transfer import write_json
ROOT=Path(__file__).resolve().parents[1]

def main():
    target=ROOT/'paper/engineering_optimization/thermal_verification.json'
    if target.exists(): raise FileExistsError('Verification outputs already exist')
    designs={'uniform':np.full(12,.5),'ascending':np.linspace(0,1,12),
             'alternating':np.tile([0.,1.],6)}
    records=[]; attempts=0
    for condition in ['central_source','offset_source']:
        for name,x in designs.items():
            values=[]
            for n in [24,48,96]:
                attempts+=1
                value,checks=ThermalDesign(n,condition).solve(x)
                values.append(value)
                records.append({'condition':condition,'design':name,'mesh':n,
                                'objective':value,**checks})
                write_json(target,{'complete':False,'mesh_verification_attempts':attempts,
                                   'records':records,'stop_24_vs_96_relative_drift':.05})
            if abs(values[0]/values[2]-1)>.05:
                raise AssertionError('Prespecified grid drift exceeded 5%')
    report={'complete':True,'mesh_verification_attempts':attempts,
            'analytic_test_solver_attempts':4,'total_verification_solver_attempts':attempts+4,
            'optimization_calls_before_verification':0,'records':records,
            'stop_24_vs_96_relative_drift':.05,'python':platform.python_version(),
            'versions':{p:importlib.metadata.version(p) for p in ['numpy','scipy','scikit-learn']},
            'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in
                            ['configs/engineering_optimization_thermal.json',
                             'src/engineering_thermal_adapter.py',
                             'src/engineering_optimization_thermal.py',
                             'src/verify_engineering_thermal.py']}}
    write_json(target,report)
    print(json.dumps({'complete':True,'verification_solver_attempts':attempts+4}))
if __name__=='__main__': main()
