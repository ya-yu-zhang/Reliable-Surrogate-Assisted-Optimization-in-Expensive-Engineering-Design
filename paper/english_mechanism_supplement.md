---
title: "Supplement: Independent Mechanism Validation"
date: "17 September 2026"
---

# S1 Scope, aggregation, and audit

This supplement accompanies the English mechanism working manuscript. All printed numbers derive from the completed independent validation; development data are not pooled into its tests. The full design comprises 24 BBOB functions, dimensions 10/20/40, instances 11/12/13, three repeats, six methods, and budget 10D: 3,888 runs, 907,200 paid algorithm calls. Independent diagnostics comprise 7,776 states and 1,990,656 additional labels, never supplied to optimizers. Failed runs and exact duplicate calls are zero.

Endpoint and contrast tables use the frozen hierarchy: three-repeat median within instance, three-instance average within function, then equal function weights for suite summaries. Contrasts are constructed at their prespecified component level. Raw-error IQR tables instead describe all nine paid runs for a function and method; they are not the estimators used for primary hypothesis tests.

Only the nine prespecified comparisons form the primary Holm family. Tables here provide complete function-level inputs and descriptive secondary outputs; they add no tests. The observed training truncation count is 185,328 fits. Source, pre-information, original residual, candidate-selection, and diagnostic-index audits passed. Real-arithmetic ordering equivalence is separate from arbitrary floating-point tie behavior.

The original optimization-improvement gate remains failed. New instances support mechanism and failure analysis. Neither this supplement nor the manuscript claims a pointwise coverage theorem, FDP/FDR control, evaluation savings, or application acceleration. Live GP-EI/TuRBO batches and unexecuted exclusive-cost measurements are absent from these tables.

All raw runs, predicted-before-label journals, candidate pools, hidden diagnostic labels, four checkpoint state tables, dependency locks, seeds, and failure logs are available in the project. Seed = 100000D + 1000f + 10i + r, with r=0,1,2. Initialization, candidates, and management use distinct random streams. Sharing this seed alone is not a claim of identical downstream histories.

\newpage

# S2.10 Full function endpoint scores, D=10

Lower is better. Scores are log10(max(final error / common initial error, 1e-12)), with the frozen within-instance median and across-instance average. Random means the paid random candidate policy, not independent-domain Sobol.

| Function | Greedy | Fixed .1 | Fixed .3 | Random | PEM-T | PEM-ST |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | -1.9834 | -1.7330 | -1.5064 | -0.1841 | -1.5907 | -1.5998 |
| 2 | -0.5809 | -0.7906 | -0.7593 | -0.0856 | -0.5229 | -0.5481 |
| 3 | -0.3652 | -0.3124 | -0.2679 | -0.0609 | -0.2810 | -0.2941 |
| 4 | -0.1263 | -0.0789 | -0.1170 | -0.0359 | -0.0504 | -0.0143 |
| 5 | -0.8662 | -0.8101 | -0.7117 | -0.0652 | -0.7618 | -0.7374 |
| 6 | -3.1709 | -3.1172 | -3.0736 | -0.3935 | -2.8907 | -3.0354 |
| 7 | -1.0807 | -1.0923 | -1.0271 | -0.2608 | -0.9152 | -0.9152 |
| 8 | -1.7713 | -1.8968 | -1.6115 | -0.3213 | -1.4271 | -1.5771 |
| 9 | -1.3192 | -1.2243 | -1.2079 | -0.0788 | -1.0173 | -1.0684 |
| 10 | -0.9057 | -0.7745 | -0.7705 | -0.2539 | -0.7886 | -0.7921 |
| 11 | -0.8648 | -1.2172 | -0.6966 | -0.7170 | -0.6618 | -0.7868 |
| 12 | -0.5551 | -0.4166 | -0.3526 | -0.0371 | -0.1603 | -0.1835 |
| 13 | -0.8567 | -0.6796 | -0.6189 | -0.0824 | -0.5792 | -0.6537 |
| 14 | -0.7637 | -0.7258 | -0.5251 | -0.1895 | -0.4739 | -0.4739 |
| 15 | -0.5217 | -0.5104 | -0.3960 | -0.1514 | -0.3795 | -0.3632 |
| 16 | -0.0299 | -0.0520 | -0.0436 | -0.0639 | -0.0216 | -0.0108 |
| 17 | -0.3329 | -0.3021 | -0.2586 | -0.1783 | -0.2201 | -0.2534 |
| 18 | -0.4174 | -0.2357 | -0.2848 | -0.0877 | -0.2106 | -0.2106 |
| 19 | -0.3659 | -0.3849 | -0.3056 | -0.1483 | -0.2792 | -0.2826 |
| 20 | -3.4967 | -3.3994 | -3.1207 | -0.4768 | -3.3170 | -3.4424 |
| 21 | -0.8677 | -0.6352 | -0.5508 | -0.0107 | -0.1617 | -0.1242 |
| 22 | -0.4136 | -0.4118 | -0.2858 | -0.0027 | -0.1287 | -0.2206 |
| 23 | 0.0000 | -0.0887 | 0.0000 | -0.0102 | -0.0450 | -0.0450 |
| 24 | -0.3083 | -0.2868 | -0.2970 | -0.1427 | -0.2901 | -0.2840 |

