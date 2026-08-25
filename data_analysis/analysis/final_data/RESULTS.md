# Results — MET-AI Interventions (Final Dataset)

All five conditions, n = 917. Numbers produced by the notebooks in this folder; see
[`METHODS.md`](METHODS.md) for the pipeline and statistical conventions.

**Conventions.** Welch's *t* vs the `ai` baseline, Hedges' *g* [95% CI], Holm-corrected within
outcome family. Confirmatory p directional (per-wave preregistrations); two-sided reported where
it changes the conclusion. Omnibus = Welch's ANOVA + Kruskal–Wallis (ε²). α = .05.

---

## 1. Verdict

Does each intervention improve performance and/or metacognition vs baseline?

| Intervention | Performance | Metacognition | Hypothesis |
|---|---|---|---|
| Reliability cards | no (two-sided *reversed*, g = −0.23) | **yes** — error g = −0.46, discrimination g = +0.50 | **supported via metacognition** |
| Alternatives | no (two-sided reversed, g = −0.22) | **yes** — error g = −0.65, discrimination g = +0.28 | **supported via metacognition** |
| Pause points | no (two-sided reversed, g = −0.57) | partial — error g = −0.33 only | **partially supported** |
| Reflection task | no (g = −0.03) | no (error p = .064; discrimination n.s.) | **not supported** |

Three headline facts:

1. **Metacognition improves; performance does not.** No intervention raises accuracy; pause points
   lowers it (g = −0.57).
2. **The mechanism is mostly deflated self-estimates**, not insight — post-study estimates drop
   1.6–2.2 items in the effective interventions vs 0.5 in baseline. Exception: reliability cards
   and alternatives also sharpen item-level discrimination, which deflation alone cannot produce.
3. **Every intervention costs UX** — lower SUS and UEQ-S, higher TLX, and lower trust for three of
   four. Pause points is the most expensive; reliability cards the most efficient (§7).

## 2. Sample

| Condition | Intervention | Collected | Loaded | Analyzed |
|---|---|---|---|---|
| `ai` | Plain AI chat (baseline) | Jul 2026 (+5 Aug) | 189 | 187 |
| `ai-reliability` | Per-task AI reliability cards | Jul 2026 | 184 | 182 |
| `alternatives` | Two alternative AI replies per prompt | Aug 2026 | 183 | 181 |
| `pause-points` | Step-by-step AI replies with pause points | Aug 2026 | 184 | 184 |
| `reflection-task` | Reflection page after every problem | Aug 2026 | 185 | 183 |

925 loaded, 8 excluded (7 failed ≥2 of 4 attention checks; 1 finished < 10 min), **917 analyzed**.
Age M = 35.7 (SD 10.9, range 18–78); 45–54% women per condition; frequent AI users (M = 5.7–6.0
on 1–7). Median completion 30.6 / 35.2 / 36.8 / 41.5 / 69.7 min (baseline / reliability /
alternatives / pause / reflection) — reflection takes ~2× baseline.

**Cohort caveat.** Wave 1 (Jul 2026) = baseline + reliability cards; wave 2 (Aug 2026) = the other
three. Only 5 baseline participants came from wave 2, so every wave-2-vs-baseline comparison is
also cross-period. §9 shows the results survive the available checks; the confound cannot be fully
removed by analysis.

## 3. Data integrity

| Check | Result |
|---|---|
| `answerResults` present, 12 booleans, sum = `correctAnswers` | ✅ 925/925 |
| `answerResults` vs canonical-key recomputation | ✅ 0 mismatches / 11,100 items |
| Deduplication (38 repeat participants, earliest run kept) | ✅ verified vs raw wave exports |
| Convenience CSV correctness columns (`export_condition_csvs.py` scored against a key wrong on 8/12 items — 4,971/11,100 values disagreed) | ✅ **fixed** — now sourced from each record's `answerResults`, asserting `n_correct == correctAnswers` |
| Regenerated CSVs (2026-08-19) | ✅ 0/11,100 per-question, 0/925 `n_correct`, byte-for-byte reproducible |

All analysis metrics derive from the JSON records, not the convenience CSVs.

## 4. Confirmatory outcomes

