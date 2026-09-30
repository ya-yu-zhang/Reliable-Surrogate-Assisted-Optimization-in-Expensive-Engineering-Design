from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.report_all_references import combine_runs


def complete_fixture():
    # This fixture uses complete internal observations, never partial live GP data.
    root=Path(__file__).resolve().parents[1]
    internal=pd.read_csv(root/'results/mechanism_validation_analysis_v1/runs.csv')
    assert 'algorithm_evaluations' not in internal.columns
    base=internal[internal.method=='fixed01'][['dim','fid','instance','rep','error']]
    # Artificial equal-error competitors test arithmetic only, not performance.
    parts=[]
    for method in ['sobol','cma_es','gp_ei','turbo_1']:
        frame=base.copy();frame['method']=method;frame['algorithm_evaluations']=10*frame.dim;parts.append(frame)
    return internal,pd.concat(parts,ignore_index=True)


def test_full_combination_counts_internal_budget_and_normalizes_before_medians():
    internal,external=complete_fixture();original=internal.copy(deep=True)
    combined=combine_runs(internal,external)
    assert combined.algorithm_evaluations.sum()==1512000
    assert combined[combined.method.isin(internal.method)].algorithm_evaluations.sum()==907200
    assert combined[combined.method=='turbo_1'].algorithm_evaluations.sum()==151200
    keys=['dim','fid','instance','rep']
    fixed=combined[combined.method=='fixed01'].set_index(keys).sort_index()
    for method in ['sobol','cma_es','gp_ei','turbo_1']:
        contender=combined[combined.method==method].set_index(keys).sort_index()
        np.testing.assert_allclose(contender.log_relative_error,fixed.log_relative_error,rtol=0,atol=1e-12)
    pd.testing.assert_frame_equal(internal,original)


def test_wrong_external_budget_rejected_before_report():
    internal,external=complete_fixture();external.loc[0,'algorithm_evaluations']+=1
    with pytest.raises(AssertionError):combine_runs(internal,external)
