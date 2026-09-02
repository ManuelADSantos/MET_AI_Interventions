# Methods — MET-AI Interventions (Final Dataset)

Pipeline, variable definitions, and measure-selection decisions. Results in
[`RESULTS.md`](RESULTS.md).

---

## 1. Design

925 Prolific participants solved 12 four-option planning/organizing problems with an AI chat
assistant, rating confidence (0–100) per problem and estimating their performance before and after,
in one of five conditions:

| Condition | Manipulation |
|---|---|
| `ai` | Plain AI chat (baseline) |
| `ai-reliability` | Per-task AI reliability card + evaluation strategies |
| `alternatives` | Two parallel AI replies per prompt |
| `pause-points` | Step-by-step AI replies with pause points |
| `reflection-task` | Reflection page after every problem |

Collected in two waves: wave 1 (Jul 2026) = `ai` + `ai-reliability`; wave 2 (Aug 2026) = the other
three. Hypothesis: interventions improve **performance and/or metacognition** vs baseline.

## 2. Data source and integrity

Raw records: one JSON per condition in `data_analysis/raw_data/data/final_data/`, each holding
`participantId`, `condition`, `tasks` (per-task answer + confidence), `answerResults` (backend-scored
booleans), `correctAnswers`, interaction log, messages, timestamps, and questionnaire responses.

Verification performed before any analysis (results in `RESULTS.md` §3):

1. **Scoring** — recompute every answer against the canonical key
   (`src/customizations/questions/correct_answers.py`, the module the backend imported at runtime)
   and diff against stored `answerResults`.
2. **Internal consistency** — `answerResults` has exactly 12 booleans per record and sums to
   `correctAnswers`.
3. **Deduplication** — 38 participants appeared in two conditions across waves; `final_data` keeps
   each participant's earliest run. `repeated.csv` documents dropped runs.

All analysis metrics derive from the JSONs. The convenience CSVs are a derived view; their
correctness columns were rebuilt after a defect was found (details in `RESULTS.md` §3).

## 3. Exclusions

| Rule | Excluded |
|---|---|
| Failed > 1 of 4 embedded attention checks | 7 |
| Answered < 12 problems | 0 |
| Completed in < 10 minutes | 1 |
| **Analysis sample** | **917 of 925** |

A wave-1 manual exclusion list (18 IDs, provenance "less than 30%", undocumented) is **not**
applied; `APPLY_MANUAL_EXCLUSIONS` in the primary notebook reruns everything with it as a
sensitivity analysis.

## 4. Variables

**Trial level** (`task_metrics.csv`, 11,004 rows = 917 × 12): `answer`, `correct`, `confidence`
(0–100), `dwell_seconds`, `prompts_on_task`, `authored_order`, `display_index`.

**Participant level** (`participant_metrics.csv`, 917 rows):

| Variable | Definition |
|---|---|
| `actual_score` | Correct answers, 0–12 |
| `mean_confidence` | Mean confidence across 12 items |
| `confidence_discrimination` | conf(correct) − conf(incorrect), in pp — **primary item-level metacognition outcome** |
| `pre_with_ai` / `post_with_ai` | Self-estimated score with AI help, 0–12, before/after |
| `pre_without_ai` / `post_without_ai` | Same, estimated without AI |
| `pre_ai_alone` / `post_ai_alone` | Estimated score for the AI working alone |
| `signed_estimation_error` | `post_with_ai − actual_score` (positive = overestimation) |
| `absolute_estimation_error` | \|`post_with_ai − actual_score`\| — **primary global metacognition outcome** |
| `pre/post_self_percentile`, `pre/post_ai_percentile` | Social-comparison estimates, 0–100 |
| `prompts_per_task`, `mean_prompt_words`, `pasted_task_share` | Prompting behavior |
| `assistant_output_tokens`, `assistant_reasoning_tokens` | AI output volume |
| `cards_hidden`, `reflection_pages_answered`, `reflection_words`, `gate_matched` | Manipulation exposure |
| `completion_minutes` | From interaction-log timestamps |

**Questionnaire scoring:** SUS (0–100, standard 10-item alternating reversal); UEQ-S (−3…+3;
overall, pragmatic, hedonic); NASA-TLX (unweighted mean of 6 subscales, 0–20); NFC (mean of 6
items, 1–5, two reversed); Trust/TSQ (mean, 1–5). Cronbach's α reported per scale in `RESULTS.md` §7.

