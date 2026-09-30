"""Verify exact author exports and installed runtime without objective labels."""
import ast
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform

ROOT = Path(__file__).resolve().parents[1]


def main():
    exports = {}
    for directory,commit in [('LassoBench-export','cb9702e87c07b83e4c175ab88155ad8272edea0c'),
                             ('sparse-ho-export','a97929dff3b7a40211c224f9cc53328ebf545a82')]:
        root = ROOT/'literature/source-code'/directory
        record = json.loads((root/'SOURCE.json').read_text('utf-8'))
        assert record['commit'] == commit and record['partial_export']
        assert any('license' in name.lower() for name in record['files_sha256'])
        for name,digest in record['files_sha256'].items():
            assert hashlib.sha256((root/name).read_bytes()).hexdigest() == digest
        exports[directory] = record
    import LassoBench
    import sparse_ho
    installed = {'LassoBench':Path(LassoBench.__file__).parent,'sparse_ho':Path(sparse_ho.__file__).parent}
    runtime_verified = []
    for directory,record in exports.items():
        for name,digest in record['files_sha256'].items():
            path = Path(name)
            if path.suffix != '.py' or path.parts[0] not in installed or 'tests' in path.parts:
                continue
            file = installed[path.parts[0]].joinpath(*path.parts[1:])
            assert file.exists() and hashlib.sha256(file.read_bytes()).hexdigest() == digest
            runtime_verified.append(name)
    file = ROOT/'literature/source-code/LassoBench-export/LassoBench/LassoBench.py'
    tree = ast.parse(file.read_text('utf-8'))
    targets = {}; heldout_in_constructor = {}
    for cls in [node for node in tree.body if isinstance(node,ast.ClassDef)]:
        if cls.name not in ['SyntheticBenchmark','RealBenchmark']: continue
        evaluate = next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='evaluate')
        attributes = sorted({n.attr for n in ast.walk(evaluate) if isinstance(n,ast.Attribute)})
        assert 'X_test' not in attributes and 'y_test' not in attributes and 'mspe_oracle' not in attributes
        assert 'X_train' in attributes and 'y_train' in attributes
        targets[cls.name] = dict(evaluate_reads_test_labels=False,attributes=attributes,
                                divides_by_training_oracle='loss_oracle' in attributes)
        constructor = next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='__init__')
        calls = [n for n in ast.walk(constructor) if isinstance(n,ast.Call)
                 and isinstance(n.func,ast.Name) and n.func.id=='mean_squared_error']
        heldout_in_constructor[cls.name] = any(isinstance(n,ast.Attribute) and n.attr=='y_test'
                                                for call in calls for n in ast.walk(call))
    assert heldout_in_constructor == {'SyntheticBenchmark':True,'RealBenchmark':False}
    packages = {p:importlib.metadata.version(p) for p in
        ['numpy','scipy','scikit-learn','celer','numba','libsvmdata','hyperopt','sparse-ho','LassoBench']}
    report = dict(python=platform.python_version(),source_exports=exports,packages=packages,
        installed_author_modules_verified=runtime_verified,target_audit=targets,
        constructor_precomputes_fixed_test_normalizer=heldout_in_constructor,
        optimization_objective_calls=0,test_method_calls=0,
        no_global_optimum_supplied=True,formal_application_labels_not_generated=True)
    out = ROOT/'results/application_source_audit';out.mkdir(parents=True,exist_ok=True)
    (out/'audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['python','packages','optimization_objective_calls',
        'test_method_calls','constructor_precomputes_fixed_test_normalizer']},indent=2))


if __name__ == '__main__':
    main()
