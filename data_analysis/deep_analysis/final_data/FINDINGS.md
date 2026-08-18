# MET-AI Interventions — Results Analysis (Final Dataset)

Findings from the merged final dataset (`data_analysis/results/data/final_data/`), covering all
five conditions of the study. Every number in this document is produced by
[`deep_analysis_notebook.ipynb`](deep_analysis_notebook.ipynb) in this folder (§3.5 additionally
by [`pairwise_tests_notebook.ipynb`](pairwise_tests_notebook.ipynb)); run the notebooks top to
bottom to regenerate them.

**Analysis conventions.** Analysis sample n = 917 (see §1). Group comparisons are Welch's *t*
against the `ai` baseline with Hedges' *g* (95% CI) and Holm correction within each outcome
family; confirmatory p-values are directional, following the per-wave preregistrations, with
two-sided p reported where it changes the conclusion. Omnibus tests are Welch's ANOVA and
Kruskal–Wallis (ε²). α = .05.

---

## 1. Dataset and sample

| Condition | Intervention | Collected | Loaded | Analyzed |
|---|---|---|---|---|
| `ai` | Plain AI chat (baseline) | Jul 2026 (+5 in Aug) | 189 | 187 |
| `ai-reliability` | Per-task AI reliability cards | Jul 2026 | 184 | 182 |
| `alternatives` | Two alternative AI replies per prompt | Aug 2026 | 183 | 181 |
| `pause-points` | Step-by-step AI replies with pause points | Aug 2026 | 184 | 184 |
| `reflection-task` | Post-task reflection page after every problem | Aug 2026 | 185 | 183 |

925 unique participants loaded; 8 excluded (7 failed ≥2 of 4 embedded attention checks, 1
finished in under 10 minutes), leaving **917 analyzed**. Mean age 35.7 years (SD 10.9, range
18–78); gender is close to balanced in every condition (45–54% women); participants are frequent
AI users (mean 5.7–6.0 on a 1–7 use-frequency scale). Median completion time: 30.6 / 35.2 / 36.8
/ 41.5 / 69.7 minutes for baseline / reliability / alternatives / pause points / reflection —
the reflection condition takes roughly twice as long as the baseline.

**Cohort structure (important caveat).** The baseline and reliability-cards conditions were
collected in July 2026 (wave 1), the other three interventions in August 2026 (wave 2), with only
5 baseline participants collected during wave 2. Every wave-2-vs-baseline comparison is therefore
also a comparison across recruitment periods; §8 shows the results are insensitive to the checks
available, but the confound cannot be fully removed by analysis.

## 2. Data integrity

* **Scoring is verified.** Recomputing every answer against the canonical key
  (`customizations/questions/correct_answers.py`, the module the backend imported at runtime)
  reproduces the backend's stored `answerResults` exactly: **0 mismatches across 11,100 scored
  items**.
* **The convenience CSVs' correctness columns are defective.** `export_condition_csvs.py`
  hard-codes an answer key that differs from the canonical key on **8 of 12 items**, so the
  `*_correct`, `n_correct` and `metacog_sensitivity` columns in `final_data/*.csv` are wrong and
  are not used anywhere in this analysis. All metrics derive from the JSON exports.
* **Repeated participation is already handled.** 38 participants took part in two conditions
  across the waves. `final_data` keeps exactly one record per participant — always the earliest
  run (verified against the raw wave exports) — so their analyzed data is their first, clean
  exposure; `repeated.csv` documents the dropped later runs.

## 3. Confirmatory outcomes

Omnibus differences across the five conditions are significant for all four outcome families:

| Outcome | Welch F (df) | p | Kruskal–Wallis ε² |
|---|---|---|---|
| Metacognitive accuracy \|post estimate − actual\| | 11.87 (4, 455.5) | < .001 | .038 |
| Confidence discrimination | 8.08 (4, 452.0) | < .001 | .032 |
| Prompts per completed task | 54.06 (4, 447.9) | < .001 | .302 |
| Actual score | 9.44 (4, 455.4) | < .001 | .048 |

Per-intervention effects vs the `ai` baseline (Holm-corrected directional p; * = significant):

### 3.1 Metacognitive accuracy — |post-study estimate − actual score| (lower is better)

Baseline mean 4.42 items.

| Intervention | Mean | g [95% CI] | Holm p |
|---|---|---|---|
| Reliability cards | 3.35 | −0.46 [−0.67, −0.25] | < .001 * |
| Alternatives | 2.96 | −0.65 [−0.86, −0.44] | < .001 * |
| Pause points | 3.61 | −0.33 [−0.54, −0.13] | .002 * |
| Reflection task | 4.03 | −0.16 [−0.36, +0.05] | .064 |