\newpage

# S2.20 Full function endpoint scores, D=20

Lower is better. Scores are log10(max(final error / common initial error, 1e-12)), with the frozen within-instance median and across-instance average. Random means the paid random candidate policy, not independent-domain Sobol.

| Function | Greedy | Fixed .1 | Fixed .3 | Random | PEM-T | PEM-ST |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | -1.6820 | -1.6604 | -1.4000 | -0.2050 | -1.3338 | -1.4436 |
| 2 | -1.0234 | -0.9404 | -0.9793 | -0.3234 | -0.8794 | -0.9600 |
| 3 | -0.4893 | -0.4672 | -0.4691 | -0.1596 | -0.4593 | -0.4985 |
| 4 | -0.2492 | -0.2330 | -0.2305 | -0.1605 | -0.2004 | -0.1837 |
| 5 | -0.9105 | -0.8274 | -0.6863 | -0.1245 | -0.7928 | -0.7450 |
| 6 | -3.3391 | -3.4096 | -2.7282 | -0.3286 | -3.1255 | -3.1124 |
| 7 | -0.8569 | -0.9348 | -0.8613 | -0.2253 | -0.8318 | -0.8752 |
| 8 | -1.6783 | -1.6372 | -1.5885 | -0.2687 | -1.6901 | -1.7226 |
| 9 | -1.3875 | -1.3276 | -1.2672 | -0.4295 | -1.2298 | -1.3932 |
| 10 | -0.9261 | -0.8323 | -0.5536 | -0.1740 | -0.5420 | -0.6041 |
| 11 | -1.4417 | -1.5274 | -1.3294 | -1.0957 | -1.1293 | -1.1492 |
| 12 | -0.3436 | -0.3167 | -0.2405 | -0.3195 | -0.3442 | -0.3442 |
| 13 | -0.7274 | -0.6725 | -0.6150 | -0.0814 | -0.7002 | -0.6307 |
| 14 | -0.6917 | -0.6200 | -0.5653 | -0.1573 | -0.6970 | -0.6865 |
| 15 | -0.5765 | -0.5012 | -0.5491 | -0.2020 | -0.4970 | -0.5595 |
| 16 | -0.0482 | -0.0863 | -0.0652 | -0.0889 | -0.0937 | -0.1138 |
| 17 | -0.5015 | -0.4647 | -0.3443 | -0.1048 | -0.3243 | -0.3304 |
| 18 | -0.4201 | -0.3763 | -0.3129 | -0.1285 | -0.3073 | -0.3259 |
| 19 | -0.4221 | -0.4355 | -0.4064 | -0.1518 | -0.3917 | -0.4100 |
| 20 | -2.2002 | -2.2540 | -1.8271 | -0.3838 | -2.1324 | -2.0332 |
| 21 | -0.7052 | -0.6441 | -0.7432 | -0.0358 | -0.3390 | -0.2657 |
| 22 | -0.6147 | -0.4840 | -0.4384 | -0.0143 | -0.2533 | -0.2130 |
| 23 | -0.0822 | -0.0497 | -0.0068 | -0.0486 | -0.0439 | -0.0132 |
| 24 | -0.3157 | -0.3236 | -0.2968 | -0.1235 | -0.2926 | -0.2909 |

