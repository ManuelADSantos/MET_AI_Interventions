# Final-Dataset Analysis

Analysis of the merged final dataset (`data_analysis/raw_data/data/final_data/`) — all five
conditions of the MET-AI interventions study. 925 participants, 917 analyzed, 12 four-option
planning problems, five conditions (plain AI chat baseline, reliability cards, alternatives,
pause points, reflection task). Hypothesis: interventions improve performance and/or metacognition
vs baseline.

## Read this

| | |
|---|---|
| **[`RESULTS.md`](RESULTS.md)** | Every result: verdict, sample, integrity, confirmatory tests, all-pairs, UX costs, exploratory findings, follow-up analyses, limitations |
| **[`METHODS.md`](METHODS.md)** | Pipeline, variable definitions, statistical conventions, metacognition measure selection, reproduce commands |
| **[`MONITORING_WITHOUT_CONTROL.md`](MONITORING_WITHOUT_CONTROL.md)** | Literature memo: why monitoring improves but performance does not — six candidate explanations mapped to our evidence, for the paper's discussion |

## Code

| File | What it does | Depends on |
|---|---|---|
| [`deep_analysis_notebook.ipynb`](deep_analysis_notebook.ipynb) | Primary notebook: load, integrity audit, scoring, exclusions, confirmatory + exploratory analyses, CSV exports | raw JSONs — **run first** |
| [`analysis_S1.ipynb`](analysis_S1.ipynb) / [`.py`](analysis_S1.py) | Full 13-step analysis in paper-figure form (descriptives → tests → mediation → figures → precision card) | `participant_metrics.csv` |
| [`analysis_S1.Rmd`](analysis_S1.Rmd) | Same 13 steps in R (tidyverse, lavaan, effectsize) | `participant_metrics.csv` |
| [`pairwise_tests_notebook.ipynb`](pairwise_tests_notebook.ipynb) | All 10 condition pairs × 15 outcomes = 150 Welch tests, Holm-corrected, Mann–Whitney robustness | `participant_metrics.csv` |
| [`rahnev_metrics_notebook.ipynb`](rahnev_metrics_notebook.ipynb) | Implements Rahnev's (2025) 17 metacognition measures; applies the 4 computable ones, validates the SDT family on simulation | raw JSONs |
| [`hypothesis_tests.R`](hypothesis_tests.R) | Base-R replication of the confirmatory + pairwise tests — reproduces the Python results exactly. Log: [`hypothesis_tests_R_output.txt`](hypothesis_tests_R_output.txt) | `participant_metrics.csv` |
| [`followup_analyses.py`](followup_analyses.py) | Meeting action items: temporal/trial-split analysis, easy-vs-hard × condition, Dunning–Kruger, trial-level mixed models (GEE/MixedLM), Bayesian assertion of the performance null (results in `RESULTS.md` §11) | both metrics CSVs |
| [`meeting_analyses.py`](meeting_analyses.py) | Independent replication of §11 with alternative operationalizations (pooled-difficulty split, items-metric DK modulation, linear-probability mixed model) — agreements noted inline in §11 | both metrics CSVs |
| [`qualitative_coding.py`](qualitative_coding.py) | Lexical multi-label coding of the post-study free-text responses (strategies + manipulation questions); prevalence tables in `RESULTS.md` §11.6 | raw JSONs |
| [`llm_competence_analysis.py`](llm_competence_analysis.py) | LLM-competence split (AI-correct vs AI-wrong items) and item difficulty distribution figure; results in `RESULTS.md` §11.7 | both metrics CSVs |

Notebooks are committed executed. Generated tables and figures go to `notebook_analysis_output/`
(gitignored, regenerated on run). Run commands in [`METHODS.md`](METHODS.md) §7.

## Headline

| Intervention | Performance | BF₀₊ | Metacognition | Verdict |
|---|---|---|---|---|
| Reliability cards | reversed (g = −0.23) | 27.0 | error g = −0.46, discrimination g = +0.50 | **supported via metacognition** |
| Alternatives | reversed (g = −0.22) | 26.5 | error g = −0.65, discrimination g = +0.28 | **supported via metacognition** |
| Pause points | reversed (g = −0.57) | 58.2 | error g = −0.33 only | **partially supported** |
| Reflection task | null (g = −0.03) | 10.6 | null | **not supported** |

Metacognition improves, performance does not. BF₀₊ is the JZS Bayes factor for "no improvement"
over the preregistered improvement hypothesis — strong evidence against a performance gain in
every condition. A strict no-difference null is assertable only for reflection (BF₀₁ = 8.4,
TOST-equivalent at |g| < .3); reliability cards and alternatives are inconclusive between no
effect and a small cost (BF₀₁ ≈ 1), and pause points is a real deficit ([`RESULTS.md`](RESULTS.md)
§11.1). The metacognition mechanism is mostly deflated self-estimates rather than insight — though
reliability cards and alternatives also genuinely sharpen item-level discrimination. Every
intervention costs user experience. Full detail in [`RESULTS.md`](RESULTS.md).

**Caveat:** wave 1 (Jul 2026) collected baseline + reliability cards, wave 2 (Aug 2026) the other
three, so cross-wave comparisons carry a cohort confound. Within-wave-2 checks confirm the
pause-points accuracy cost and the alternatives metacognition advantage hold without it.
