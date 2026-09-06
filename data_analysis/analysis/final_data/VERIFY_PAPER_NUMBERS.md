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

Strategies: N = 814 (per condition [170, 147, 165, 172, 160]); uncoded [0.0, 0.0, 0.0, 0.0, 0.0]%
| code | Base | Cards | Alts | Pausep | Refl | chi2 (df) | p | Cramer's V | N |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UNCODED | 33.5 | 24.5 | 28.5 | 45.9 | 33.8 | 19.14 (4) | 0.001 | 0.153 | 814 |
| ai_self_verify | 14.1 | 15.0 | 13.3 | 3.5 | 10.6 | 14.67 (4) | 0.005 | 0.134 | 814 |
| effort_cost_time | 9.4 | 3.4 | 4.2 | 7.0 | 10.6 | 9.60 (4) | 0.048 | 0.109 | 814 |
| full_reliance | 18.8 | 8.8 | 3.6 | 11.6 | 14.4 | 21.23 (4) | 0.000 | 0.161 | 814 |
| manipulation_use | 0.0 | 11.6 | 38.8 | 9.9 | 0.0 | 105.08 (3) | 0.000 | 0.404 | 644 |
| no_strategy | 1.2 | 3.4 | 3.0 | 1.7 | 4.4 | 4.15 (4) | 0.386 | 0.071 | 814 |
| overrode_ai | 3.5 | 4.1 | 6.7 | 1.7 | 3.8 | 5.54 (4) | 0.236 | 0.083 | 814 |
| own_first_then_compare | 12.9 | 19.7 | 13.3 | 12.8 | 19.4 | 6.25 (4) | 0.181 | 0.088 | 814 |
| prompt_engineering | 5.3 | 6.1 | 3.6 | 7.0 | 5.0 | 2.04 (4) | 0.728 | 0.050 | 814 |
| reasoning_check | 12.9 | 8.2 | 9.1 | 6.4 | 5.0 | 8.01 (4) | 0.091 | 0.099 | 814 |
| unspecified_verification | 9.4 | 15.0 | 6.7 | 6.4 | 10.6 | 8.85 (4) | 0.065 | 0.104 | 814 |
| verify_against_source | 11.8 | 6.1 | 9.7 | 6.4 | 4.4 | 8.25 (4) | 0.083 | 0.101 | 814 |

Effect of the manipulation: N = 640 (per condition [145, 162, 173, 160]); uncoded [0.0, 0.0, 0.0, 0.0]%
| code | Cards | Alts | Pausep | Refl | chi2 (df) | p | Cramer's V | N |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UNCODED | 40.0 | 52.5 | 57.8 | 59.4 | 14.05 (3) | 0.003 | 0.148 | 640 |
| more_careful | 33.1 | 25.3 | 9.8 | 11.9 | 36.77 (3) | 0.000 | 0.240 | 640 |
| no_change | 13.8 | 12.3 | 8.7 | 24.4 | 17.78 (3) | 0.000 | 0.167 | 640 |
| slowed_friction | 2.8 | 2.5 | 23.1 | 6.2 | 58.56 (3) | 0.000 | 0.303 | 640 |
| trust_less | 17.2 | 11.7 | 2.3 | 0.6 | 40.82 (3) | 0.000 | 0.253 | 640 |
| trust_more | 1.4 | 1.2 | 0.6 | 0.6 | 0.87 (3) | 0.833 | 0.037 | 640 |

Held-out validation: macro-F1 over all 16 codes = 0.61 (paper .61); codes with F1 >= .7: ['effort_cost_time', 'full_reliance', 'manipulation_use', 'more_careful', 'no_change', 'no_strategy', 'reasoning_check']

## Headroom (Discussion)

Baseline parsed advice accuracy 47.1%; always following yields 5.65 of 12 (paper 5.65 at 47%).
