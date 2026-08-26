# Round-2 review analyses

## 1. H2 specification adjudication: how the correct x condition terms move

- **binary (correct x hard01)**: ai-reliability: b = +5.22 [+2.89, +7.56], p = 0.0000; alternatives: b = +3.31 [+0.98, +5.64], p = 0.0054
- **continuous (+ cond x diff_z)**: ai-reliability: b = +0.15 [-2.41, +2.71], p = 0.9079; alternatives: b = +1.24 [-1.33, +3.81], p = 0.3452
- **item FE (correct x item)**: ai-reliability: b = +5.31 [+3.02, +7.60], p = 0.0000; alternatives: b = +3.59 [+1.31, +5.88], p = 0.0021
- **item FE + cond x item**: ai-reliability: b = +0.15 [-2.37, +2.66], p = 0.9092; alternatives: b = +1.65 [-0.88, +4.17], p = 0.2025
- **three-way (correct x cond x diff_z)**: ai-reliability: b = +0.32 [-2.23, +2.88], p = 0.8036; alternatives: b = +1.25 [-1.33, +3.82], p = 0.3423
  - three-way correct01:C(cond)[T.ai-reliability]:diff_z: b = +0.25, p = 0.8557
  - three-way correct01:C(cond)[T.alternatives]:diff_z: b = -5.57, p = 0.0000
  - three-way correct01:C(cond)[T.pause-points]:diff_z: b = -3.22, p = 0.0150
  - three-way correct01:C(cond)[T.reflection-task]:diff_z: b = -2.81, p = 0.0397

BIC-approximate BF01 for dropping the correct x condition block from the maximal item-FE model: 26,802,359 (BIC full 98105 vs reduced 98071; Wagenmakers 2007 approximation)

## 2. Continuous-difficulty control WITHIN the easy stratum

- easy-only correct01:C(cond)[T.ai-reliability]: b = -0.05, p = 0.9778
- easy-only correct01:C(cond)[T.alternatives]: b = +5.71, p = 0.0012

## 3. JZS Bayes-factor prior sensitivity (r = 0.5, 0.707, 1.0)

| test | r=0.5 | r=0.707 | r=1.0 |
|---|---|---|---|
| BF0+ score, cards vs baseline | 19.2 | 27.0 | 38.1 |
| BF0+ score, alternatives vs baseline | 18.9 | 26.5 | 37.5 |
| BF0+ score, pause vs baseline | 66.4 | 93.6 | 132.1 |
| BF0+ score, reflection vs baseline | 7.6 | 10.6 | 14.8 |
| BF10 two-sided score, pause vs baseline | 1.33e+05 | 1.29e+05 | 1.13e+05 |
| BF01 two-sided score, reflection vs baseline | 6.1 | 8.4 | 11.8 |
| BF01 two-sided monitoring error, reflection vs baseline | 2.1 | 2.8 | 3.9 |

## 4. Wave-1 manual exclusion list (18 IDs, not applied): sensitivity

- flagged among analyzed N: 13 (N drops 917 -> 904)
- max |delta-g| across the 16 confirmatory contrasts: 0.019 (actual_score / cards: g -0.226 -> -0.245)

## 5. Reliability cards: card-implied benchmark and exposure dose-response

- card-implied expected score: 7.1 of 12 (the cards imply 59% assistant accuracy; scripted eval measured 41.7%)
- cards post-estimate M = 8.23 vs benchmark 7.1: t = 7.11, p = 2.63e-11 (estimates sit ABOVE the card anchor)
- baseline post-estimate M = 9.70; actual scores: cards 5.18, baseline 5.57
- cards |estimate - anchor| M = 1.93 vs |estimate - own score| M = 3.35 (paired t = -10.96, p = 9.12e-22)
- card exposure: median 12/12 presented, 90% saw all 12, min 0
- dose-response r(cards shown, monitoring error) = +0.00 (p = 0.999)
- dose-response r(cards shown, post estimate) = -0.05 (p = 0.536)
- dose-response r(cards shown, dConf) = +0.12 (p = 0.122)

## 6. Per-protocol gate sensitivity: high-gate-share halves vs baseline

(endogenous split: gate share depends on participant prompt style)

- alternatives high-share half (n = 98, median share 0.71): error g = -0.60 (p = 0.000); score g = -0.23 (p = 0.053)
- pause high-share half (n = 92, median share 0.53): error g = -0.31 (p = 0.014); score g = -0.63 (p = 0.000)
- reflection high-share half (n = 94, median share 0.55): error g = -0.06 (p = 0.633); score g = -0.03 (p = 0.778)

## 7. Stratified dConf: per-stratum ns and condition-differential exclusion

- easy: baseline 172/187; cards 171/182; alternatives 173/181
  chi-square on defined-vs-dropped rates: chi2 = 2.07, p = 0.356
- hard: baseline 160/187; cards 145/182; alternatives 154/181
  chi-square on defined-vs-dropped rates: chi2 = 2.84, p = 0.242

## 8. Murphy resolution ceiling: perfectly difficulty-keyed observer

- baseline: ceiling resolution = 0.0443 (a confidence = item base-rate observer)
- cards: ceiling resolution = 0.0418 (a confidence = item base-rate observer)
- alternatives: ceiling resolution = 0.0483 (a confidence = item base-rate observer)
- pause: ceiling resolution = 0.0231 (a confidence = item base-rate observer)
- reflection: ceiling resolution = 0.0540 (a confidence = item base-rate observer)

## 9. Four-option guessing floor: knowledge rate and lucky-guess share

- baseline: accuracy 0.464, knowledge rate k = 0.286, lucky-guess share of correct trials = 38%
- cards: accuracy 0.432, knowledge rate k = 0.242, lucky-guess share of correct trials = 44%
- alternatives: accuracy 0.433, knowledge rate k = 0.244, lucky-guess share of correct trials = 44%
- pause: accuracy 0.374, knowledge rate k = 0.165, lucky-guess share of correct trials = 56%
- reflection: accuracy 0.460, knowledge rate k = 0.281, lucky-guess share of correct trials = 39%
- pooled: accuracy 0.433, knowledge rate k = 0.244, lucky-guess share of correct trials = 44%
- items at or below the 25% floor (pooled): 3 of 12 (range 0.180-0.255 for the 4 hardest)

## 10. H3 headroom: always-follow vs oracle-reliance expected scores

- scripted-eval per-item assistant accuracy (n = 3 reps/item, patient sweep): mean 0.417
- expected score always-follow = 5.00/12; oracle reliance (follow when right, guess otherwise) = 6.75/12; headroom = 1.75 problems (15 pp)
- observed condition means: baseline 5.57, cards 5.18, alternatives 5.20, pause 4.49, reflection 5.52
- (oracle assumes perfect trial-level error detection AND 25% chance on rejected trials; real headroom is smaller)

## 11. Per-participant type-2 AUC attenuation at 12 trials (simulation)

- true AUC2 = 0.55 -> mean 12-trial estimate = 0.551
- true AUC2 = 0.60 -> mean 12-trial estimate = 0.594
- true AUC2 = 0.65 -> mean 12-trial estimate = 0.642
- true AUC2 = 0.70 -> mean 12-trial estimate = 0.691

## 12. Signed estimation error (post estimate - actual score) by condition

- baseline: M = +4.12 (SD 2.91)
- cards: M = +3.04 (SD 2.64)
- alternatives: M = +2.50 (SD 2.56)
- pause: M = +3.28 (SD 2.88)
- reflection: M = +3.63 (SD 3.04)