\newpage

# S2.40 Full function endpoint scores, D=40

Lower is better. Scores are log10(max(final error / common initial error, 1e-12)), with the frozen within-instance median and across-instance average. Random means the paid random candidate policy, not independent-domain Sobol.

| Function | Greedy | Fixed .1 | Fixed .3 | Random | PEM-T | PEM-ST |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | -1.2112 | -1.2326 | -1.0894 | -0.2584 | -1.1720 | -1.1741 |
| 2 | -1.2054 | -1.0937 | -0.9946 | -0.4467 | -0.9065 | -0.7905 |
| 3 | -0.5155 | -0.5833 | -0.4918 | -0.1928 | -0.5266 | -0.5230 |
| 4 | -0.2900 | -0.2612 | -0.2655 | -0.1742 | -0.2393 | -0.2376 |
| 5 | -0.7832 | -0.7302 | -0.6422 | -0.1613 | -0.7388 | -0.6742 |
| 6 | -2.6753 | -2.8177 | -2.4509 | -0.3562 | -2.3885 | -2.2635 |
| 7 | -0.9055 | -0.9318 | -0.8804 | -0.1851 | -0.8669 | -0.9004 |
| 8 | -1.7307 | -1.7844 | -1.6654 | -0.5741 | -1.6092 | -1.6275 |
| 9 | -1.2941 | -1.2041 | -1.1497 | -0.5013 | -1.1577 | -1.0611 |
| 10 | -1.2909 | -1.1676 | -1.0811 | -0.2766 | -1.1969 | -1.2051 |
| 11 | -0.7728 | -0.7548 | -0.7077 | -0.8592 | -0.6661 | -0.4877 |
| 12 | -0.5093 | -0.4568 | -0.3637 | -0.3497 | -0.3492 | -0.3565 |
| 13 | -0.5333 | -0.5347 | -0.5095 | -0.1336 | -0.5020 | -0.5148 |
| 14 | -0.7277 | -0.7359 | -0.6712 | -0.2766 | -0.6802 | -0.6559 |
| 15 | -0.4987 | -0.5070 | -0.4711 | -0.2374 | -0.4218 | -0.4495 |
| 16 | -0.0602 | -0.0521 | -0.0575 | -0.0487 | -0.0365 | -0.0773 |
| 17 | -0.4202 | -0.4425 | -0.4090 | -0.1568 | -0.3537 | -0.3751 |
| 18 | -0.5101 | -0.4587 | -0.4364 | -0.2007 | -0.4808 | -0.4443 |
| 19 | -0.4884 | -0.4515 | -0.4362 | -0.2502 | -0.4420 | -0.4647 |
| 20 | -1.9465 | -1.7348 | -1.3354 | -0.3918 | -1.8456 | -1.7511 |
| 21 | -0.5208 | -0.3612 | -0.3872 | -0.0293 | -0.3693 | -0.3633 |
| 22 | -0.3394 | -0.3528 | -0.2130 | -0.0249 | -0.2416 | -0.1843 |
| 23 | -0.0553 | -0.0875 | -0.0420 | -0.0349 | -0.0695 | -0.0559 |
| 24 | -0.2943 | -0.3057 | -0.2818 | -0.1737 | -0.2483 | -0.2605 |

\newpage

# S3.10 Full primary contrast inputs, D=10

The three columns have different units. Positive endpoint difference means worse PEM-T; positive gain difference favors feedback. History interaction is a difference of selected-minus-pool failure gaps between fixed .3 and greedy histories and has no inherent favorable sign. It is not a same-pool causal effect.

