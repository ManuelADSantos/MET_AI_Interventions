# =====================================================================================
# MET-AI Interventions - Hypothesis tests in R (base R only, no package dependencies)
# =====================================================================================
#
# HYPOTHESIS
#   Each intervention condition improves PERFORMANCE and/or METACOGNITION relative to
#   the plain-AI baseline (condition `ai`). Operationalized as in the Python analysis
#   (deep_analysis_notebook.ipynb):
#
#     Performance:    actual_score                (0-12 correct answers;   expected GREATER)
#     Metacognition:  absolute_estimation_error   (|post estimate - actual|; expected LESS)
#                     confidence_discrimination   (mean conf correct - incorrect; expected GREATER)
#
#   Tests are directional Welch t-tests per the preregistered directions, with Hedges' g
#   (95% CI), Holm correction across the 4 interventions within each outcome, and
#   two-sided p-values reported alongside as a sensitivity check. A second section runs
#   the exploratory two-sided Welch t-tests for ALL 10 condition pairs on the same
#   outcomes (the R version of pairwise_tests_notebook.ipynb).
#
# DATA
#   Reads notebook_analysis_output/participant_metrics.csv, exported by running
#   deep_analysis_notebook.ipynb (Part 1 + module Q). Exclusions are taken from that
#   export (attention checks, completeness, minimum duration), giving the same 917-
#   participant analysis sample as the Python notebooks.
#
# RUN
#   Rscript hypothesis_tests.R
#   Results print to the console; tables are written to notebook_analysis_output/.
#
# CAVEAT
#   `ai` and `ai-reliability` were collected in July 2026, the other three interventions
#   in August 2026, so intervention-vs-baseline contrasts for alternatives, pause-points,
#   and reflection-task are also cross-wave comparisons (see FINDINGS.md section 1 and
#   deep_analysis_notebook.ipynb modules B and O).
# =====================================================================================

ALPHA <- 0.05
BASELINE <- "ai"
CONDITIONS <- c("ai", "ai-reliability", "alternatives", "pause-points", "reflection-task")
INTERVENTIONS <- setdiff(CONDITIONS, BASELINE)
CONDITION_LABELS <- c(
  "ai" = "AI (baseline)", "ai-reliability" = "Reliability cards",
  "alternatives" = "Alternatives", "pause-points" = "Pause points",
  "reflection-task" = "Reflection task"
)
WAVE_OF <- c("ai" = 1, "ai-reliability" = 1, "alternatives" = 2,
             "pause-points" = 2, "reflection-task" = 2)

# outcome, expected direction for the intervention relative to baseline, family
HYPOTHESES <- data.frame(
  outcome  = c("actual_score", "absolute_estimation_error", "confidence_discrimination"),
  expected = c("greater", "less", "greater"),
  family   = c("performance", "metacognition", "metacognition"),
  stringsAsFactors = FALSE
)
OUTCOME_LABELS <- c(
  actual_score = "Actual score (0-12)",
  absolute_estimation_error = "Metacognitive accuracy |est - actual|",
  confidence_discrimination = "Confidence discrimination (pp)"
)

# ---------------------------------------------------------------- 1. Load the data --
metrics_csv <- file.path("notebook_analysis_output", "participant_metrics.csv")
if (!file.exists(metrics_csv)) {
  stop(sprintf(paste0(
    "%s not found.\nRun deep_analysis_notebook.ipynb (Part 1 and module Q) first; ",
    "it exports the participant-level metrics this script tests."), metrics_csv))
}
participants <- read.csv(metrics_csv, stringsAsFactors = FALSE)
participants$exclude_primary <- as.logical(participants$exclude_primary)
eligible <- participants[!participants$exclude_primary, ]
stopifnot(all(eligible$condition %in% CONDITIONS))

cat(sprintf("Analysis sample: %d of %d participants (exclusions from the Python export)\n",
            nrow(eligible), nrow(participants)))
print(table(factor(eligible$condition, levels = CONDITIONS)))
if (nrow(eligible) != 917) {
  warning("Analysis sample differs from the Python notebooks (expected 917).")
}

# ------------------------------------------------------------ 2. Statistical helpers --
hedges_g <- function(x, y, conf_level = 0.95) {
  nx <- length(x); ny <- length(y)
  pooled <- ((nx - 1) * var(x) + (ny - 1) * var(y)) / (nx + ny - 2)
  if (pooled <= 0) return(c(g = NA, low = NA, high = NA))
  g <- (mean(x) - mean(y)) / sqrt(pooled) * (1 - 3 / (4 * (nx + ny) - 9))
  se <- sqrt((nx + ny) / (nx * ny) + g^2 / (2 * (nx + ny - 2)))
  z <- qnorm(0.5 + conf_level / 2)
  c(g = g, low = g - z * se, high = g + z * se)
}