Omnibus differences across the five conditions are significant for all four
families, on both the parametric and the non-parametric test:

| Outcome | Welch *F* | df | *p* | KW *H* | KW *p* | ε² |
|---|---|---|---|---|---|---|
| Metacognitive accuracy \|post estimate − actual\| | 11.87 | 4, 455.5 | 3.5 × 10⁻⁹ | 38.76 | < .001 | .038 |
| Confidence discrimination | 8.08 | 4, 452.0 | 2.7 × 10⁻⁶ | 33.40 | < .001 | .032 |
| Prompts per completed task | 54.06 | 4, 447.9 | 3.6 × 10⁻³⁷ | 279.01 | < .001 | .302 |
| Actual score | 9.44 | 4, 455.4 | 2.4 × 10⁻⁷ | 47.35 | < .001 | .048 |

**Why Welch's rather than classical ANOVA.** Group variances are unequal, so the
homoscedasticity assumption of classical ANOVA does not hold. Brown–Forsythe
tests reject equal variance for confidence discrimination (*p* = 2.5 × 10⁻⁸,
SDs 8.92–13.59), prompts per task (*p* = 5.2 × 10⁻³⁰, SDs 0.70–2.06) and
estimation error (*p* = .011, SDs 2.01–2.48); actual score is borderline
(*p* = .052, SDs 1.53–2.00). Welch's *F* does not assume equal variances, which
is also why the denominator df are fractional. Kruskal–Wallis is reported
alongside as an assumption-free check, and agrees on all four outcomes.

Effect sizes are small for the three substantive outcomes (ε² = .032–.048) and
large only for prompts per task (ε² = .302), where the difference is largely
mechanical — the interventions' interaction designs require different numbers of
turns. A significant omnibus here says the five conditions are not
interchangeable; it does not say which differ, which is what §4.1–4.4 test.

> **Verification.** These four omnibus tests were recomputed independently from
> `participant_metrics.csv` (pingouin `welch_anova` + scipy `kruskal`) rather
> than carried over from an earlier report. All four reproduce the primary
> notebook's values exactly — *F*, denominator df, and ε² — to the precision
> shown.

Descriptives, M (SD):

| Condition | n | Actual score | Post-estimate | Estimation error |
|---|---|---|---|---|
| AI (baseline) | 187 | 5.57 (1.81) | 9.70 (2.37) | 4.42 (2.42) |
| Reliability cards | 182 | 5.18 (1.63) | 8.23 (2.14) | 3.35 (2.23) |
| Alternatives | 181 | 5.20 (1.53) | 7.70 (2.22) | 2.96 (2.01) |
| Pause points | 184 | 4.49 (2.00) | 7.77 (2.56) | 3.61 (2.45) |
| Reflection task | 183 | 5.52 (1.65) | 9.15 (2.54) | 4.03 (2.48) |

Per-intervention vs baseline (Holm-corrected directional p; * = significant):

**4.1 Metacognitive accuracy** — |post estimate − actual|, lower is better. Baseline M = 4.42.

| Intervention | M | g [95% CI] | Holm p |
|---|---|---|---|
| Reliability cards | 3.35 | −0.46 [−0.67, −0.25] | < .001 * |
| Alternatives | 2.96 | −0.65 [−0.86, −0.44] | < .001 * |
| Pause points | 3.61 | −0.33 [−0.54, −0.13] | .002 * |
| Reflection task | 4.03 | −0.16 [−0.36, +0.05] | .064 |

**4.2 Confidence discrimination** — conf(correct) − conf(incorrect), higher is better.
Baseline M = 2.34 pp.

| Intervention | M | g [95% CI] | Holm p |
|---|---|---|---|
| Reliability cards | 7.74 | +0.50 [+0.29, +0.70] | < .001 * |
| Alternatives | 5.59 | +0.28 [+0.08, +0.49] | .011 * |
| Pause points | 3.14 | +0.08 [−0.13, +0.28] | .462 |
| Reflection task | 2.10 | −0.03 [−0.23, +0.18] | .597 |

**4.3 Prompts per completed task** — expected higher. Baseline M = 1.59.