| Function | History interaction | Endpoint T - .1 | Gain feedback - mean |
| --- | --- | --- | --- |
| 1 | 0.1553 | 0.1423 | -0.0682 |
| 2 | 0.2360 | 0.2677 | 0.0000 |
| 3 | 0.1387 | 0.0314 | -0.0104 |
| 4 | 0.1348 | 0.0285 | 0.0000 |
| 5 | 0.0889 | 0.0483 | -0.0471 |
| 6 | 0.1833 | 0.2266 | -0.0123 |
| 7 | 0.1742 | 0.1770 | -0.0192 |
| 8 | 0.0944 | 0.4696 | -0.0159 |
| 9 | 0.1911 | 0.2070 | -0.0039 |
| 10 | 0.0586 | -0.0141 | 1.138e-21 |
| 11 | 0.0309 | 0.5554 | 0.0000 |
| 12 | 0.0973 | 0.2564 | -0.0002 |
| 13 | 0.0404 | 0.1005 | -0.0540 |
| 14 | 0.0430 | 0.2519 | -0.0067 |
| 15 | 0.0615 | 0.1309 | -0.0207 |
| 16 | -0.0999 | 0.0304 | 0.0000 |
| 17 | 0.1449 | 0.0820 | -1.210e-05 |
| 18 | 0.1891 | 0.0251 | -0.0061 |
| 19 | 0.1432 | 0.1057 | -0.0086 |
| 20 | 0.0150 | 0.0824 | -0.0190 |
| 21 | -0.0042 | 0.4735 | -0.0138 |
| 22 | 0.0804 | 0.2831 | -0.0592 |
| 23 | -0.0931 | 0.0437 | 0.0000 |
| 24 | -0.0609 | -0.0033 | -0.0433 |

\newpage

# S3.20 Full primary contrast inputs, D=20

The three columns have different units. Positive endpoint difference means worse PEM-T; positive gain difference favors feedback. History interaction is a difference of selected-minus-pool failure gaps between fixed .3 and greedy histories and has no inherent favorable sign. It is not a same-pool causal effect.

| Function | History interaction | Endpoint T - .1 | Gain feedback - mean |
| --- | --- | --- | --- |
| 1 | 0.3343 | 0.3266 | -0.0261 |
| 2 | 0.2367 | 0.0611 | -0.0001 |
| 3 | 0.1042 | 0.0079 | -0.0197 |
| 4 | 0.1204 | 0.0325 | -0.0003 |
| 5 | 0.2581 | 0.0346 | -0.0966 |
| 6 | 0.2796 | 0.2841 | -0.0075 |
| 7 | 0.0749 | 0.1030 | -0.0011 |
| 8 | 0.1976 | -0.0529 | -0.0393 |
| 9 | 0.1540 | 0.0978 | -0.0025 |
| 10 | 0.1257 | 0.2903 | -0.0001 |
| 11 | 0.0671 | 0.3980 | 0.0000 |
| 12 | 0.1185 | -0.0275 | -0.0001 |
| 13 | 0.2008 | -0.0276 | -0.0522 |
| 14 | 0.1862 | -0.0770 | -0.0028 |
| 15 | 0.2533 | 0.0042 | -0.0237 |
| 16 | -0.2565 | -0.0074 | 0.0000 |
| 17 | 0.0612 | 0.1404 | -0.0046 |
| 18 | 0.0622 | 0.0690 | -2.086e-05 |
| 19 | -0.0306 | 0.0438 | -0.0022 |
| 20 | 0.2018 | 0.1216 | -0.0250 |
| 21 | 0.0824 | 0.3052 | -0.0327 |
| 22 | 0.0068 | 0.2308 | -0.0041 |
| 23 | -0.0029 | 0.0058 | 0.0000 |
| 24 | 0.1055 | 0.0310 | -0.0389 |

\newpage

# S3.40 Full primary contrast inputs, D=40

The three columns have different units. Positive endpoint difference means worse PEM-T; positive gain difference favors feedback. History interaction is a difference of selected-minus-pool failure gaps between fixed .3 and greedy histories and has no inherent favorable sign. It is not a same-pool causal effect.