## 5. Statistical approach

| Analysis | Method |
|---|---|
| Omnibus across five conditions | Welch's ANOVA (unequal variance) + Kruskal–Wallis with ε² |
| Intervention vs baseline | Welch's *t*, Hedges' *g* with small-sample correction (J), 95% CI |
| Multiplicity | Holm correction within each outcome family |
| Directionality | Confirmatory tests one-sided per the per-wave preregistrations; two-sided reported where it changes the conclusion |
| All-pairs | 10 condition pairs × 15 outcomes = 150 two-sided Welch tests, Holm within outcome, Mann–Whitney robustness, cross-wave pairs flagged |
| Trial-level calibration | AUROC2, Brier score, calibration slope/intercept (logistic), binned calibration curves |
| Mediation | Parallel mediation, 4 condition dummies (`ai` reference) → trust + hedonic UEQ → overestimation; 5,000 bootstrap resamples (lavaan in R, statsmodels OLS path models in Python) |
| Moderators | Condition × moderator OLS (NFC, trust, AI use frequency, age) on score, error, discrimination |
| Trend | Jonckheere–Terpstra for ordered patterns across conditions |
| Wave sensitivity | (a) drop the 5 wave-2 baseline participants; (b) within-wave-2-only omnibus |
| Performance null | JZS Bayes factors (Cauchy r = .707): two-sided BF₀₁ and directional BF₀₊ vs the preregistered improvement H1; Welch TOST equivalence at \|g\| < 0.3 and 0.2 |
| Trial-level models | GEE logit (exchangeable working correlation, robust SE, cluster = participant) for accuracy; MixedLM random intercepts for confidence; `BinomialBayesMixedGLM` (VB) robustness. Covariates: baseline-defined item difficulty (z), presentation position (z), NFC (z) |
| Temporal | Presentation position = rank of interface slot within participant (order randomized); GEE position slopes per condition, halves/thirds contrasts, trial-1-excluded re-analysis |
| Dunning–Kruger | Within-condition percentile ranks; quartile gaps; slope-modulation OLS (HC3); Gignac–Zajenkowski artifact checks (quadratic term, Breusch–Pagan) |
| LLM-competence split | Each item classified as AI-correct (baseline modal answer = correct) or AI-wrong; per-item-set Welch contrasts vs baseline; GEE logit condition × AI-competence interaction |

α = .05 throughout. Figures use a colorblind-safe palette: `ai` #2a78d6, `ai-reliability` #eb6834,
`alternatives` #1baf7a, `pause-points` #eda100, `reflection-task` #e87ba4.

## 6. Metacognition measure selection