welch_row <- function(data, outcome, cond_a, cond_b, alternative) {
  x <- data[data$condition == cond_a, outcome]; x <- x[is.finite(x)]
  y <- data[data$condition == cond_b, outcome]; y <- y[is.finite(y)]
  directional <- t.test(x, y, alternative = alternative, var.equal = FALSE)
  two_sided <- t.test(x, y, alternative = "two.sided", var.equal = FALSE)
  g <- hedges_g(x, y)
  data.frame(
    outcome = outcome, cond_a = cond_a, cond_b = cond_b,
    n_a = length(x), n_b = length(y),
    mean_a = mean(x), mean_b = mean(y), diff = mean(x) - mean(y),
    t = unname(directional$statistic), df = unname(directional$parameter),
    p = directional$p.value, p_two_sided = two_sided$p.value,
    hedges_g = unname(g["g"]), g_ci_low = unname(g["low"]), g_ci_high = unname(g["high"]),
    stringsAsFactors = FALSE
  )
}

fmt_p <- function(p) ifelse(!is.finite(p), "-",
                            ifelse(p < 0.001, "< .001", sub("0\\.", "= .", sprintf("%.3f", p))))

# ---------------------------------------- 3. Confirmatory tests: each intervention vs ai --
cat("\n=====================================================================\n")
cat("CONFIRMATORY: intervention vs baseline, directional Welch t, Holm within outcome\n")
cat("=====================================================================\n")

confirmatory <- do.call(rbind, lapply(seq_len(nrow(HYPOTHESES)), function(h) {
  rows <- do.call(rbind, lapply(INTERVENTIONS, function(cond) {
    welch_row(eligible, HYPOTHESES$outcome[h], cond, BASELINE, HYPOTHESES$expected[h])
  }))
  rows$expected <- HYPOTHESES$expected[h]
  rows$family <- HYPOTHESES$family[h]
  rows$p_holm <- p.adjust(rows$p, method = "holm")
  rows
}))
confirmatory$significant <- confirmatory$p_holm < ALPHA
confirmatory$cross_wave <- WAVE_OF[confirmatory$cond_a] != WAVE_OF[confirmatory$cond_b]

for (outcome in HYPOTHESES$outcome) {
  block <- confirmatory[confirmatory$outcome == outcome, ]
  cat(sprintf("\n%s (expected %s than baseline; baseline mean %.2f)\n",
              OUTCOME_LABELS[outcome], block$expected[1], block$mean_b[1]))
  for (i in seq_len(nrow(block))) {
    r <- block[i, ]
    cat(sprintf("  %-18s mean %5.2f  diff %+5.2f  t(%.1f) = %+5.2f  p %s  Holm p %s  g = %+.2f [%+.2f, %+.2f]  %s%s\n",
                CONDITION_LABELS[r$cond_a], r$mean_a, r$diff, r$df, r$t,
                fmt_p(r$p), fmt_p(r$p_holm), r$hedges_g, r$g_ci_low, r$g_ci_high,
                ifelse(r$significant, "SIGNIFICANT", "n.s."),
                ifelse(r$cross_wave, " [cross-wave]", "")))
  }
}

# Opposite-direction check: a directional test cannot flag effects opposite to the
# hypothesis, so surface those via the two-sided p.
opposite <- confirmatory[!confirmatory$significant & confirmatory$p_two_sided < ALPHA, ]
if (nrow(opposite) > 0) {
  cat("\nOpposite-direction effects (directional test n.s., two-sided p < .05):\n")
  for (i in seq_len(nrow(opposite))) {
    r <- opposite[i, ]
    cat(sprintf("  %s, %s: g = %+.2f, two-sided p %s - direction OPPOSITE to hypothesis\n",
                OUTCOME_LABELS[r$outcome], CONDITION_LABELS[r$cond_a],
                r$hedges_g, fmt_p(r$p_two_sided)))
  }
}

# ------------------------------------------------- 4. Per-intervention hypothesis verdict --
cat("\n=====================================================================\n")
cat("HYPOTHESIS VERDICT PER INTERVENTION\n")
cat("(improves performance and/or metacognition vs the ai baseline?)\n")
cat("=====================================================================\n")
verdicts <- do.call(rbind, lapply(INTERVENTIONS, function(cond) {
  block <- confirmatory[confirmatory$cond_a == cond, ]
  performance <- block[block$family == "performance", ]
  metacognition <- block[block$family == "metacognition", ]
  data.frame(
    intervention = CONDITION_LABELS[cond],
    improves_performance = any(performance$significant),
    performance_note = ifelse(any(performance$p_two_sided < ALPHA & !performance$significant),
                              "two-sided REVERSED", "no"),
    improves_metacognition = any(metacognition$significant),
    metacognition_measures = paste(
      OUTCOME_LABELS[metacognition$outcome[metacognition$significant]], collapse = "; "),
    hypothesis_supported = any(block$significant),
    stringsAsFactors = FALSE
  )
}))
verdicts$performance_note[verdicts$improves_performance] <- "yes"
print(verdicts, row.names = FALSE, right = FALSE)