| Function | History interaction | Endpoint T - .1 | Gain feedback - mean |
| --- | --- | --- | --- |
| 1 | 0.3343 | 0.0606 | -0.1179 |
| 2 | 0.2135 | 0.1873 | -0.0003 |
| 3 | 0.1784 | 0.0567 | -0.0233 |
| 4 | 0.1641 | 0.0220 | -0.0114 |
| 5 | 0.3662 | -0.0086 | -0.1300 |
| 6 | 0.3424 | 0.4292 | -0.0245 |
| 7 | 0.2699 | 0.0649 | -0.0050 |
| 8 | 0.2344 | 0.1752 | -0.0547 |
| 9 | 0.2292 | 0.0464 | -0.0051 |
| 10 | 0.1602 | -0.0293 | -0.0038 |
| 11 | 0.0671 | 0.0887 | 0.0000 |
| 12 | 0.1055 | 0.1076 | 1.481e-20 |
| 13 | 0.4954 | 0.0327 | -0.0553 |
| 14 | 0.1465 | 0.0557 | -0.0105 |
| 15 | -0.0202 | 0.0852 | -0.0031 |
| 16 | -0.0876 | 0.0156 | 0.0000 |
| 17 | -0.0944 | 0.0887 | -0.0014 |
| 18 | -0.0352 | -0.0222 | -0.0030 |
| 19 | -0.0501 | 0.0095 | -0.0028 |
| 20 | 0.2751 | -0.1108 | -0.0132 |
| 21 | 0.2386 | -0.0081 | -0.0375 |
| 22 | -0.0635 | 0.1112 | -0.3186 |
| 23 | -0.0023 | 0.0180 | 0.0000 |
| 24 | 0.0107 | 0.0573 | -0.0052 |

\newpage

# S4.10 Raw paid-run error dispersion, D=10

Absolute final error above the known optimum; all nine runs per function and method. This raw dispersion uses a different aggregation from the primary contrasts. Complete six-method IQR values are retained in internal_raw_error_iqr.csv. Scientific notation avoids rounding nonzero errors to zero.

| Function | Fixed .1 median [Q25, Q75] | PEM-T median [Q25, Q75] |
| --- | --- | --- |
| 1 | 7.098e-01 [5.755e-01, 1.250e+00] | 9.146e-01 [7.384e-01, 1.464e+00] |
| 2 | 1.112e+05 [5.615e+04, 1.477e+05] | 1.797e+05 [1.458e+05, 2.010e+05] |
| 3 | 1.149e+02 [1.017e+02, 1.232e+02] | 1.210e+02 [1.141e+02, 1.345e+02] |
| 4 | 2.462e+02 [2.343e+02, 3.088e+02] | 2.462e+02 [2.343e+02, 3.267e+02] |
| 5 | 2.038e+01 [1.222e+01, 2.565e+01] | 2.156e+01 [1.495e+01, 3.202e+01] |
| 6 | 7.880e+01 [5.704e+01, 1.003e+02] | 1.227e+02 [6.997e+01, 1.548e+02] |
| 7 | 2.311e+01 [1.294e+01, 2.999e+01] | 3.419e+01 [2.598e+01, 3.857e+01] |
| 8 | 2.655e+02 [2.251e+02, 5.498e+02] | 6.560e+02 [4.140e+02, 9.133e+02] |
| 9 | 6.746e+02 [5.013e+02, 9.464e+02] | 1.501e+03 [8.256e+02, 1.912e+03] |
| 10 | 9.126e+04 [5.554e+04, 1.088e+05] | 1.358e+05 [6.925e+04, 1.694e+05] |
| 11 | 2.879e+02 [1.898e+02, 3.564e+02] | 4.030e+02 [2.734e+02, 5.538e+02] |
| 12 | 2.325e+07 [1.420e+07, 3.436e+07] | 3.963e+07 [3.111e+07, 5.058e+07] |
| 13 | 2.351e+02 [2.226e+02, 2.452e+02] | 2.968e+02 [2.440e+02, 3.226e+02] |
| 14 | 4.106e+00 [3.111e+00, 5.044e+00] | 5.445e+00 [5.008e+00, 7.365e+00] |
| 15 | 1.003e+02 [9.082e+01, 1.098e+02] | 1.468e+02 [1.052e+02, 1.544e+02] |
| 16 | 2.755e+01 [2.067e+01, 2.881e+01] | 2.491e+01 [2.067e+01, 2.758e+01] |
| 17 | 6.351e+00 [3.317e+00, 7.877e+00] | 7.694e+00 [6.882e+00, 8.380e+00] |
| 18 | 2.479e+01 [1.668e+01, 2.841e+01] | 3.277e+01 [2.289e+01, 3.755e+01] |
| 19 | 6.382e+00 [6.016e+00, 7.571e+00] | 8.043e+00 [7.297e+00, 9.105e+00] |
| 20 | 3.454e+00 [3.395e+00, 3.622e+00] | 4.693e+00 [4.126e+00, 5.385e+00] |
| 21 | 1.573e+01 [7.002e+00, 2.255e+01] | 4.058e+01 [2.591e+01, 5.281e+01] |
| 22 | 2.384e+01 [1.691e+01, 2.610e+01] | 5.497e+01 [3.971e+01, 5.729e+01] |
| 23 | 3.310e+00 [2.947e+00, 3.583e+00] | 3.319e+00 [3.282e+00, 3.977e+00] |
| 24 | 1.034e+02 [9.785e+01, 1.089e+02] | 1.021e+02 [9.125e+01, 1.105e+02] |