| Intervention | M | g [95% CI] | Holm p |
|---|---|---|---|
| Reliability cards | 1.61 | +0.03 [−0.17, +0.24] | .381 |
| Alternatives | 1.77 | +0.24 [+0.03, +0.44] | .024 * |
| Pause points | 3.68 | +1.36 [+1.13, +1.59] | < .001 * |
| Reflection task | 2.28 | +0.74 [+0.53, +0.95] | < .001 * |

The pause-points effect is largely mechanical — step-wise replies require extra turns; its prompts
are also the shortest (70 words vs 122–166 elsewhere).

**4.4 Actual score, 0–12** — expected higher; **not supported, direction reversed**.
Baseline M = 5.57. Directional tests all n.s. (Holm p = 1.000); two-sided, three interventions
score significantly *lower*:

| Intervention | M | g [95% CI] | two-sided p |
|---|---|---|---|
| Reliability cards | 5.18 | −0.23 [−0.43, −0.02] | .030 |
| Alternatives | 5.20 | −0.22 [−0.43, −0.02] | .033 |
| Pause points | 4.49 | −0.57 [−0.77, −0.36] | < .001 |
| Reflection task | 5.52 | −0.03 [−0.23, +0.18] | .792 |

## 5. All-pairs comparisons

150 two-sided Welch tests (10 condition pairs × 15 outcomes), Holm-corrected within outcome,
Mann–Whitney robustness, cross-wave pairs flagged. **80 Holm-significant, 36 of them same-wave**
(where the cohort confound cannot operate). Welch and Mann–Whitney disagree on only 9/150.
Full table: `pairwise_condition_tests.csv`.

Same-wave results that sharpen §4:

- **The pause-points performance cost is condition-specific, not a wave artifact:** it scores below
  both other wave-2 interventions (vs alternatives g = −0.40, vs reflection g = −0.56, Holm
  p < .05), mirroring its cross-wave deficit vs baseline (g = −0.57).
- **Alternatives leads on metacognitive accuracy:** smaller error than pause points (g = −0.29) and
  reflection (g = −0.47); better discrimination than reflection (g = +0.30).
- **Interaction cost ordering:** pause points forces the most prompts (vs alternatives g = +1.22,
  vs reflection g = +0.85); reflection is the heaviest workload (TLX vs alternatives g = +0.69, vs
  pause points g = +0.64) and slowest; pause points is worst on usability even among interventions
  (SUS vs alternatives g = −0.37, vs reflection g = −0.64).
- **Trust:** reflection preserves trust better than alternatives (g = +0.61) and pause points
  (g = +0.47).

## 6. Mechanism — calibration and self-estimates

- **Universal overconfidence.** 76–88% of participants overestimate (baseline highest at 88%);
  item-level confidence exceeds accuracy by 26–33 pp in every condition. Calibration curves sit
  below the diagonal in all conditions across all confidence bins.
- **Estimates come down, performance does not go up.** All groups lower their pre→post "with AI"
  estimate, but the three conditions with significant accuracy gains lower it far more
  (reliability −1.59, alternatives −1.94, pause points −2.18 items) than baseline (−0.48) or
  reflection (−0.51).
- **Except for genuine discrimination gains.** Reliability cards and alternatives also improve
  item-level discrimination, and those effects survive adjustment for actual score
  (ΔConf: +5.40 → +5.31 and +3.25 → +3.17).

## 7. UX, workload, and trust

Means by condition with Cronbach's α; two-sided Welch vs baseline, Holm-corrected per scale.

| Scale (α) | ai | ai-rel | alt | pause | refl | Significant vs baseline |
|---|---|---|---|---|---|---|
| SUS 0–100 (.89) | 79.5 | 74.6 | 67.5 | 59.9 | 72.8 | all four lower (pause g = −0.96) |
| UEQ-S −3…+3 (.89) | 1.31 | 1.07 | 0.80 | 0.21 | 0.86 | all four lower (pause g = −0.91) |
| NASA-TLX 0–20 (.69) | 7.67 | 9.22 | 9.52 | 9.67 | 11.68 | all four higher (refl g = +1.21) |
| NFC 1–5 (.89) | 3.53 | 3.42 | 3.43 | 3.46 | 3.37 | none — trait, randomization check ✅ |
| Trust 1–5 (.88) | 3.78 | 3.45 | 3.15 | 3.26 | 3.64 | ai-rel, alt, pause lower (alt g = −0.80) |

