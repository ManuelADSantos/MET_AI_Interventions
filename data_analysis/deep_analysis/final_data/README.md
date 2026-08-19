# Final-Dataset Analysis Package

Entry point for the analysis of the merged final dataset
(`data_analysis/results/data/final_data/`) — all five conditions of the MET-AI interventions
study. This file indexes the deliverables, records the verified data-quality facts and open
issues, and summarizes what the analyses concluded. Last updated 2026-08-19.

## The study, in one paragraph

925 Prolific participants solved 12 four-option planning/organizing problems with an AI chat
assistant, rating their confidence per problem and estimating their performance before and after,
in one of five conditions: plain **AI chat (baseline)**, **reliability cards** (per-task AI
reliability info with evaluation strategies), **alternatives** (two parallel AI replies per
prompt), **pause points** (step-by-step AI replies), and **reflection task** (a reflection page
after every problem). Data were collected in two waves (baseline + reliability cards in July 2026;
the other three interventions in August 2026), so cross-wave comparisons carry a cohort caveat.
The study hypothesis: interventions improve **performance and/or metacognition** vs the baseline.

## Deliverables and run order

| File | What it is | Depends on |
|---|---|---|
| [`deep_analysis_notebook.ipynb`](deep_analysis_notebook.ipynb) | Primary notebook: loading, integrity audit, scoring, exclusions, confirmatory + exploratory analyses (modules A–Q), exports | final_data JSONs only — **run first** |
| [`FINDINGS.md`](FINDINGS.md) | Written results report (sample, integrity, all outcome families, pairwise highlights, limitations) | numbers from the notebooks |
| [`pairwise_tests_notebook.ipynb`](pairwise_tests_notebook.ipynb) | Two-sided Welch t-tests for **all 10 condition pairs** × 15 outcomes, Holm-corrected, Mann–Whitney robustness, effect-size matrices | `notebook_analysis_output/participant_metrics.csv` from the primary notebook |
| [`hypothesis_tests.R`](hypothesis_tests.R) | **R replication** (base R, no packages) of the confirmatory hypothesis tests + pairwise tests; log in [`hypothesis_tests_R_output.txt`](hypothesis_tests_R_output.txt) — reproduces the Python results exactly | same CSV export |
| [`rahnev_metrics_notebook.ipynb`](rahnev_metrics_notebook.ipynb) | Implements the 17 metacognition measures from Rahnev (2025, *Nat Commun*, [doi:10.1038/s41467-025-56117-0](https://doi.org/10.1038/s41467-025-56117-0)); applies the 4 applicable ones, validates the SDT-based ones on simulation | final_data JSONs (self-contained; soft cross-check vs the CSV export) |
| [`METACOGNITION_METRICS_RATIONALE.md`](METACOGNITION_METRICS_RATIONALE.md) | Use / use-with-caution / do-not-use verdict for each of the 17 measures, with reasoning | — |

All notebooks are committed executed (outputs included). Generated tables/figures go to
`notebook_analysis_output/` (gitignored; regenerated on run).

## Analysis conventions (shared across deliverables)

* **Scoring ground truth**: the canonical answer key
  (`customizations/questions/correct_answers.py`) — verified to reproduce the backend's stored
  `answerResults` bit-for-bit for all 925 records (0 mismatches / 11,100 scored items).
* **Analysis sample n = 917** of 925: excluded are participants failing >1 of 4 embedded
  attention checks (7), answering <12 problems (0), or finishing in <10 minutes (1). A wave-1
  manual ID list ("less than 30%", provenance undocumented) is flagged but **not** applied.
* **Repeated participation**: 38 participants took part in two conditions; `final_data` keeps
  only each participant's **earliest** run (verified against the raw wave exports), so no
  further exclusion is needed; `repeated.csv` documents the dropped runs.
* **Statistics**: Welch t-tests with Hedges' g (95% CI); Holm correction within each outcome
  family; confirmatory intervention-vs-baseline tests are **directional** per the per-wave
  preregistrations (two-sided reported alongside); everything else is two-sided and exploratory.
* **Cohort caveat**: comparisons of the three wave-2 interventions against the (97% wave-1)
  baseline are also cross-wave comparisons. Sensitivity checks (main notebook module O; the
  within-wave-2 tests in the pairwise notebook) show the headline results are not driven by the
  five wave-2 baseline participants, and the pause-points effects replicate within wave 2 — but
  the confound cannot be fully removed by analysis.

## Headline results (details and exact statistics in FINDINGS.md)

**Hypothesis verdict — does each intervention improve performance and/or metacognition vs
baseline?** (directional Welch t, Holm-corrected)

| Intervention | Performance (actual score) | Metacognition | Hypothesis |
|---|---|---|---|
| Reliability cards | no — two-sided *reversed* (g = −0.23, p = .030) | **yes**: estimation error g = −0.46, discrimination g = +0.50 | supported via metacognition |
| Alternatives | no — two-sided reversed (g = −0.22, p = .033) | **yes**: estimation error g = −0.65, discrimination g = +0.28 | supported via metacognition |
| Pause points | no — two-sided reversed (g = −0.57, p < .001) | **yes**: estimation error g = −0.33 | supported via metacognition |
| Reflection task | no (g = −0.03) | no (error p = .064; discrimination n.s.) | not supported |

* The metacognitive gains come mostly from **lowered self-estimates** (post-study "with AI"
  estimates drop 1.6–2.2 problems in the effective interventions vs 0.5 in baseline), except
  that reliability cards and alternatives also genuinely improve item-level confidence
  discrimination — and those effects survive adjustment for actual score.
* **Every intervention costs user experience**: lower SUS and UEQ-S, higher NASA-TLX; trust in
  the AI drops under reliability cards, alternatives, and pause points. Pause points is the most
  expensive (SUS −19.6 points, accuracy g = −0.57); reflection is the heaviest workload and
  roughly doubles completion time but preserves trust best.
* All-pairs tests (150, Holm-corrected): 80 significant, 36 of them between same-wave conditions
  — including confound-free confirmation that pause points scores below the other wave-2
  interventions and that alternatives leads them on metacognitive accuracy.
* Of Rahnev's 17 metacognition measures, only the four traditional type-2 measures are
  computable here (no SDT stimulus structure; 12 trials); ΔConf (= the study's
  `confidence_discrimination`) is the recommended primary, AUC2 the robustness check.

## Data-quality register

| # | Item | Status |
|---|---|---|
| 1 | Backend scoring (`answerResults`) internally consistent: present for 925/925 records, 12 boolean entries each, sum equals stored `correctAnswers` in 925/925 | ✅ verified |
| 2 | `answerResults` matches the canonical key recomputation (11,100 items) | ✅ verified, 0 mismatches |
| 3 | `final_data` deduplication: one record per participant, earliest run kept for all 38 repeats | ✅ verified against raw wave exports |
| 4 | **Convenience CSVs' correctness columns** (`*_correct`, `n_correct`, `metacog_sensitivity`): the original `export_condition_csvs.py` scored against a hard-coded key that was wrong on 8/12 items (the committed CSVs disagreed with `answerResults` on 4,971/11,100 per-question values) | ✅ **fixed** — exporter now sources correctness from each record's own `answerResults` and asserts `n_correct == correctAnswers` per row |
| 5 | Regenerated CSVs verified (2026-08-19): per-question vs `answerResults` **0/11,100** mismatches; `n_correct` vs `correctAnswers` **0/925**; `mean_confidence` and `metacog_sensitivity` recompute exactly from the corrected flags; headers/row counts unchanged; re-running the exporter reproduces the committed files byte-for-byte | ✅ verified |

Every metric in this package is derived from the JSON records (or from
`participant_metrics.csv`, which the primary notebook derives from the JSONs); the CSVs are a
convenience view, now consistent with the same ground truth.

## Reproducing

```bash
# Python (pandas, numpy, scipy, statsmodels, matplotlib)
jupyter nbconvert --to notebook --execute deep_analysis_notebook.ipynb   # run first
jupyter nbconvert --to notebook --execute pairwise_tests_notebook.ipynb
jupyter nbconvert --to notebook --execute rahnev_metrics_notebook.ipynb

# R (base R only)
Rscript hypothesis_tests.R
```

Committed runs: Python 3.11 (pandas 3.0.5, numpy 2.4.6, scipy 1.17.1, statsmodels 0.14.6,
matplotlib 3.11.1), R 4.3.3, August 2026.