\newpage

# S4.20 Raw paid-run error dispersion, D=20

Absolute final error above the known optimum; all nine runs per function and method. This raw dispersion uses a different aggregation from the primary contrasts. Complete six-method IQR values are retained in internal_raw_error_iqr.csv. Scientific notation avoids rounding nonzero errors to zero.

| Function | Fixed .1 median [Q25, Q75] | PEM-T median [Q25, Q75] |
| --- | --- | --- |
| 1 | 2.537e+00 [1.906e+00, 3.956e+00] | 6.305e+00 [4.882e+00, 7.206e+00] |
| 2 | 2.572e+05 [1.961e+05, 3.275e+05] | 4.485e+05 [2.546e+05, 5.864e+05] |
| 3 | 2.699e+02 [2.426e+02, 2.893e+02] | 2.470e+02 [2.370e+02, 3.145e+02] |
| 4 | 5.702e+02 [4.867e+02, 6.545e+02] | 6.376e+02 [5.447e+02, 7.997e+02] |
| 5 | 4.099e+01 [3.097e+01, 4.249e+01] | 4.368e+01 [3.758e+01, 4.803e+01] |
| 6 | 2.288e+02 [1.159e+02, 3.182e+02] | 3.973e+02 [2.188e+02, 6.247e+02] |
| 7 | 6.424e+01 [5.375e+01, 7.998e+01] | 9.765e+01 [7.775e+01, 1.027e+02] |
| 8 | 2.742e+03 [2.085e+03, 3.945e+03] | 2.325e+03 [1.569e+03, 3.050e+03] |
| 9 | 5.078e+03 [3.099e+03, 6.643e+03] | 6.938e+03 [5.268e+03, 9.142e+03] |
| 10 | 2.249e+05 [1.786e+05, 3.121e+05] | 3.586e+05 [2.308e+05, 5.034e+05] |
| 11 | 2.460e+02 [1.940e+02, 2.779e+02] | 3.399e+02 [3.020e+02, 5.969e+02] |
| 12 | 1.096e+08 [8.093e+07, 1.257e+08] | 1.096e+08 [9.474e+07, 1.170e+08] |
| 13 | 4.866e+02 [3.865e+02, 5.354e+02] | 4.477e+02 [3.401e+02, 5.496e+02] |
| 14 | 1.110e+01 [8.602e+00, 1.176e+01] | 8.549e+00 [6.434e+00, 1.188e+01] |
| 15 | 2.336e+02 [2.304e+02, 2.792e+02] | 2.454e+02 [2.243e+02, 2.648e+02] |
| 16 | 3.319e+01 [2.949e+01, 3.672e+01] | 3.319e+01 [2.949e+01, 3.506e+01] |
| 17 | 5.684e+00 [4.583e+00, 6.415e+00] | 7.839e+00 [6.766e+00, 8.267e+00] |
| 18 | 2.276e+01 [2.112e+01, 2.581e+01] | 2.687e+01 [2.586e+01, 3.085e+01] |
| 19 | 8.017e+00 [7.778e+00, 8.212e+00] | 8.999e+00 [8.736e+00, 9.557e+00] |
| 20 | 9.235e+01 [3.511e+01, 6.165e+02] | 3.906e+02 [2.724e+02, 5.468e+02] |
| 21 | 2.152e+01 [9.198e+00, 2.518e+01] | 3.644e+01 [1.794e+01, 4.776e+01] |
| 22 | 2.497e+01 [1.643e+01, 4.765e+01] | 3.554e+01 [2.832e+01, 5.830e+01] |
| 23 | 4.972e+00 [4.189e+00, 5.302e+00] | 4.979e+00 [4.725e+00, 5.059e+00] |
| 24 | 2.550e+02 [2.465e+02, 2.654e+02] | 2.732e+02 [2.308e+02, 2.785e+02] |