Assessed against the 17 measures reviewed in Rahnev, D. (2025), *A comprehensive assessment of
current methods for measuring metacognition*, **Nature Communications**,
[doi:10.1038/s41467-025-56117-0](https://doi.org/10.1038/s41467-025-56117-0)
(open access [PMC11735976](https://pmc.ncbi.nlm.nih.gov/articles/PMC11735976/); code
[OSF y5w2d](https://osf.io/y5w2d/)). All 17 are implemented and, where applicable, validated on
simulated observers in `rahnev_metrics_notebook.ipynb`.

**What this design offers, and what it rules out:**

| Property | Value | Consequence |
|---|---|---|
| Trials per participant | 12 | Far below the paper's 50–400 regimes; individual estimates noisy, group comparisons unbiased |
| Task format | 4-option MCQ, chance 25% | **No S1/S2 stimulus structure** → type-1 d′/criterion undefined → no SDT measure estimable |
| Confidence | 0–100 slider | Quasi-continuous; suits all four traditional measures |
| Accuracy | M = 43.3%; 0 participants at 0% or 100% | ΔConf and AUC2 defined for all 917 |
| Constant-confidence participants | 15 of 917 | Gamma and Phi undefined for them (n = 902) |

**Verdicts:**

| Measure | Verdict | Reason |
|---|---|---|
| **ΔConf** | **Use — primary** | Computable for all 917; identical to the preregistered `confidence_discrimination` (agrees to 7×10⁻¹⁵); most test-retest-reliable measure in the paper |
| **AUC2** | **Use — primary robustness check** | Computable for all 917; rank-based, so invariant to confidence-scale usage — covers ΔConf's main weakness |
| Gamma | Caution — secondary | n = 902; r = .95 with AUC2, same information with different tie handling |
| Phi | Caution — secondary | n = 902; sensitive to scale usage and accuracy base rate; r ≥ .86 with the others |
| meta-d′, M-Ratio, M-Diff | **Do not use** | Need S1/S2 SDT structure + ≳100 trials; task has neither, and no defensible binary collapse of the four options exists. Implementation is validated on simulated 2AFC observers (ideal observer recovered at M-Ratio = 1.005) and kept for future SDT-compatible designs |
| ΔConf/AUC2/Gamma/Phi × Ratio and Diff (8 variants) | **Do not use** | Their SDT-ideal baseline requires d′ and criterion — undefined here. Purpose adopted by regression instead (below) |
| meta-noise | **Do not use** | Process-model fit unidentifiable from 12 MCQ trials. A simplified Gaussian reduction recovers only the *ordering* of true meta-noise even at 100,000 simulated trials, while inflating its magnitude — a caution against treating reduced forms as calibrated quantities |
| meta-uncertainty (CASANDRE) | **Do not use** | Requires graded stimulus strengths and many trials per level |

**The performance confound.** The paper's most consequential warning is that traditional type-2
measures rise with type-1 performance even when metacognition is unchanged — and our conditions do
differ in accuracy (pause points ≈ −1.1 problems vs baseline). The paper's remedy (the Ratio
variants) is structurally unavailable, so the analysis instead:

1. **reproduces the confound on simulation** — with metacognition held fixed, traditional measures
   grow ~1.4–4.5× as accuracy rises from 60% to 90%, while Ratio variants stay flat;
2. **measures it empirically** — in this dataset measure–accuracy correlations are ≈ 0
   (r = −.01 to −.07), likely because individual accuracy differences are dominated by AI-reliance
   strategy rather than a common evidence axis;
3. **adjusts for it** — all condition effects re-estimated with standardized actual score as a
   covariate. Conclusions unchanged (ΔConf: reliability cards +5.40 → +5.31, p < .001;
   alternatives +3.25 → +3.17, p = .008).

**Reporting notes.** The reliability-cards effect replicates on all four traditional measures
(ΔConf g = +0.50; AUC2 0.60 vs 0.54, g = +0.36, Holm p = .002; Gamma g = +0.27, p = .042;
Phi g = +0.29, p = .027). The alternatives effect is Holm-significant on ΔConf only (AUC2 p = .10
uncorrected), so describe it as confidence-*magnitude* separation rather than improved rank
ordering. Pooled item-level AUC2 puts baseline discrimination barely above chance (0.516,
CI [0.493, 0.539]) against reliability cards 0.573 and alternatives 0.565 — but pooled values mix
within- and between-person variance, so they complement rather than replace the per-participant
analysis.

A follow-up wanting M-Ratio-style efficiency needs a two-class task (e.g. 2AFC statement
verification) with ≥50–100 trials per participant; the notebook's validated implementations are
ready for that design. The study's global-estimate outcomes (`absolute_estimation_error` etc.) are
not among the paper's 17 — those are all item-level — and remain complementary evidence about
whole-task metacognitive monitoring.

## 7. Reproducing

```bash
# Python — run the primary notebook first; it writes the CSVs the others consume
jupyter nbconvert --to notebook --execute deep_analysis_notebook.ipynb
jupyter nbconvert --to notebook --execute pairwise_tests_notebook.ipynb
jupyter nbconvert --to notebook --execute rahnev_metrics_notebook.ipynb
jupyter nbconvert --to notebook --execute analysis_S1.ipynb

# Follow-up analyses (temporal, easy/hard, Dunning–Kruger, mixed models, Bayesian null)
python3 followup_analyses.py

# LLM-competence split and item difficulty figure
python3 llm_competence_analysis.py

# R
Rscript hypothesis_tests.R          # base R, no packages — replicates the confirmatory tests
Rscript -e 'rmarkdown::render("analysis_S1.Rmd")'
```

Committed runs: Python 3.11 (pandas 3.0.5, numpy 2.4.6, scipy 1.17.1, statsmodels 0.14.6,
matplotlib 3.11.1), R 4.3.3, August 2026. Generated tables and figures go to
`notebook_analysis_output/` (gitignored, regenerated on run).
