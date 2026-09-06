# Publication-ready analysis of the empirical study

Everything reported in Section 5 (Empirical Evaluation) of the CHI'27 paper can be regenerated
from this folder. `./run.sh` runs the Python pipeline and the independent R replication.

Numbers were last regenerated on 2026-09-05 (evening run, including tab:null). Python 3.12.13 (pingouin 0.6.1, statsmodels 0.14.6,
SciPy 1.17.1, pandas 3.0.5, numpy 2.4.6); R 4.6.1 (BayesFactor 0.9.12-4.8, effectsize 1.0.3).

## Layout

| Path | Content |
|---|---|
| `data/participant_metrics.csv` | One row per participant (925; `exclude_primary == False` gives the analysed 917): condition, scores, estimates, confidence measures, prompts, exposure logs, questionnaires, exclusion flags |
| `data/task_metrics.csv` | One row per participant x problem (11,100): answer, correctness, confidence, dwell, prompts, display position |
| `data/reliance_trials.csv` | Per-problem parsed assistant verdict (7,909 covered problems): verdict, followed, AI correct, difficulty |
| `data/qualitative_codes_*.csv`, `data/free_text_responses.csv` | Free-text answers and their lexical codes (codebook v2) |
| `scripts/apa_results.py` | All inferential statistics (ANOVA, Tukey HSD, t-tests vs baseline, Bayesian ANOVA, Welch/Games-Howell robustness, reliance OLS and GEE models) |
| `scripts/apa_tables.py` | Renders `output/apa_tables.tex` (tab:effects, tab:ux, tab:reliance) from `output/apa_results.json` |
| `scripts/verify_paper_numbers.py` | Recomputes every descriptive and exploratory number quoted in the text (`output/VERIFY_PAPER_NUMBERS.md`) |
| `scripts/make_figures.py` | The four figures in `figures/`, as `.pdf` (matplotlib fonts) and, with `--pgf`, as `.pgf` twins whose text is typeset by LaTeX in the paper's font (reference renderings; not the ones the paper inputs) |
| `scripts/make_tikz_figures.py` | The figures the paper inputs (`figures/*_tikz.tex`): the same data written out as editable pgfplots code, 1:1 with the `.pgf` exports in geometry, sizes and colours (need `\usepgfplotslibrary{groupplots}` and `\usetikzlibrary{matrix,calc}`) |
| `scripts/verdict_parse.py` | Rule-based parser of the assistant's verdicts from the raw chat logs (needs `data_analysis/raw_data`; its output is `data/reliance_trials.csv`; write-up in `output/VERDICT_PARSE.md`) |
| `scripts/qualitative_coding.py`, `qualitative_validation/` | Lexical codebook, coding of the free-text answers, the two-round validation samples, and the human coding of the complete set (`CODEBOOK.md` with shorthand key, `full_coding_sheet.csv` = all 1,454 analysed answers, `HUMAN_CODER_INSTRUCTIONS.md`, `score_validation.py` with `full` mode; standard library only, reads the stored machine codes) |
| `rank_posterior.R`, `rank_posterior_output.txt`, `output/rank_table.tex` | Posterior ranking of the five conditions per outcome from the same `anovaBF` model (100k draws): P(best), expected rank, P(beats baseline), P(all four beat baseline), pairwise P(A > B); `rank_table.tex` holds the rows of tab:ranking |
| `replicate.R`, `replicate_R_output.txt` | Independent R replication: `aov`, `TukeyHSD`, `t.test(var.equal = TRUE)`, `effectsize::hedges_g`, `BayesFactor::anovaBF(rscaleFixed = 0.5)` |

## Where each element of the paper comes from

| Paper element | Source |
|---|---|
| tab:participants, exposure checks, task difficulty range | `output/VERIFY_PAPER_NUMBERS.md` (sections Sample, Tasks, Manipulation and exposure checks) |
| tab:effects, tab:ux (M, SD, F, omega^2, BF10, t, df, p, g [CI]) | `output/apa_tables.tex`; numbers in `output/apa_results.json` |
| Tukey HSD comparisons quoted in the text | `output/APA_RESULTS.md` (Tukey blocks) |
| Bayesian ANOVA on score without pause points (BF01 = 3.96) | `output/apa_results.json` -> `extra.score_bf_without_pause`; R: `replicate_R_output.txt` |
| tab:reliance, follow-rate ANOVA and t-tests, GEE logits | `output/apa_results.json` -> `reliance`; `output/APA_RESULTS.md` |
| tab:qual (code prevalences, chi-square, Cramer's V on the analysed sample: 814 strategy and 640 manipulation answers) and the held-out macro-F1 (.61 over all 16 codes) | `output/VERIFY_PAPER_NUMBERS.md` (section Qualitative codes); raw codes in `data/qualitative_codes_*.csv` (these still include the 7 + 5 answers from excluded participants) |
| tab:calib, Brier/Murphy decomposition, type-2 AUC, difficulty GEE, time course, card anchoring, trust correlations | `output/VERIFY_PAPER_NUMBERS.md` |
| tab:null (directional and two-sided JZS BF, Welch TOST at |g| < .3, GEE OR with NFC and position covariates) | `output/apa_results.json` -> `extra.null_robustness`; rendered in `output/apa_tables.tex`; BFs cross-checked in `replicate_R_output.txt` |
| tab:ranking (posterior P(best) [expected rank], P(all four beat baseline)) and the ranking paragraph | `output/rank_table.tex`; full matrices in `rank_posterior_output.txt` |
| fig:results, fig:confidence, fig:difficulty, fig:reliance | `figures/*_tikz.tex` (used in main.tex); `.pdf`/`.pgf` renderings alongside |

## Testing logic

1. One-way ANOVA across the five conditions with omega^2 (Welch ANOVA reported as robustness check).
2. Tukey HSD post-hoc tests over all ten pairs (Games-Howell as robustness check).
3. Uncorrected two-sided pooled-variance t-tests of each intervention against baseline, with Hedges' g and 95% CI.
4. Default Bayesian ANOVA (Rouder et al., 2012; JZS prior, r = 0.5 on standardized effects). The Python implementation
   (`jzs_anova_bf10`) integrates the g-prior numerically and is validated in two ways: for k = 2 it equals pingouin's
   JZS t-test Bayes factor, and for the paper's outcomes it matches `BayesFactor::anovaBF` (see `replicate_R_output.txt`).
5. Reliance: OLS of per-participant follow rate on condition; GEE logistic regressions (exchangeable, clustered by
   participant) of following on condition, condition x advice correctness, and condition x item difficulty.

## Known limits

- `verdict_parse.py` and `qualitative_coding.py` need the raw chat logs in `data_analysis/raw_data/data/final_data/`,
  which are not copied here; their outputs are.
- The qualitative codebook was validated against blind annotation by the analyst (an LLM), not by a human coder. The
  complete set is being hand-coded in `qualitative_validation/full_coding_sheet.csv` (see `HUMAN_CODER_INSTRUCTIONS.md`);
  once done, `score_validation.py full` gives the human-coded prevalences for tab:qual and the codebook's agreement.