\newpage

# S4.40 Raw paid-run error dispersion, D=40

Absolute final error above the known optimum; all nine runs per function and method. This raw dispersion uses a different aggregation from the primary contrasts. Complete six-method IQR values are retained in internal_raw_error_iqr.csv. Scientific notation avoids rounding nonzero errors to zero.

| Function | Fixed .1 median [Q25, Q75] | PEM-T median [Q25, Q75] |
| --- | --- | --- |
| 1 | 1.888e+01 [1.427e+01, 2.437e+01] | 2.221e+01 [1.893e+01, 2.864e+01] |
| 2 | 7.676e+05 [5.266e+05, 9.763e+05] | 1.474e+06 [6.705e+05, 1.600e+06] |
| 3 | 5.262e+02 [5.158e+02, 5.512e+02] | 6.134e+02 [5.424e+02, 6.284e+02] |
| 4 | 1.325e+03 [1.255e+03, 1.468e+03] | 1.449e+03 [1.407e+03, 1.506e+03] |
| 5 | 1.033e+02 [8.277e+01, 1.321e+02] | 1.013e+02 [9.825e+01, 1.325e+02] |
| 6 | 1.039e+03 [6.585e+02, 1.642e+03] | 1.056e+03 [5.835e+02, 7.238e+03] |
| 7 | 2.433e+02 [2.212e+02, 2.664e+02] | 2.178e+02 [1.978e+02, 2.818e+02] |
| 8 | 8.581e+03 [7.757e+03, 9.110e+03] | 1.202e+04 [1.021e+04, 1.397e+04] |
| 9 | 1.892e+04 [1.409e+04, 2.013e+04] | 2.183e+04 [1.771e+04, 2.871e+04] |
| 10 | 6.175e+05 [5.401e+05, 6.291e+05] | 5.935e+05 [5.230e+05, 7.774e+05] |
| 11 | 5.342e+02 [5.074e+02, 6.715e+02] | 6.025e+02 [5.541e+02, 1.022e+03] |
| 12 | 2.898e+08 [2.267e+08, 3.284e+08] | 3.198e+08 [3.011e+08, 3.498e+08] |
| 13 | 9.915e+02 [9.375e+02, 1.068e+03] | 1.050e+03 [9.868e+02, 1.085e+03] |
| 14 | 1.807e+01 [1.554e+01, 1.842e+01] | 1.853e+01 [1.571e+01, 2.293e+01] |
| 15 | 6.570e+02 [6.081e+02, 6.905e+02] | 6.686e+02 [6.467e+02, 9.689e+02] |
| 16 | 4.407e+01 [4.122e+01, 4.538e+01] | 4.469e+01 [4.246e+01, 4.539e+01] |
| 17 | 7.482e+00 [7.120e+00, 8.101e+00] | 8.704e+00 [7.807e+00, 9.926e+00] |
| 18 | 2.993e+01 [2.376e+01, 3.394e+01] | 2.803e+01 [2.590e+01, 3.284e+01] |
| 19 | 1.019e+01 [9.952e+00, 1.032e+01] | 1.015e+01 [1.002e+01, 1.071e+01] |
| 20 | 2.523e+03 [1.174e+03, 4.019e+03] | 1.884e+03 [1.146e+03, 3.832e+03] |
| 21 | 3.918e+01 [2.767e+01, 5.223e+01] | 3.481e+01 [2.919e+01, 5.203e+01] |
| 22 | 3.763e+01 [3.084e+01, 5.112e+01] | 5.212e+01 [4.466e+01, 5.703e+01] |
| 23 | 6.131e+00 [5.709e+00, 6.328e+00] | 5.980e+00 [4.970e+00, 6.328e+00] |
| 24 | 6.359e+02 [6.047e+02, 6.587e+02] | 6.829e+02 [6.398e+02, 7.275e+02] |

\newpage

# S5 Fixed BBOB structural groups

