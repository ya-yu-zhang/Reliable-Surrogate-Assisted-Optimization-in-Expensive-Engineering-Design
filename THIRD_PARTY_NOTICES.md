# Third-party materials

## Final numerical code/data profile

The selected profile contains original project Python code and research records. It installs its numerical dependencies separately and does not bundle their implementations or library binaries.

| Dependency | Recorded version | Upstream license information |
|---|---|---|
| NumPy | 2.3.5 | https://github.com/numpy/numpy/blob/main/LICENSE.txt |
| SciPy | 1.17.0 | https://github.com/scipy/scipy/blob/main/LICENSE.txt |
| scikit-learn | 1.8.0 | https://github.com/scikit-learn/scikit-learn/blob/main/COPYING |
| CFFI | 2.1.1 | https://cffi.readthedocs.io/en/stable/overview.html |
| threadpoolctl | 3.6.0 | https://github.com/joblib/threadpoolctl/blob/master/LICENSE |
| MPFR | 4.2.1, external 64-bit shared library | https://www.mpfr.org/mpfr-4.2.1/ |

The upstream package distributions govern their own included dependencies and notices. MPFR is dynamically loaded through CFFI; no MPFR or GMP source or binary is redistributed in this profile. Its source, copying conditions and installation remain available upstream. The implementation's MPFR declarations and Python wrappers are project code.

## Historical engineering and optimization studies

Historical adapters refer to author implementations and installed packages such as TuRBO, DRSO, LassoBench, EngiBench, COCO/IOH, pycma and CVXOPT. Their source versions and execution settings remain in the historical protocols and manuscript evidence. External author source trees, datasets and environments are excluded from the selected numerical profile. Installing or redistributing those materials requires following their own terms; the selected MIT grant does not apply to them.

Publisher class/style assets, downloaded articles, rendered manuscripts and figure render caches are also excluded from the selected profile. Historical copies in the private repository are not part of this software license grant.
