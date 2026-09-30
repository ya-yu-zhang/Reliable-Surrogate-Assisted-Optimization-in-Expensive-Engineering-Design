import numpy as np
import pandas as pd
from src.validate_mechanisms import summarize_components


def test_validation_takes_each_method_median_before_contrast():
    # Median of paired differences is zero; difference of medians is nine.
    rows=[dict(dim=10,fid=f,instance=i,rep=r,a=a,b=b)
          for f in [1,2] for i in [11,12]
          for r,(a,b) in enumerate(zip([0.,10.,11.],[0.,1.,20.]))]
    result,functions=summarize_components(pd.DataFrame(rows),['a','b'],np.array([1.,-1.]),10,repeats=16)
    assert result['estimate']==9
    assert functions.contrast.tolist()==[9.,9.]


def test_validation_zero_contrasts_have_defined_p_and_interval():
    rows=[dict(dim=20,fid=f,instance=11,rep=r,a=float(r),b=float(r))
          for f in [1,2] for r in range(3)]
    result,functions=summarize_components(pd.DataFrame(rows),['a','b'],np.array([1.,-1.]),20,repeats=16)
    assert result['p']==1 and result['estimate']==0
    assert result['ci_low']==result['ci_high']==0