Pause points is the most expensive in usability (SUS −19.6), reflection in workload (TLX +4.0).
Trust drops most under alternatives (−0.63), consistent with two-answers-per-prompt exposing AI
inconsistency; self-reported double-checking is accordingly highest there (3.73 vs 3.39 baseline).

**Cost-effectiveness** — metacognitive gain per SUS point sacrificed:

| Intervention | Error reduction | SUS cost | Score cost | Efficiency |
|---|---|---|---|---|
| Reliability cards | −1.07 items | −4.9 | −0.39 | **0.217 items/pt** |
| Alternatives | −1.46 items | −12.0 | −0.37 | 0.121 items/pt |
| Reflection task | −0.39 items | −6.7 | −0.05 | 0.058 items/pt |
| Pause points | −0.81 items | −19.6 | −1.08 | 0.041 items/pt |

Reliability cards delivers 73% of alternatives' metacognitive gain at 41% of its SUS cost, and is
5× more efficient than pause points.

## 8. Behavior and manipulation checks

- **Engagement:** every analyzed participant prompted the AI on all 12 problems. Median dwell per
  problem: 71 s (baseline) → 82/92 s (reliability/alternatives) → 118/123 s (pause/reflection).
- **Exposure:** reliability cards appeared on all 12 problems for 90% of `ai-reliability`
  participants (median 12/12); 72% hid the card at least once. Reflection participants answered a
  median 12/12 pages, writing a median 973 words. The wave-2 intervention gate (prompt must cover
  the task text) passed on 50–67% of tests by condition.
- **AI output volume:** alternatives roughly doubles generated tokens (~57.9k/participant vs
  21.7–30.5k elsewhere) because every prompt yields two replies.
- **Chat resets** concentrate in wave 2 (187–235 per condition vs 0–9 in wave 1) — an interface
  affordance change, not a behavioral difference.
- **Moderators:** condition × moderator OLS finds no robust individual-difference moderation. Two
  uncorrected interactions at p < .05 (pause × NFC on score +0.42, p = .023; alternatives × Trust
  on discrimination +2.95, p = .017) are hypothesis-generating at best — 12 terms across three
  models, R² ≤ .06.

## 9. Sensitivity checks

- Dropping the 5 wave-2 baseline participants changes no effect size by more than |Δg| = 0.02.
- **Within wave 2 only** (no cross-wave confound), the omnibus stays significant for all four
  confirmatory outcomes (actual score Welch F = 14.79, p < .001 — pause points below alternatives
  and reflection). The pause-points performance cost is not a wave artifact.
- The manual wave-1 exclusion list (18 IDs, provenance "less than 30%") is flagged but **not**
  applied; `APPLY_MANUAL_EXCLUSIONS` in the primary notebook reruns everything with it.
- **Independent pre-study corroboration.** A scripted-participant evaluation run before data
  collection (`eval_results/SUMMARY.md`, from `tests/eval_intervention_accuracy.py`) anticipated
  the pause-points accuracy cost: the model alone scored 41.7% under the plain prompt vs 30.6%
  (patient participant) and 13.3% (impatient) under the pause-points prompt.

---

## 10. Exploratory findings

Uncorrected and hypothesis-generating. Numbers from `participant_metrics.csv` (n = 917) and
`task_metrics.csv` (11,004 trials).

**10.1 Reliability cards deflates confidence selectively, not uniformly.** The confidence drop vs
baseline is concentrated on hard items — evidence against pure blanket deflation.

| Intervention | Easy Δconf (>50% correct) | Hard Δconf (<25%) | Selectivity |
|---|---|---|---|
| Reliability cards | −3.3 pp | −15.8 pp | **+12.4** |
| Alternatives | −6.9 pp | −11.6 pp | +4.7 |
| Pause points | −11.9 pp | −10.3 pp | −1.6 |
| Reflection task | −2.1 pp | −1.6 pp | −0.6 |

