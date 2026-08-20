# Analysis Process

Step-by-step description of the full analysis pipeline for the MET-AI
Interventions study (5 conditions, 925 participants, 12 four-option
planning problems). Each step names the deliverable(s) that implement it and
the key decisions made.

---

## 1. Data collection and storage

- Participants recruited on Prolific in two waves:
  - **Wave 1** (Jul 2026): `ai` (baseline) and `ai-reliability` (reliability
    cards).
  - **Wave 2** (Aug 2026): `alternatives`, `pause-points`, and
    `reflection-task`.
- Each participant's full session is stored as a JSON record in
  `data_analysis/results/data/final_data/`, one file per condition.
- Each record contains: `participantId`, `condition`, `tasks` (with per-task
  answer and confidence), `answerResults` (backend-scored boolean per item),
  `correctAnswers` (total), interaction log, messages, timestamps, and
  post-task questionnaire responses.

## 2. Data loading and integrity audit

**Deliverable:** `deep_analysis_notebook.ipynb` (Part 1, modules 1-4)

- Load all five condition JSONs (925 records total).
- **Scoring verification:** recompute every answer against the canonical answer
  key (`src/customizations/questions/correct_answers.py`) and compare to the
  backend's stored `answerResults` -- 0 mismatches across 11,100 scored items.
- **Internal consistency:** check that `answerResults` has exactly 12 boolean
  entries per participant, and that the sum equals the stored `correctAnswers`
  field (925/925 match).
- **Deduplication:** 38 participants took part in two conditions across waves;
  `final_data` keeps each participant's earliest run only.

## 3. Variable construction and scoring

**Deliverable:** `deep_analysis_notebook.ipynb` (modules 5-7)

- **Task-level variables** (one row per participant per item, 12 items):
  answer, correctness, confidence (0-100), dwell time (seconds), prompts on
  task.
- **Questionnaire scoring:**
  - SUS (System Usability Scale, 0-100): standard 10-item scoring with
    alternating-item reversal.
  - UEQ-S (User Experience Questionnaire Short): overall, pragmatic, and
    hedonic subscales (-3 to +3).
  - NASA-TLX (Task Load Index): unweighted mean of 6 subscales (0-20).
  - NFC (Need for Cognition): mean of 6 items (1-5 scale, two reversed).
  - Trust / TSQ: mean of trust items (1-5 scale).
- **Behavioral measures:**
  - Total prompts, prompts per task, mean prompt word count, pasted-task share.
  - AI output volume: assistant output tokens, reasoning tokens.
  - Chat resets, intervention gate tests and matches, reliability cards
    presented/hidden, reflection pages answered and word count.
  - Completion time (seconds/minutes) from interaction log timestamps.
- **Participant-level outcomes:**
  - `actual_score` (0-12): sum of correct answers.
  - `mean_confidence`, `mean_conf_correct`, `mean_conf_incorrect`: average
    confidence overall and split by correctness.
  - `confidence_discrimination`: mean confidence on correct minus mean
    confidence on incorrect items (higher = better metacognitive sensitivity).
  - `pre_with_ai`, `post_with_ai` (0-12): pre- and post-study self-estimates
    of performance "with AI help".
  - `pre_without_ai`, `post_without_ai`: estimates for "without AI".
  - `pre_ai_alone`, `post_ai_alone`: estimates for "AI alone".
  - `signed_estimation_error`: post_with_ai minus actual_score (positive =
    overestimation).
  - `absolute_estimation_error`: |post_with_ai minus actual_score|.
  - Pre/post self-percentile and AI-percentile (0-100).
  - All exported to `notebook_analysis_output/participant_metrics.csv` (917
    rows, 73+ columns) and `task_metrics.csv` (11,004 trials).

## 4. Exclusion criteria

**Deliverable:** `deep_analysis_notebook.ipynb` (module 8)

- **Attention checks:** exclude participants failing more than 1 of 4
  embedded attention-check items (7 excluded).
- **Completeness:** exclude participants who answered fewer than 12 problems
  (0 excluded).
- **Speed screen:** exclude participants finishing in under 10 minutes (1
  excluded).