# ----------------------------------- 5. Exploratory: all pairwise two-sided comparisons --
cat("\n=====================================================================\n")
cat("EXPLORATORY: all 10 condition pairs, two-sided Welch t, Holm within outcome\n")
cat("=====================================================================\n")
pairs <- t(combn(CONDITIONS, 2))
pairwise <- do.call(rbind, lapply(HYPOTHESES$outcome, function(outcome) {
  rows <- do.call(rbind, lapply(seq_len(nrow(pairs)), function(k) {
    welch_row(eligible, outcome, pairs[k, 1], pairs[k, 2], "two.sided")
  }))
  rows$p_holm <- p.adjust(rows$p_two_sided, method = "holm")
  rows
}))
pairwise$significant <- pairwise$p_holm < ALPHA
pairwise$cross_wave <- WAVE_OF[pairwise$cond_a] != WAVE_OF[pairwise$cond_b]

for (outcome in HYPOTHESES$outcome) {
  block <- pairwise[pairwise$outcome == outcome & pairwise$significant, ]
  cat(sprintf("\n%s - Holm-significant pairs:\n", OUTCOME_LABELS[outcome]))
  if (nrow(block) == 0) { cat("  none\n"); next }
  for (i in seq_len(nrow(block))) {
    r <- block[i, ]
    cat(sprintf("  %s %s %s (g = %+.2f, Holm p %s)%s\n",
                CONDITION_LABELS[r$cond_a], ifelse(r$diff > 0, ">", "<"),
                CONDITION_LABELS[r$cond_b], r$hedges_g, fmt_p(r$p_holm),
                ifelse(r$cross_wave, " [cross-wave]", "")))
  }
}

# -------------------------------------------------------------------- 6. Write outputs --
output_dir <- "notebook_analysis_output"
dir.create(output_dir, showWarnings = FALSE)
write.csv(confirmatory, file.path(output_dir, "r_confirmatory_vs_baseline.csv"), row.names = FALSE)
write.csv(verdicts, file.path(output_dir, "r_hypothesis_verdicts.csv"), row.names = FALSE)
write.csv(pairwise, file.path(output_dir, "r_pairwise_tests.csv"), row.names = FALSE)

# Effect-size figure (base graphics): Hedges' g of each intervention vs baseline.
png(file.path(output_dir, "r_effect_sizes_vs_baseline.png"),
    width = 2200, height = 800, res = 200)
old_par <- par(mfrow = c(1, nrow(HYPOTHESES)), mar = c(4, 9, 3, 1))
palette_map <- c("ai-reliability" = "#eb6834", "alternatives" = "#1baf7a",
                 "pause-points" = "#eda100", "reflection-task" = "#e87ba4")
for (outcome in HYPOTHESES$outcome) {
  block <- confirmatory[confirmatory$outcome == outcome, ]
  block <- block[rev(seq_len(nrow(block))), ]
  plot(NULL, xlim = range(c(block$g_ci_low, block$g_ci_high, 0)),
       ylim = c(0.5, nrow(block) + 0.5), yaxt = "n",
       xlab = "Hedges' g vs baseline", ylab = "",
       main = OUTCOME_LABELS[outcome], cex.main = 0.9, font.main = 1)
  abline(v = 0, col = "#a5a39d")
  for (i in seq_len(nrow(block))) {
    r <- block[i, ]
    color <- palette_map[r$cond_a]
    segments(r$g_ci_low, i, r$g_ci_high, i, col = color, lwd = 3)
    points(r$hedges_g, i, pch = 19, col = color, cex = 1.3)
    text(r$hedges_g, i + 0.28, sprintf("%+.2f%s", r$hedges_g,
                                       ifelse(r$significant, " *", "")), cex = 0.75)
  }
  axis(2, at = seq_len(nrow(block)), labels = CONDITION_LABELS[block$cond_a],
       las = 1, cex.axis = 0.8, tick = FALSE)
}
par(old_par)
invisible(dev.off())

cat(sprintf("\nWrote: %s\n", paste(file.path(output_dir,
  c("r_confirmatory_vs_baseline.csv", "r_hypothesis_verdicts.csv",
    "r_pairwise_tests.csv", "r_effect_sizes_vs_baseline.png")), collapse = "\n       ")))
cat(sprintf("\nR %s | executed %s\n", getRversion(), format(Sys.time(), "%Y-%m-%d %H:%M %Z")))