S1=f1-5 (separable), S2=f6-9 (low/moderate conditioning), S3=f10-14 (ill-conditioned unimodal), S4=f15-19 (structured multimodal), S5=f20-24 (weakly structured multimodal). Values are equal-function means of endpoint scores. These groups are descriptive and do not become new significant subgroup claims.

| D | Group | Greedy | Fixed .1 | Fixed .3 | Random | PEM-T | PEM-ST |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | S1 | -0.7844 | -0.7450 | -0.6725 | -0.0863 | -0.6413 | -0.6387 |
| 10 | S2 | -1.8355 | -1.8326 | -1.7300 | -0.2636 | -1.5626 | -1.6490 |
| 10 | S3 | -0.7892 | -0.7628 | -0.5927 | -0.2560 | -0.5328 | -0.5780 |
| 10 | S4 | -0.3336 | -0.2970 | -0.2577 | -0.1259 | -0.2222 | -0.2241 |
| 10 | S5 | -1.0173 | -0.9644 | -0.8509 | -0.1286 | -0.7885 | -0.8232 |
| 20 | S1 | -0.8709 | -0.8257 | -0.7530 | -0.1946 | -0.7332 | -0.7661 |
| 20 | S2 | -1.8155 | -1.8273 | -1.6113 | -0.3130 | -1.7193 | -1.7759 |
| 20 | S3 | -0.8261 | -0.7938 | -0.6608 | -0.3656 | -0.6825 | -0.6829 |
| 20 | S4 | -0.3937 | -0.3728 | -0.3356 | -0.1352 | -0.3228 | -0.3479 |
| 20 | S5 | -0.7836 | -0.7511 | -0.6625 | -0.1212 | -0.6122 | -0.5632 |
| 40 | S1 | -0.8011 | -0.7802 | -0.6967 | -0.2467 | -0.7166 | -0.6799 |
| 40 | S2 | -1.6514 | -1.6845 | -1.5366 | -0.4042 | -1.5056 | -1.4631 |
| 40 | S3 | -0.7668 | -0.7300 | -0.6667 | -0.3791 | -0.6789 | -0.6440 |
| 40 | S4 | -0.3955 | -0.3823 | -0.3620 | -0.1788 | -0.3470 | -0.3622 |
| 40 | S5 | -0.6313 | -0.5684 | -0.4519 | -0.1309 | -0.5548 | -0.5230 |

\newpage

# S6 Localized bounds and metric conventions

Actual selected points; differences are ST minus T, within each dimension/history. Lower quantile loss does not establish optimization gains. State-level fallback and component-level aggregation differ; this table uses the frozen function-level diagnostic aggregation.

| D | History | Loss ST-T | Margin ST-T | ESS ST-T | Fallback ST-T |
| --- | --- | --- | --- | --- | --- |
| 10 | fixed03 | -0.0175 | -0.1673 | -5.5875 | 0.0000 |
| 10 | greedy | -0.0106 | -0.0884 | -7.3423 | 0.0000 |
| 10 | pool_random | -0.0033 | -0.0317 | -1.6307 | 0.0000 |
| 20 | fixed03 | -0.0250 | -0.2231 | -11.3516 | 0.0000 |
| 20 | greedy | -0.0108 | -0.1154 | -13.5952 | 0.0000 |
| 20 | pool_random | -0.0030 | -0.0380 | -1.4721 | 0.0000 |
| 40 | fixed03 | -0.0159 | -0.1990 | -11.1133 | 0.0000 |
| 40 | greedy | -0.0082 | -0.1211 | -14.6521 | 0.0000 |
| 40 | pool_random | -0.0020 | -0.0260 | -0.9110 | 0.0000 |

The frozen AUC and convergence curve floor absolute error at 1e-12 before division by initial error, then take log10, inclusive from n0 through B. The endpoint floors the error ratio after division. They are distinct formulas at the near-zero boundary. This dataset has no curve entries below -12 and no exactly optimal final run; the boundary distinction remains documented.

Full CSV sources include function_scores.csv, prespecified_function_contrasts.csv, internal_raw_error_iqr.csv, structural_endpoint_scores.csv, and localization_description.csv. Full checkpoint records and sparse declaration denominators accompany the audit. This printable supplement does not replace the machine-readable records or source fingerprint manifest.