- **Manual list:** a wave-1 manual exclusion list (18 IDs, provenance "less
  than 30%") is flagged but NOT applied -- available via a
  `APPLY_MANUAL_EXCLUSIONS` switch for sensitivity analysis.
- **Final sample:** 917 of 925 participants (8 excluded).

## 5. Descriptive statistics and demographics

**Deliverable:** `deep_analysis_notebook.ipynb` (module A); `analysis_S1.Rmd`
(Step 5); `analysis_S1.py` (Step 5)

- Sample demographics: age (M, SD, range), gender distribution, education
  level, AI use frequency, all tabulated by condition.
- Randomization checks: one-way ANOVAs on demographics and pre-study
  estimates across conditions (confirm no significant baseline differences).
- Completion time summaries by condition (median, IQR).
- Score and confidence distributions: histograms, skewness, kurtosis.

## 6. Omnibus tests across all five conditions

**Deliverable:** `deep_analysis_notebook.ipynb` (module E); `analysis_S1.Rmd`
(Step 6); `analysis_S1.py` (Step 6)

- **Welch's ANOVA** (does not assume equal variances) on each primary outcome:
  - Actual score (0-12)
  - Absolute estimation error (|post-estimate - actual|)
  - Confidence discrimination (conf_correct - conf_incorrect)
  - Prompts per completed task
- **Kruskal-Wallis** H-tests as non-parametric robustness checks, with
  epsilon-squared (epsilon^2) effect sizes.
- All four outcomes show significant omnibus differences (p < .001).

## 7. Pairwise intervention-vs-baseline comparisons

**Deliverable:** `deep_analysis_notebook.ipynb` (module F); `analysis_S1.Rmd`
(Step 6); `analysis_S1.py` (Step 6); `hypothesis_tests.R`

- For each of the 4 interventions vs the `ai` baseline:
  - **Welch's t-test** (unequal variance).
  - **Hedges' g** with small-sample correction (J factor) and 95% CI.
  - **Holm correction** within each outcome family (4 tests per family).
  - **Directional tests** as preregistered (one-sided in the predicted
    direction: lower error, higher discrimination, higher score).
  - **Two-sided tests** reported alongside (important because the actual-score
    direction reversed).
- **R replication:** `hypothesis_tests.R` (base R, no packages) independently
  reproduces the Python results exactly; console output in
  `hypothesis_tests_R_output.txt`.

## 8. All-pairs pairwise comparisons

**Deliverable:** `pairwise_tests_notebook.ipynb`

- Two-sided Welch t-tests for **all 10 condition pairs** on 15 outcomes (150
  tests total).
- Holm correction within each outcome (10 tests per outcome).
- Mann-Whitney U tests as non-parametric robustness checks (Welch and
  Mann-Whitney conclusions disagree on only 9 of 150 tests).
- Cross-wave pairs flagged to distinguish within-wave (confound-free) from
  cross-wave results.
- Effect-size matrices (Hedges' g) exported for visualization.
- Key finding: 80 of 150 tests are Holm-significant; 36 of those are between
  same-wave conditions, confirming that the main findings hold without the
  cohort confound.

## 9. Item-level accuracy and confidence calibration

**Deliverable:** `deep_analysis_notebook.ipynb` (modules G-H); `analysis_S1.Rmd`
(Step 7); `analysis_S1.py` (Step 7)

- **Item difficulty:** proportion correct for each of the 12 problems (range:
  18% to 80%).
- **Calibration curves:** binned confidence vs proportion correct per
  condition.
- **Trial-level metacognitive sensitivity:**
  - Confidence discrimination (delta-conf) = mean conf correct - mean conf
    incorrect, per participant.
  - AUROC2 (type-2 area under ROC): the probability that a correct trial
    has higher confidence than an incorrect trial.
  - Brier score: mean squared error of confidence vs binary correctness.
  - Calibration slope and intercept from logistic regression of correctness
    on confidence.
- All computed per participant; condition comparisons via Welch t and
  Hedges' g.

## 10. Rahnev (2025) metacognition metrics

**Deliverable:** `rahnev_metrics_notebook.ipynb`;
`METACOGNITION_METRICS_RATIONALE.md`

- Implements all 17 metacognition measures from Rahnev (2025, *Nature
  Communications*).
- **Applicability gate:** only 4 of 17 measures are computable for this study
  (no SDT stimulus structure; only 12 trials):
  - delta-Conf (= the study's confidence_discrimination) -- recommended
    primary.
  - AUC2 (type-2 AUROC) -- robustness check.
  - Gamma (Goodman-Kruskal correlation).
  - Phi (Pearson correlation between confidence and correctness).
- SDT-based measures (meta-d', M-ratio, M-diff, etc.) validated on
  simulated observers to confirm the implementation is correct, then marked
  as not applicable.
- Accuracy-adjusted condition effects (partial correlation controlling for
  actual score) confirm reliability cards and alternatives still show genuine
  discrimination gains beyond what their score differences explain.

## 11. Post-task questionnaires

**Deliverable:** `deep_analysis_notebook.ipynb` (module L); `analysis_S1.Rmd`
(Step 8); `analysis_S1.py` (Step 8)

- Condition comparisons on SUS, UEQ-S (overall/pragmatic/hedonic), NASA-TLX,
  NFC, and Trust.
- Cronbach's alpha for each scale on the analysis sample.
- Welch t-tests vs baseline, Holm-corrected per scale.
- NFC serves as a randomization check (trait measure, should not differ) --
  no significant differences confirmed.
- Key finding: every intervention worsens user experience relative to
  baseline; pause points is the costliest, reflection the heaviest workload.

## 12. Mediation analysis

**Deliverable:** `analysis_S1.Rmd` (Step 9); `analysis_S1.py` (Step 9)

- **Parallel mediation model** (4 condition dummies with ai as reference):
  - Condition -> Trust + Hedonic UEQ -> Overestimation.
  - 5,000 bootstrap resamples for indirect-effect CIs.
- Tests whether the metacognitive improvement is mediated by changes in trust
  and user experience.
- Implemented via lavaan (R) and statsmodels OLS path models (Python).

## 13. Exploratory moderator analyses

**Deliverable:** `deep_analysis_notebook.ipynb` (module N); `analysis_S1.Rmd`
(Step 6, moderator models)

- Condition x moderator OLS models testing whether individual differences
  moderate intervention effects:
  - Moderators tested: NFC, Trust, AI use frequency, age.
  - Outcomes: actual score, overestimation, confidence discrimination.
- No robust moderation found (12 interaction terms tested; model R-squared
  <= .06).

## 14. Figures

**Deliverable:** `analysis_S1.Rmd` (Step 10); `analysis_S1.py` (Step 10);
`deep_analysis_notebook.ipynb` (modules C-D, F)

- Raincloud plots (violin + boxplot + jitter) for primary outcomes by
  condition.
- Bar charts with error bars (95% CI) for questionnaire scales.
- Scatter plots for key bivariate relationships (trust x overestimation,
  confidence x score).
- Effect-size forest plots (Hedges' g with 95% CI, one row per intervention).
- Condition colour palette: ai=#2a78d6, ai-reliability=#eb6834,
  alternatives=#1baf7a, pause-points=#eda100, reflection-task=#e87ba4
  (colorblind-safe).

## 15. Preregistered directional hypothesis tests and verdicts

**Deliverable:** `analysis_S1.Rmd` (Step 11); `analysis_S1.py` (Step 11);
`hypothesis_tests.R`

- For each intervention, the preregistered hypothesis is: "the intervention
  improves performance and/or metacognition vs baseline."
- **Performance**: directional Welch t (predicted: higher score). Not
  supported for any intervention; two-sided test reveals reversed direction
  for reliability cards, alternatives, and pause points.
- **Metacognition**: directional Welch t on estimation error (predicted:
  lower) and confidence discrimination (predicted: higher).
- **Holm correction** within each family (4 tests).
- **Verdict per intervention** (IU = Inference upon the Inequalities
  framework):
  - Reliability cards: **supported via metacognition** (error g = -0.46,
    discrimination g = +0.50).
  - Alternatives: **supported via metacognition** (error g = -0.65,
    discrimination g = +0.28).
  - Pause points: **partially supported** (error g = -0.33 only).
  - Reflection task: **not supported** (error p = .064, discrimination n.s.).
- **Jonckheere-Terpstra trend test** for ordered patterns across conditions.

## 16. Wave sensitivity analyses

**Deliverable:** `deep_analysis_notebook.ipynb` (module O); `analysis_S1.Rmd`
(Step 12); `analysis_S1.py` (Step 12); `pairwise_tests_notebook.ipynb`
(within-wave-2 tests)

- **Drop wave-2 baseline participants** (n = 5): re-run all confirmatory tests
  -- no effect size changes by more than |delta-g| = 0.02.
- **Within-wave-2 only** (alternatives vs pause-points vs reflection-task):
  Welch ANOVA remains significant for all four confirmatory outcomes (e.g.
  actual score F = 14.79, p < .001), confirming the pause-points performance
  cost and the alternatives metacognition advantage are not driven by the
  wave difference.
- **Manual exclusion list** sensitivity: available via notebook switch but not
  applied in the primary analysis.

## 17. Exploratory deep-dive

**Deliverable:** `EXPLORATORY_FINDINGS.md`

- **Selective confidence deflation:** reliability cards reduces confidence
  15.8 pp on hard items vs only 3.3 pp on easy items (not blanket deflation).
- **Trust-overestimation link:** trust correlates r = 0.36 with overestimation
  but r approximately 0 with actual score -- trust amplifies overconfidence.
- **Perceived AI superiority inflation:** baseline and reflection increase
  belief that "AI outperforms me" post-study; reliability cards and
  alternatives prevent this inflation.
- **Better-than-average bias dissolution:** self-percentile drops below 50%
  post-study under pause points and alternatives.
- **Cost-effectiveness ranking:** reliability cards is 5x more efficient than
  pause points (0.217 vs 0.041 error-items per SUS point).
- **Participant profiles (cluster analysis):** three clusters -- "calibrated
  skeptics" (over-represented in reliability cards/alternatives),
  "overconfident believers" (over-represented in baseline/reflection),
  "capable optimists" (highest scores).
- **Dunning-Kruger pattern:** r = -0.50 to -0.59 (actual score x
  overestimation) across all conditions.
- **High-confidence errors:** 38.8% of baseline trials are high-confidence
  (>= 70) but incorrect; reliability cards reduces this to 29.0%.
- **Prompt length predicts performance at baseline only** (r = 0.21),
  suggesting interventions compensate for prompt quality.
- **Reflection effort (word count) does not predict outcomes** -- the
  mechanism is the task structure, not engagement depth.
- **Frequent AI users overestimate more** (r = 0.12, p < .001) without
  performing better.
- **No within-session learning or confidence drift** (r approximately 0 with
  presentation position).

## 18. Summary statistics and export

**Deliverable:** `analysis_S1.Rmd` (Step 13); `analysis_S1.py` (Step 13);
`deep_analysis_notebook.ipynb` (modules P-Q)

- Compact reference card with all key numbers for quick look-up.
- Export of prepared tables to `notebook_analysis_output/`:
  - `participant_metrics.csv` (917 rows, 73+ columns)
  - `task_metrics.csv` (11,004 trials)
  - `pairwise_condition_tests.csv` (150 tests)
  - `omnibus_tests.csv`
  - `exclusion_funnel.csv`
  - `open_text_answers.csv`
  - `prompts.csv`
  - Rahnev per-participant and condition-test CSVs

---

## Deliverable index

| Step(s) | Deliverable | Language |
|---|---|---|
| 2-6, 9, 11, 13-16, 18 | `deep_analysis_notebook.ipynb` | Python |
| 1-18 | `analysis_S1.Rmd` | R |
| 1-18 | `analysis_S1.py` / `analysis_S1.ipynb` | Python |
| 7, 15 | `hypothesis_tests.R` | R |
| 8 | `pairwise_tests_notebook.ipynb` | Python |
| 10 | `rahnev_metrics_notebook.ipynb` | Python |
| 17 | `EXPLORATORY_FINDINGS.md` | -- |
| -- | `FINDINGS.md` | -- |
| -- | `PRELIMINARY_RESULTS.md` | -- |
| 10 | `METACOGNITION_METRICS_RATIONALE.md` | -- |
