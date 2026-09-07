# Paper numbers recomputed from the exported data


## Sample (tab:participants)

| condition | n | age M (SD) | AI use M (SD) | median completion min |
| --- | --- | --- | --- | --- |
| Base | 187 | 36.3 (11.1) | 6.0 (1.1) | 30.6 |
| Cards | 182 | 35.6 (10.8) | 5.7 (1.5) | 35.2 |
| Alts | 181 | 35.8 (10.7) | 5.7 (1.6) | 36.8 |
| Pausep | 184 | 35.0 (10.8) | 5.9 (1.4) | 41.5 |
| Refl | 183 | 35.7 (11.2) | 5.7 (1.5) | 69.7 |

Reflection sessions over 60 min: 67% (paper: 67%).
AI use by condition (baseline vs others): {'ai': 6.04, 'ai-reliability': 5.7, 'alternatives': 5.66, 'pause-points': 5.87, 'reflection-task': 5.72}

## Tasks

Pooled item accuracy range: 18--80% (paper 18--78); baseline: 20--86% (paper 20--86).
Items at or below 25% pooled: 3 (paper 3); by baseline accuracy: 2 (paper 2).
Pooled participant accuracy: 43.3% (paper 43.3); baseline: 46.4% (paper 46.4).
Every participant prompted on all 12 problems: True.

## Manipulation and exposure checks

Cards shown on all 12 problems: 90% of participants (paper 90%); share of problems with card: 97% (paper 97%); collapsed at least once: 72% (paper 72%).
Pause-points gate engaged share of problems: 74% (paper 74%).
Reflection pages answered median: 12/12; median words 973 (paper 973).
Assistant output tokens per participant: {'ai': 24226.0, 'ai-reliability': 22711.0, 'alternatives': 57853.0, 'pause-points': 21701.0, 'reflection-task': 30468.0} (alternatives about double).
Mean prompt words by condition: {'ai': 133.0, 'ai-reliability': 122.0, 'alternatives': 127.0, 'pause-points': 70.0, 'reflection-task': 166.0} (paper: pause 70 vs 122--166).

## Calibration profile (tab:calib)

| condition | overestimating % | signed error M (SD) | delta with-AI estimate | conf - acc (pp) | delta (AI - self) gap |
| --- | --- | --- | --- | --- | --- |
| Base | 88 | +4.12 (2.91) | -0.48 | +32.6 | +1.05 |
| Cards | 80 | +3.04 (2.64) | -1.59 | +25.8 | +0.03 |
| Alts | 76 | +2.50 (2.56) | -1.94 | +26.5 | -0.01 |
| Pausep | 80 | +3.28 (2.88) | -2.18 | +29.4 | +0.69 |
| Refl | 85 | +3.63 (3.04) | -0.51 | +30.9 | +1.48 |

Share of all participants overestimating: 82% (paper 82%).

## Proper scoring and type-2 AUC

| condition | Brier | reliability | resolution | uncertainty | pooled type-2 AUC | participant-mean AUC |
| --- | --- | --- | --- | --- | --- | --- |
| Base | 0.391 | 0.143 | 0.002 | 0.249 | 0.516 | 0.541 |
| Cards | 0.347 | 0.106 | 0.005 | 0.245 | 0.573 | 0.603 |
| Alts | 0.361 | 0.119 | 0.004 | 0.246 | 0.565 | 0.571 |
| Pausep | 0.376 | 0.146 | 0.004 | 0.234 | 0.549 | 0.550 |
| Refl | 0.391 | 0.144 | 0.002 | 0.248 | 0.515 | 0.523 |

Cards vs baseline on participant type-2 AUC: t(366.8) = 3.45, p = 0.001, g = +0.36 (paper g = +0.36).
Pooled baseline type-2 AUC 0.516 [0.491, 0.539] (paper .516 [.493, .539]).

## Difficulty analyses

| condition | conf-acc hard (pp) | conf-acc easy (pp) | acc hard % | acc easy % |
| --- | --- | --- | --- | --- |
| Base | +49 | +16 | 29 | 64 |
| Cards | +37 | +14 | 25 | 61 |
| Alts | +42 | +11 | 25 | 62 |
| Pausep | +40 | +19 | 25 | 50 |
| Refl | +50 | +12 | 26 | 66 |

GEE logit correct ~ condition x difficulty_z (interaction terms):
- C(condition, Treatment('ai'))[T.ai-reliability]:difficulty_z: b = +0.06, z = 0.69, p = 0.491
- C(condition, Treatment('ai'))[T.alternatives]:difficulty_z: b = -0.03, z = -0.39, p = 0.694
- C(condition, Treatment('ai'))[T.pause-points]:difficulty_z: b = +0.33, z = 4.26, p = 0.000
- C(condition, Treatment('ai'))[T.reflection-task]:difficulty_z: b = -0.11, z = -1.34, p = 0.180
Pause points vs baseline on the six easy items: t(360.1) = -6.25, p = 1.18e-09, g = -0.65 (paper g = -0.65).

