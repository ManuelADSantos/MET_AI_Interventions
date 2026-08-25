# Meeting analyses (2026-08-25)

n = 917 participants, 11004 trials. Exploratory/uncorrected unless stated.

## 1. Temporal analysis

### Accuracy by display position (proportion correct)

| condition | p1 | p2 | p3 | p4 | p5 | p6 | p7 | p8 | p9 | p10 | p11 | p12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.46 | 0.45 | 0.51 | 0.45 | 0.48 | 0.44 | 0.47 | 0.46 | 0.48 | 0.45 | 0.50 | 0.43 |
| reliability cards | 0.42 | 0.38 | 0.45 | 0.40 | 0.52 | 0.47 | 0.35 | 0.41 | 0.40 | 0.49 | 0.42 | 0.48 |
| alternatives | 0.44 | 0.46 | 0.45 | 0.47 | 0.46 | 0.37 | 0.45 | 0.38 | 0.45 | 0.39 | 0.47 | 0.40 |
| pause points | 0.38 | 0.35 | 0.34 | 0.41 | 0.40 | 0.38 | 0.38 | 0.33 | 0.35 | 0.35 | 0.40 | 0.42 |
| reflection | 0.45 | 0.47 | 0.50 | 0.42 | 0.48 | 0.47 | 0.44 | 0.42 | 0.50 | 0.48 | 0.43 | 0.49 |

### Within-participant trend (per-trial correctness vs position)

| condition | pooled r(position, correct) | p |
|---|---|---|
| baseline | -0.002 | 0.922 |
| reliability cards | +0.019 | 0.364 |
| alternatives | -0.025 | 0.246 |
| pause points | +0.012 | 0.558 |
| reflection | +0.001 | 0.946 |
| ALL | +0.001 | 0.896 |

### Score excluding the first displayed trial (0-11) vs full score: Welch vs baseline

| intervention | M(0-11) | g vs baseline | two-sided p | full-score g (ref) |
|---|---|---|---|---|
| reliability cards | 4.76 | -0.21 | 0.045 | -0.23 |
| alternatives | 4.76 | -0.22 | 0.036 | -0.22 |
| pause points | 4.11 | -0.56 | 0.000 | -0.57 |
| reflection | 5.07 | -0.02 | 0.813 | -0.03 |

### Halves and thirds (proportion correct per block, within participant)


**halves**

| condition | pos 1-6 | pos 7-12 | last-first Δ | paired p |
|---|---|---|---|---|
| baseline | 0.463 | 0.465 | +0.002 | 0.933 |
| reliability cards | 0.440 | 0.424 | -0.016 | 0.481 |
| alternatives | 0.443 | 0.424 | -0.019 | 0.377 |
| pause points | 0.376 | 0.372 | -0.004 | 0.857 |
| reflection | 0.464 | 0.457 | -0.006 | 0.767 |

Condition differences in last-minus-first change (halves): F = 0.17, p = 0.956

**thirds**

| condition | pos 1-4 | pos 5-8 | pos 9-12 | last-first Δ | paired p |
|---|---|---|---|---|---|
| baseline | 0.467 | 0.460 | 0.467 | +0.000 | 1.000 |
| reliability cards | 0.412 | 0.438 | 0.445 | +0.033 | 0.219 |
| alternatives | 0.456 | 0.414 | 0.430 | -0.026 | 0.287 |
| pause points | 0.370 | 0.372 | 0.380 | +0.011 | 0.636 |
| reflection | 0.459 | 0.449 | 0.473 | +0.014 | 0.582 |

Condition differences in last-minus-first change (thirds): F = 0.78, p = 0.541

## 2. Easy vs hard items x condition

Item difficulty (pooled p correct) range 0.18-0.80; easy = 4 easiest items, hard = 4 hardest.

| condition | acc easy | acc hard | overconf easy (pp) | overconf hard (pp) |
|---|---|---|---|---|
| baseline | 0.717 | 0.247 | +9.1 | +53.3 |
| reliability cards | 0.672 | 0.217 | +10.3 | +41.6 |
| alternatives | 0.696 | 0.198 | +5.5 | +46.4 |
| pause points | 0.546 | 0.209 | +15.7 | +44.7 |
| reflection | 0.740 | 0.219 | +5.4 | +55.0 |

