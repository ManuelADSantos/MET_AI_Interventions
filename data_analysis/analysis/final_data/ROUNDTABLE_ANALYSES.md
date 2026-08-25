# Roundtable analyses

## 1. Reflection monitoring-error null, held to the performance-null standard

- TOST |g|<0.3: p = 0.088
- TOST |g|<0.2: p = 0.347
- two-sided BF10 = 0.35 (BF01 = 2.83); BF0- (against an error reduction) = 1.52
- score TOST |g|<0.3: p = 0.005
- score TOST |g|<0.2: p = 0.049

## 2. Discrimination within baseline-derived difficulty strata

- **easy items**: baseline M=2.41 (n=172); cards M=4.74 (n=171), g=+0.16, p=0.137; alternatives M=8.79 (n=173), g=+0.36, p=0.001
- **hard items**: baseline M=0.79 (n=160); cards M=-0.85 (n=145), g=-0.10, p=0.391; alternatives M=-3.18 (n=154), g=-0.20, p=0.081

MixedLM confidence ~ correct x condition + correct x difficulty (participant RI):
- correct01:C(cond)[T.ai-reliability]: b = +5.22, p = 0.0000
- correct01:C(cond)[T.alternatives]: b = +3.31, p = 0.0054
- correct01:C(cond)[T.pause-points]: b = +1.64, p = 0.1769
- correct01:C(cond)[T.reflection-task]: b = -0.31, p = 0.7928
- correct01:hard01: b = -5.13, p = 0.0000

## 3. Post-estimate-on-score slope by condition (tracking vs bias)

- baseline: slope = +0.07 (r = +0.05, p = 0.489)
- cards: slope = +0.05 (r = +0.04, p = 0.616)
- alternatives: slope = +0.14 (r = +0.10, p = 0.181)
- pause: slope = +0.28 (r = +0.22, p = 0.003)
- reflection: slope = -0.02 (r = -0.01, p = 0.878)

## 4. Bootstrap 95% CIs for the efficiency ledger

- cards: 0.217 items/SUS-pt, 95% CI [0.107, 0.659] (unstable resamples: 0.0%)
- alternatives: 0.121 items/SUS-pt, 95% CI [0.081, 0.180] (unstable resamples: 0.0%)
- pause: 0.041 items/SUS-pt, 95% CI [0.016, 0.066] (unstable resamples: 0.0%)
- reflection: 0.058 items/SUS-pt, 95% CI [-0.018, 0.154] (unstable resamples: 0.0%)
- cards gain / alternatives gain: 0.73, 95% CI [0.46, 1.03]
- cards SUS cost / alternatives SUS cost: 0.41, 95% CI [0.12, 0.69]

## 5. Holm across all 16 confirmatory directional tests

- survives Holm-16: absolute_estimation_error / cards (raw one-sided p = 6.58e-06, Holm p = 0.000)
- survives Holm-16: absolute_estimation_error / alternatives (raw one-sided p = 4.14e-10, Holm p = 0.000)
- survives Holm-16: absolute_estimation_error / pause (raw one-sided p = 7.54e-04, Holm p = 0.008)
- survives Holm-16: confidence_discrimination / cards (raw one-sided p = 1.48e-06, Holm p = 0.000)
- survives Holm-16: confidence_discrimination / alternatives (raw one-sided p = 3.59e-03, Holm p = 0.036)
- survives Holm-16: prompts_per_task / pause (raw one-sided p = 1.22e-29, Holm p = 0.000)
- survives Holm-16: prompts_per_task / reflection (raw one-sided p = 5.68e-12, Holm p = 0.000)
(all other tests: Holm-16 p >= .05)

Two-sided reversal, Holm within score family: cards p=0.030->Holm 0.090, alternatives p=0.033->Holm 0.090, pause p=0.000->Holm 0.000, reflection p=0.792->Holm 0.792

## 6. Trial-level Brier, Murphy decomposition, calibration slope

- baseline: Brier = 0.391 (reliability 0.143, resolution 0.002, uncertainty 0.249); calibration slope = +0.082 (p = 0.054)
- cards: Brier = 0.347 (reliability 0.106, resolution 0.005, uncertainty 0.245); calibration slope = +0.263 (p = 0.000)
- alternatives: Brier = 0.361 (reliability 0.119, resolution 0.004, uncertainty 0.246); calibration slope = +0.225 (p = 0.000)
- pause: Brier = 0.376 (reliability 0.146, resolution 0.004, uncertainty 0.234); calibration slope = +0.188 (p = 0.000)
- reflection: Brier = 0.391 (reliability 0.144, resolution 0.002, uncertainty 0.248); calibration slope = +0.082 (p = 0.056)

## 7. Wave-2 gate: engagement distribution and dose-response

- alternatives: median matched share = 0.71 (IQR 0.57-0.86, n = 181); dose-response r(share, monitoring error) = -0.03 (p = 0.714), r(share, score) = +0.10 (p = 0.187)
- pause: median matched share = 0.53 (IQR 0.23-0.75, n = 184); dose-response r(share, monitoring error) = -0.02 (p = 0.801), r(share, score) = +0.03 (p = 0.708)
- reflection: median matched share = 0.55 (IQR 0.43-0.80, n = 183); dose-response r(share, monitoring error) = +0.13 (p = 0.073), r(share, score) = +0.06 (p = 0.408)

## 8. Overconfidence (conf - 100*correct) on baseline-derived 6/6 split

- baseline: easy +16.2 pp, hard +49.0 pp
- cards: easy +14.1 pp, hard +37.5 pp
- alternatives: easy +10.6 pp, hard +42.3 pp
- pause: easy +19.1 pp, hard +39.8 pp
- reflection: easy +12.1 pp, hard +49.8 pp

4-easiest pooled range (n=917): 0.517-0.800; 4-hardest: 0.180-0.255
baseline-derived easy-6 accuracy range (pooled): 0.42-0.80

## 9. Discrimination with continuous item-difficulty control (decisive)

- correct01: b = +1.22, p = 0.1864
- correct01:C(cond)[T.ai-reliability]: b = +0.15, p = 0.9079
- correct01:C(cond)[T.alternatives]: b = +1.24, p = 0.3452
- correct01:C(cond)[T.pause-points]: b = +0.52, p = 0.6889
- correct01:C(cond)[T.reflection-task]: b = -0.24, p = 0.8553
- correct01:diff_z: b = -3.51, p = 0.0000

With item difficulty and its interactions controlled, correct x condition vanishes for every intervention: the dConf/AUC2 gains are carried by difficulty-keyed confidence adjustment, not improved within-item discrimination.
