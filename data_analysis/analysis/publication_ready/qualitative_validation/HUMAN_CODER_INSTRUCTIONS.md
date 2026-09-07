# Human coding of the free-text answers

Status: complete (2026-09-07). All 1,454 rows coded by Manuel; tab:qual is computed from these codes by `scripts/verify_paper_numbers.py`.

Purpose: the lexical codebook (`scripts/qualitative_coding.py`) was so far validated only against blind annotation by
the analyst (an LLM). Manuel decided (2026-09-06) to hand-code the complete analysed set, so the human codes become the
reported coding and the lexical codebook is scored against them as a reliability check.

Files
- `CODEBOOK.md`: the 16 codes (11 strategy, 5 manipulation) with a shorthand key (a-k, 0-4).
- `full_coding_sheet.csv`: all 1,454 analysed answers (814 STRATEGIES rows, then 640 MANIPULATION rows from the four
  intervention conditions; baseline had no manipulation to report). Random order within each block (seed 20260906).
  `holdout_vid` marks the 119 rows that were also in the earlier held-out sample. About 29k words.
- `human_coding_sheet.csv`: the earlier 120-answer held-out sheet (superseded by the full sheet; kept for the record).

Steps
1. Read `CODEBOOK.md`. Do not look at `holdout_hand_labels.csv` or `data/qualitative_codes_*.csv` (machine codes) while coding.
2. Fill `human_codes` in `full_coding_sheet.csv` with every code that applies: shorthand runs such as `adg` (strategy
   rows, letters only) or `04` (manipulation rows, digits only), or full code names separated by semicolons. Leave the
   cell empty when nothing applies. Save as UTF-8 CSV, same header.
3. Score (standard library only, no venv needed):

       cd qualitative_validation
       python3 score_validation.py full                      # codebook vs human codes on all 1,454 answers
       python3 score_validation.py holdout --labels full_coding_sheet.csv --labels-col human_codes   # not needed; the full run covers it

   The script warns about rows whose codes belong to the other question type, prints the human-coded prevalence per
   condition (input to tab:qual), per-code precision/recall of the codebook against the human codes, mean Jaccard per
   question type, and macro-F1 over the codes.
4. Paper: tab:qual is then computed from the human codes (chi-square and Cramer's V as before), and the codebook agreement
   (Jaccard, macro-F1) is reported as a reliability check. The LLM-annotation wording in Sections 5 and 6 is replaced.
