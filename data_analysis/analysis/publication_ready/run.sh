#!/usr/bin/env bash
# Reproduce every statistic, table, and figure of the paper's empirical study from data/.
# Requires the project's Python environment (../../../.venv) and R >= 4.6 with BayesFactor and effectsize.
set -e
cd "$(dirname "$0")"
PY=../../../.venv/bin/python
export MET_DATA_DIR="$PWD/data"
$PY scripts/apa_results.py          # -> scripts/APA_RESULTS.md, scripts/apa_results.json
$PY scripts/apa_tables.py           # -> scripts/apa_tables.tex
$PY scripts/verify_paper_numbers.py # -> scripts/VERIFY_PAPER_NUMBERS.md
$PY scripts/make_figures.py figures       # -> figures/*.pdf
$PY scripts/make_figures.py --pgf figures # -> figures/*.pgf (LaTeX-typeset twins used by the paper)
$PY scripts/make_tikz_figures.py figures  # -> figures/*_tikz.tex (editable pgfplots twins)
mv scripts/APA_RESULTS.md scripts/apa_results.json scripts/apa_tables.tex scripts/VERIFY_PAPER_NUMBERS.md output/
Rscript replicate.R && Rscript rank_posterior.R   # -> replicate_R_output.txt, rank_posterior_output.txt, output/rank_table.tex