### Does any intervention help differentially on easy vs hard? (accuracy)

| intervention | easy-hard gap | Δgap vs baseline (g) | two-sided p |
|---|---|---|---|
| reliability cards | 0.455 | -0.05 | 0.659 |
| alternatives | 0.499 | +0.09 | 0.369 |
| pause points | 0.337 | -0.41 | 0.000 |
| reflection | 0.522 | +0.17 | 0.101 |

baseline easy-hard gap = 0.469

## 3. Dunning-Kruger across conditions

signed error = post estimate - actual score (positive = overestimation).

| condition | r(score, signed error) | OLS slope |
|---|---|---|
| baseline | -0.582 | -0.933 |
| reliability cards | -0.588 | -0.951 |
| alternatives | -0.510 | -0.855 |
| pause points | -0.499 | -0.719 |
| reflection | -0.552 | -1.018 |

Modulation test — OLS signed error ~ score x condition (HC3 SEs), interaction terms:

| term | b | p |
|---|---|---|
| score:C(cond)[T.ai-reliability] | -0.018 | 0.895 |
| score:C(cond)[T.alternatives] | +0.078 | 0.591 |
| score:C(cond)[T.pause-points] | +0.214 | 0.110 |
| score:C(cond)[T.reflection-task] | -0.084 | 0.574 |

Joint interaction test: F = 1.47, p = 0.210 (gradient modulation by condition)

Note: estimate-score regression toward the mean inflates this gradient mechanically; the condition-modulation test is the informative part.

## 4. Trial-level linear mixed models (participant random intercept)

Trials in models: 11004 (NFC or confidence missing on 0).

### correctness (linear probability model)

| term | b | p |
|---|---|---|
| Intercept | +0.464 | 0.000 |
| C(cond)[T.ai-reliability] | -0.033 | 0.042 |
| C(cond)[T.alternatives] | -0.031 | 0.052 |
| C(cond)[T.pause-points] | -0.090 | 0.000 |
| C(cond)[T.reflection-task] | -0.004 | 0.807 |
| pos_z | +0.001 | 0.895 |
| nfc_z | +0.000 | 0.940 |

### confidence (0-100)

| term | b | p |
|---|---|---|
| Intercept | +78.744 | 0.000 |
| C(cond)[T.ai-reliability] | -9.722 | 0.000 |
| C(cond)[T.alternatives] | -8.921 | 0.000 |
| C(cond)[T.pause-points] | -11.971 | 0.000 |
| C(cond)[T.reflection-task] | -1.512 | 0.401 |
| pos_z | -0.126 | 0.490 |
| nfc_z | +3.316 | 0.000 |

### correctness robustness: GEE logit (exchangeable)

| term | OR | p |
|---|---|---|
| Intercept | 0.867 | 0.001 |
| C(cond)[T.ai-reliability] | 0.877 | 0.029 |
| C(cond)[T.alternatives] | 0.882 | 0.032 |
| C(cond)[T.pause-points] | 0.690 | 0.000 |
| C(cond)[T.reflection-task] | 0.984 | 0.795 |
| pos_z | 1.003 | 0.893 |
| nfc_z | 1.002 | 0.936 |

## 5. Bayesian evidence on the performance null (JZS, r = 0.707)

| intervention | t | BF10 (two-sided) | BF01 | BF0+ (vs improvement) |
|---|---|---|---|---|
| reliability cards | -2.18 | 1.12 | 0.90 | 27.0 |
| alternatives | -2.13 | 1.02 | 0.98 | 26.5 |
| pause points | -5.47 | 128973.31 | 0.00 | 93.6 |
| reflection | -0.26 | 0.12 | 8.41 | 10.6 |

BF0+ > 10 = strong evidence against a performance improvement; BF01 quantifies the two-sided (any difference) comparison.