### 3.2 Confidence discrimination — mean confidence on correct minus incorrect items (higher is better)

Baseline mean 2.34 pp.

| Intervention | Mean | g [95% CI] | Holm p |
|---|---|---|---|
| Reliability cards | 7.74 | +0.50 [+0.29, +0.70] | < .001 * |
| Alternatives | 5.59 | +0.28 [+0.08, +0.49] | .011 * |
| Pause points | 3.14 | +0.08 [−0.13, +0.28] | .462 |
| Reflection task | 2.10 | −0.03 [−0.23, +0.18] | .597 |

### 3.3 Prompts per completed task (expected higher)

Baseline mean 1.59.

| Intervention | Mean | g [95% CI] | Holm p |
|---|---|---|---|
| Reliability cards | 1.61 | +0.03 [−0.17, +0.24] | .381 |
| Alternatives | 1.77 | +0.24 [+0.03, +0.44] | .024 * |
| Pause points | 3.68 | +1.36 [+1.13, +1.59] | < .001 * |
| Reflection task | 2.28 | +0.74 [+0.53, +0.95] | < .001 * |

The very large pause-points effect is largely mechanical: its step-wise replies require extra
user turns (its prompts are also the shortest — 70 words vs 122–166 elsewhere).

### 3.4 Actual score, 0–12 (expected higher — **not supported; direction reversed**)

Baseline mean 5.57. No intervention improves accuracy; under the preregistered directional test
all are n.s. (Holm p = 1.000), but **two-sided, three interventions score significantly *lower***:

| Intervention | Mean | g [95% CI] | two-sided p |
|---|---|---|---|
| Reliability cards | 5.18 | −0.23 [−0.43, −0.02] | .030 |
| Alternatives | 5.20 | −0.22 [−0.43, −0.02] | .033 |
| Pause points | 4.49 | −0.57 [−0.77, −0.36] | < .001 |
| Reflection task | 5.52 | −0.03 [−0.23, +0.18] | .792 |

### 3.5 Pairwise comparisons between all conditions

[`pairwise_tests_notebook.ipynb`](pairwise_tests_notebook.ipynb) runs two-sided Welch t-tests for
**all 10 condition pairs** on 15 outcomes (150 tests, Holm-corrected within outcome, Mann–Whitney
robustness checks, cross-wave pairs flagged). 80 tests are Holm-significant — 36 of them between
same-wave conditions, where the cohort confound cannot operate. The same-wave results sharpen the
baseline comparisons of §3.1–3.4:

* **The pause-points performance cost is condition-specific, not a wave artifact:** pause points
  scores below the two other wave-2 interventions (vs alternatives g = −0.40, vs reflection
  g = −0.56, both Holm p < .05), mirroring its cross-wave deficit vs baseline (g = −0.57).
* **Alternatives leads the interventions on metacognitive accuracy:** smaller estimation error
  than pause points (g = −0.29) and reflection (g = −0.47), and better confidence discrimination
  than reflection (g = +0.30) — all same-wave.
* **Interaction cost ordering (same-wave):** pause points forces the most prompts (vs
  alternatives g = +1.22, vs reflection g = +0.85); reflection is the heaviest workload
  (TLX vs alternatives g = +0.69, vs pause points g = +0.64) and the slowest, while pause points
  is the worst on usability even among interventions (SUS vs alternatives g = −0.37, vs
  reflection g = −0.64).
* **Trust (same-wave):** reflection preserves trust better than alternatives (g = +0.61) and
  pause points (g = +0.47).
* Welch and Mann–Whitney conclusions disagree on only 9 of 150 tests at the Holm-corrected
  threshold; the full test table is exported as `pairwise_condition_tests.csv`.

## 4. Calibration detail

* Everyone is overconfident: 76–88% of participants overestimate their score (baseline highest at
  88%), and item-level confidence exceeds accuracy by 26–33 pp in every condition. Calibration
  curves sit below the diagonal in all conditions across all confidence bins.
* All groups lower their estimates from pre to post, but the three conditions with significant
  metacognitive-accuracy gains lower their "with AI" estimate far more (reliability −1.59,
  alternatives −1.94, pause points −2.18 items) than baseline (−0.48) or reflection (−0.51).
  **The accuracy of self-estimates improves mostly because estimates come down, not because
  performance goes up** — with the caveat that reliability cards and alternatives also genuinely
  improve item-level discrimination (§3.2).

## 5. Usability, workload, experience, and trust

Means by condition (baseline / reliability / alternatives / pause points / reflection), with
Cronbach's α on the analysis sample. Two-sided Welch tests vs baseline, Holm-corrected per scale:

| Scale (α) | ai | ai-rel | alt | pause | refl | Significant vs baseline |
|---|---|---|---|---|---|---|
| SUS 0–100 (.89) | 79.5 | 74.6 | 67.5 | 59.9 | 72.8 | all four lower (pause g = −0.96) |
| UEQ-S −3…+3 (.89) | 1.31 | 1.07 | 0.80 | 0.21 | 0.86 | all four lower (pause g = −0.91) |
| NASA-TLX 0–20 (.69) | 7.67 | 9.22 | 9.52 | 9.67 | 11.68 | all four higher (refl g = +1.21) |
| NFC 1–5 (.89) | 3.53 | 3.42 | 3.43 | 3.46 | 3.37 | none (trait — good randomization check) |
| Trust 1–5 (.88) | 3.78 | 3.45 | 3.15 | 3.26 | 3.64 | ai-rel, alt, pause lower (alt g = −0.80) |

**Every intervention costs user experience and adds workload.** Pause points is the most
expensive in usability (SUS 59.9, a 19.6-point drop), reflection in workload (TLX +4.0).
Trust in the AI drops most under alternatives (−0.63), consistent with its two-answers-per-prompt
design exposing AI inconsistency; self-reported double-checking of AI answers is accordingly
highest under alternatives (3.73 vs 3.39 baseline on a 1–5 item).

## 6. Behavior and manipulation checks

* **Engagement:** every analyzed participant prompted the AI on all 12 problems. Median dwell per
  problem rises from 71 s (baseline) through 82/92 s (reliability/alternatives) to 118/123 s
  (pause points/reflection).
* **Exposure:** reliability cards appeared on all 12 problems for 90% of `ai-reliability`
  participants (median 12/12); 72% hid the card at least once. Reflection participants answered a
  median of 12/12 reflection pages, writing a median of 973 words. The wave-2 intervention gate
  (prompt must cover the task text) passed on 50–67% of tests depending on condition.
* **AI output volume:** the alternatives condition roughly doubles generated tokens
  (~57.9k per participant vs ~21.7–30.5k elsewhere) because every prompt yields two replies.
* **Chat resets** concentrate in wave 2 (187–235 per condition vs 0–9 in wave 1), consistent with
  an interface affordance change rather than a behavioral difference.

## 7. Moderators (exploratory)

Condition × moderator OLS models find no robust individual-difference moderation. Two uncorrected
interactions at p < .05 — pause-points × Need for Cognition on actual score (+0.42, p = .023) and
alternatives × Trust on discrimination (+2.95, p = .017) — are hypothesis-generating at best
(12 interaction terms tested across three models; model R² ≤ .06).

## 8. Sensitivity checks

* Dropping the 5 wave-2 baseline participants changes no effect size by more than |Δg| = 0.02.
* Comparing only the three wave-2 interventions among themselves (no cross-wave confound), the
  omnibus remains significant for all four confirmatory outcomes (e.g. actual score Welch
  F = 14.79, p < .001 — pause points scores below alternatives and reflection), so the
  pause-points performance cost is not explained by the wave difference.
* The manual wave-1 exclusion list (18 IDs, provenance "less than 30%") is flagged but not
  applied; the notebook has a switch (`APPLY_MANUAL_EXCLUSIONS`) to rerun everything with it
  applied as an additional sensitivity analysis.

## 9. Summary

1. **Metacognition improves, performance does not.** Reliability cards and alternatives make
   participants meaningfully better at judging their own performance (global estimates and
   item-level discrimination); pause points improves global estimates only. No intervention
   raises actual task accuracy, and pause points *lowers* it (g = −0.57 two-sided).
2. **The mechanism looks like deflated confidence more than insight** — post-study estimates drop
   by 1.6–2.2 items in the effective interventions — except that reliability cards and
   alternatives also sharpen item-level discrimination, which deflation alone cannot produce.
3. **Every intervention has a UX price:** lower SUS and UEQ-S, higher workload, and (for
   reliability cards, alternatives, pause points) lower trust in the AI. Pause points buys its
   modest metacognitive gain at the largest usability and performance cost; alternatives delivers
   the largest calibration gain at a doubled AI-token cost and the largest trust drop.
4. **Data quality is solid** after verification (§2), with one standing defect: the correctness
   columns in the exported CSVs use a wrong answer key and must not be analyzed until
   `export_condition_csvs.py` is fixed and the CSVs regenerated.

## 10. Limitations

* Conditions were not randomized concurrently: wave (recruitment period) is partially confounded
  with condition (§1, §8).
* Directional confirmatory tests follow the per-wave preregistrations; the actual-score reversal
  (§3.4) is a two-sided, post-hoc reading and should be treated as exploratory.
* Prompts-per-task differences are partly built into the interventions' interaction designs.
* Self-estimate items are integer-valued (0–12), limiting the resolution of calibration measures.