GEE linear confidence ~ condition x difficulty_z (interaction = extra pp of confidence per SD of difficulty vs baseline):
- C(condition, Treatment('ai'))[T.ai-reliability]:difficulty_z: b = -5.97, z = -9.00, p = 0.000
- C(condition, Treatment('ai'))[T.alternatives]:difficulty_z: b = -2.55, z = -4.99, p = 0.000
- C(condition, Treatment('ai'))[T.pause-points]:difficulty_z: b = -0.73, z = -1.35, p = 0.177
- C(condition, Treatment('ai'))[T.reflection-task]:difficulty_z: b = +0.02, z = 0.04, p = 0.969

## Time course

Accuracy vs display position, pooled r = 0.014, p = 0.155 (paper r = .001).
Second half minus first half accuracy: M = -0.011, t(916) = -1.10, p = 0.272.

## Card anchoring

Cards: mean |estimate - 7.1| = 1.93 vs |estimate - actual| = 3.35 (paper 1.9 vs 3.4); paired t on the two distances: t(181) = -10.96, p = 9.12e-22; estimate above 7.1: one-sample t(181) = 7.11, p = 2.63e-11.

## Trust correlations (appendix)

- trust vs abs. estimation error: r = 0.36, p = 1.73e-29
- trust vs signed error: r = 0.42, p = 1.3e-39
- trust vs confidence: r = 0.43, p = 5.48e-42
- trust vs score: r = 0.06, p = 0.066

## Qualitative codes on the analysed sample (tab:qual)

Strategies: 814 of 814 answers human-coded; the rest lexical codebook v2
Strategies: N = 814 (per condition [170, 147, 165, 172, 160]); uncoded [1.2, 0.0, 0.6, 2.3, 0.6]%
| code | Base | Cards | Alts | Pausep | Refl | chi2 (df) | p | Cramer's V | N |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ai_self_verify | 14.7 | 12.2 | 18.2 | 6.4 | 8.8 | 13.83 (4) | 0.008 | 0.130 | 814 |
| effort_cost_time | 1.2 | 2.7 | 1.8 | 1.7 | 8.8 | 20.50 (4) | 0.000 | 0.159 | 814 |
| full_reliance | 51.2 | 34.7 | 26.1 | 47.1 | 50.0 | 32.34 (4) | 0.000 | 0.199 | 814 |
| manipulation_use | 0.0 | 11.6 | 34.5 | 1.2 | 0.0 | 122.12 (3) | 0.000 | 0.435 | 644 |
| no_strategy | 2.9 | 6.8 | 7.9 | 9.9 | 8.1 | 6.88 (4) | 0.142 | 0.092 | 814 |
| overrode_ai | 2.9 | 2.0 | 3.0 | 4.7 | 3.1 | 1.87 (4) | 0.761 | 0.048 | 814 |
| own_first_then_compare | 14.7 | 14.3 | 14.5 | 14.0 | 16.9 | 0.68 (4) | 0.954 | 0.029 | 814 |
| prompt_engineering | 8.8 | 8.8 | 7.3 | 16.9 | 10.0 | 10.26 (4) | 0.036 | 0.112 | 814 |
| reasoning_check | 26.5 | 27.2 | 36.4 | 19.8 | 15.0 | 23.02 (4) | 0.000 | 0.168 | 814 |
| unspecified_verification | 5.3 | 4.8 | 3.0 | 2.9 | 5.0 | 2.16 (4) | 0.706 | 0.052 | 814 |
| verify_against_source | 8.8 | 5.4 | 8.5 | 8.7 | 7.5 | 1.70 (4) | 0.791 | 0.046 | 814 |

Effect of the manipulation: 640 of 640 answers human-coded; the rest lexical codebook v2
Effect of the manipulation: N = 640 (per condition [145, 162, 173, 160]); uncoded [6.9, 4.9, 3.5, 11.2]%
| code | Cards | Alts | Pausep | Refl | chi2 (df) | p | Cramer's V | N |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| more_careful | 42.8 | 48.8 | 49.1 | 32.5 | 11.97 (3) | 0.007 | 0.137 | 640 |
| no_change | 17.9 | 16.0 | 12.1 | 38.8 | 41.65 (3) | 0.000 | 0.255 | 640 |
| slowed_friction | 2.8 | 15.4 | 26.6 | 9.4 | 40.96 (3) | 0.000 | 0.253 | 640 |
| trust_less | 31.7 | 34.0 | 11.0 | 4.4 | 65.74 (3) | 0.000 | 0.321 | 640 |
| trust_more | 19.3 | 21.6 | 18.5 | 17.5 | 0.96 (3) | 0.812 | 0.039 | 640 |

Held-out validation: macro-F1 over all 16 codes = 0.61 (paper .61); codes with F1 >= .7: ['effort_cost_time', 'full_reliance', 'manipulation_use', 'more_careful', 'no_change', 'no_strategy', 'reasoning_check']

## Headroom (Discussion)

Baseline parsed advice accuracy 47.1%; always following yields 5.65 of 12 (paper 5.65 at 47%).