**10.2 Pronounced hard-easy effect.** Item difficulty spans 18–80% correct. Overconfidence reaches
+42 to +58 pp on hard items vs +8 to +16 pp on easy ones. The gap is largest under reflection
(+49.9) and baseline (+43.6), smallest under reliability cards (+29.1).

**10.3 Dunning-Kruger across all conditions.** Actual score × signed error r = −0.50 to −0.59 in
every condition. No intervention eliminates the gradient.

| Tertile | Score M | Overestimation M | Confidence M |
|---|---|---|---|
| Low (n = 322) | 3.3 | +4.8 items | 70.2 |
| Mid (n = 385) | 5.5 | +3.2 items | 72.6 |
| High (n = 210) | 7.6 | +1.4 items | 75.2 |

**10.4 Trust predicts overestimation, not performance.** Trust × overestimation r = 0.36
(p < .001) and × confidence r = 0.43, but × actual score r = −0.01 to +0.07 within conditions.
Trust amplifies overconfidence rather than facilitating performance.

**10.5 Perceived AI superiority inflates by default — the effective interventions prevent it.**
Pre-study, all conditions believe "AI alone" beats "me without AI" by ~3 items. Post-study that
belief *grows* in baseline and reflection but not in reliability cards or alternatives.

| Condition | Pre | Post | Shift |
|---|---|---|---|
| Baseline | 3.03 | 4.08 | +1.05 *** |
| Reliability cards | 2.68 | 2.71 | +0.03 n.s. |
| Alternatives | 3.09 | 3.05 | −0.01 n.s. |
| Pause points | 3.00 | 3.67 | +0.69 * |
| Reflection | 3.29 | 4.73 | +1.48 *** |

**10.6 Better-than-average bias dissolves under pause points and alternatives.** Self-percentile
placement above the 50th drops from 56–66% pre to **46%** (pause) and **49%** (alternatives) post;
baseline holds at 63%. Self-percentile shift: pause −10.3, alternatives −8.6, baseline −1.2
(n.s.). AI-percentile shows a parallel downgrade (pause 66.4 → 52.7, i.e. −14.0; alternatives
−10.9; baseline +1.5 n.s.).

**10.7 High-confidence errors — the costliest calibration failure.** 34% of all 11,004 trials are
confidence ≥ 70 but wrong. Reliability cards cuts this by ~10 pp while nearly doubling healthy
low-confidence-correct trials.

| Condition | Hi-conf incorrect | Lo-conf correct |
|---|---|---|
| Baseline | 38.8% | 4.3% |
| Reliability cards | **29.0%** | 7.4% |
| Alternatives | 31.0% | 8.0% |
| Pause points | 32.8% | **8.5%** |
| Reflection | 37.1% | 5.8% |

**10.8 Three participant profiles (k-means, k = 3, on score/confidence/error/discrimination).**
Condition × cluster association χ² = 47.5, p < .001.

| Profile | n | Score | Conf | Error | Discrim | Over-represented in |
|---|---|---|---|---|---|---|
| Calibrated skeptics | 291 | 4.93 | 55.1 | 2.27 | **12.04** | reliability 43%, alternatives 40% (vs baseline 19%) |
| Overconfident believers | 321 | 3.97 | 82.5 | **6.11** | 1.55 | baseline 44%, reflection 38% |
| Capable optimists | 305 | **6.73** | 78.1 | 2.48 | −0.59 | reflection 41%, baseline 37% |

**10.9 Prompt length helps only at baseline.** Longer prompts predict higher scores at baseline
(r = 0.21, p = .005) and weakly under alternatives (r = 0.16, p = .030); the effect vanishes
elsewhere (|r| < 0.08). Intervention structure appears to standardize the interaction enough that
individual prompting skill matters less.

**10.10 Reflection effort does not predict outcomes.** Words written (M = 1,118, range
116–2,582) shows no correlation with score (r = −0.06), error (r = 0.11), or discrimination
(r = −0.04). Highest-effort tercile (M = 1,584 words) does not beat the lowest (M = 792) on any
outcome. Whatever value reflection has comes from the task structure, not engagement depth.

**10.11 Frequent AI users and high-NFC participants overestimate more.** AI use frequency ×
overestimation r = 0.12 (p < .001) but × score r = 0.02 (n.s.). NFC × overestimation r = 0.11
(p < .001) but × score r = 0.00. Neither familiarity nor enjoyment of thinking confers calibration.

**10.12 Time-on-task helps only at baseline.** More time predicts better scores (r = 0.18,
p = .014) and less overestimation (r = −0.18, p = .015) at baseline only; both vanish in every
intervention (|r| < 0.12).

**10.13 No within-session learning or confidence drift.** Confidence shows no trend across the
12-problem sequence (r = −0.005, p = .61); accuracy likewise. The one exception is a slight decline
under reliability cards (r = −0.056, p = .009), consistent with gradual updating.

**10.14 No speed-accuracy tradeoff at trial level.** Dwell × correctness |r| < 0.03 in every
condition. Prompts per task also do not predict correctness (differences < 0.05 turns except the
mechanical +0.21 under pause points).

**10.15 Score distribution avoids floor and ceiling.** Nobody scored 0/12 or 12/12; median 5,
IQR 4–7. Pause points is positively skewed (0.74) around its lowered mean of 4.49. 82%
overestimate, 10.5% underestimate, 7.4% are exact. The 68 exact calibrators score higher (M = 6.0
vs 5.2) with lower confidence (M = 62 vs 72).

**10.16 Age, gender, and education are near-null.** Age × score r = −0.03 (n.s.), × overestimation
r = 0.07 (p = .043). Score by gender: women 5.16, men 5.22 (n = 466/442). Education spans
M = 5.01–5.61 across six levels with no ordered trend.

**10.17 UX scales are tightly coupled to each other — and to overconfidence — mainly at baseline;
every intervention loosens both.** Pooled (n = 917), SUS, UEQ-pragmatic, and Trust form one
evaluative cluster (r = .61–.74; TLX opposes it, r = −.22 to −.34; NFC is independent of all,
r ≤ .24 — trait check ✅). Within conditions, both couplings are strongest in plain AI chat:

| Pearson r | ai | ai-rel | alt | pause | refl |
|---|---|---|---|---|---|
| SUS × Trust | **.74** | .59 | .58 | .61 | .54 |
| UEQ-prag × Trust | **.70** | .57 | .57 | .62 | .56 |
| UEQ-prag × TLX | **−.44** | −.28 | −.22 | −.29 | −.18 |
| Trust × signed estimation error | **.49** | .38 | .37 | .36 | .35 |
| SUS × signed estimation error | **.43** | .26 | .24 | .22 | .20 |

Twelve of 60 Fisher z comparisons of intervention r vs baseline r reach p < .05 (3 expected by
chance), and all twelve are attenuations; only SUS × Trust under reflection survives Holm across
the 60 tests (p = .0008), so read this as one consistent pattern, not twelve effects. It is not a
wave artifact: ai-reliability (wave 1, concurrent with baseline) attenuates as much as the wave-2
conditions. No scale correlates with actual score in any condition (all |r| ≤ .18) — satisfaction
measures track overconfidence, not competence (generalizing 10.4 from Trust to SUS and UEQ), and
every intervention roughly halves that link. One further decoupling: TLX × mean confidence is
−.38 at baseline (felt workload lowers confidence) but +.01 under reliability cards, where
confidence appears anchored to the card information rather than felt effort.

---

## 11. Limitations

1. **Wave confound.** Conditions were not randomized concurrently; recruitment period is partially
   confounded with condition (§2, §9).
2. **The actual-score reversal (§4.4) is post-hoc.** Directional confirmatory tests follow the
   per-wave preregistrations; the two-sided reading should be treated as exploratory.
3. **Prompts-per-task differences are partly built in** to the interventions' interaction designs.
4. **Self-estimates are integer-valued (0–12)**, limiting calibration resolution.
5. **12 trials per participant** makes individual-level metacognition estimates noisy; all
   item-level measures are group-level only (see [`METHODS.md`](METHODS.md) §6).
6. **Section 10 is uncorrected.** Treat as hypothesis-generating.
