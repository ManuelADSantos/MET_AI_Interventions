# Independent R replication of the inferential statistics reported in Section 5 of the paper.
# Reads the exported participant-level data, recomputes the one-way ANOVAs, Tukey HSD post-hoc
# tests, the uncorrected two-sided t-tests against baseline with Hedges' g, and the default
# Bayesian ANOVA (BayesFactor::anovaBF, rscaleFixed = 0.5), and writes replicate_R_output.txt
# plus sessionInfo() so that versions can be quoted in the paper.
#
# Run from this folder:  Rscript replicate.R

suppressPackageStartupMessages({
  library(BayesFactor)
  library(effectsize)
})

pm <- read.csv("data/participant_metrics.csv", stringsAsFactors = FALSE)
pm <- pm[pm$exclude_primary == "False", ]
stopifnot(nrow(pm) == 917)
pm$condition <- factor(pm$condition, levels = c("ai", "ai-reliability", "alternatives", "pause-points", "reflection-task"))

outcomes <- c(absolute_estimation_error = "Estimation error", confidence_discrimination = "Confidence discrimination",
              actual_score = "Score", prompts_per_task = "Prompts per problem", sus_score = "SUS",
              ueq_overall = "UEQ-S", tlx_mean = "NASA-TLX", trust_mean = "Trust")

sink("replicate_R_output.txt")
cat("R replication of the paper's inferential statistics\n")
cat("N =", nrow(pm), "; per condition:", paste(table(pm$condition), collapse = " "), "\n\n")

set.seed(1)
for (v in names(outcomes)) {
  cat("=====", outcomes[v], "(", v, ") =====\n")
  d <- pm[!is.na(pm[[v]]), c(v, "condition")]
  names(d)[1] <- "y"
  fit <- aov(y ~ condition, data = d)
  s <- summary(fit)[[1]]
  omega <- (s[1, "Sum Sq"] - s[1, "Df"] * s[2, "Mean Sq"]) / (sum(s[, "Sum Sq"]) + s[2, "Mean Sq"])
  cat(sprintf("ANOVA: F(%d, %d) = %.2f, p = %.3g, omega^2 = %.3f\n", s[1, "Df"], s[2, "Df"], s[1, "F value"], s[1, "Pr(>F)"], omega))
  w <- oneway.test(y ~ condition, data = d)
  cat(sprintf("Welch ANOVA (robustness): F(%.0f, %.1f) = %.2f, p = %.3g\n", w$parameter[1], w$parameter[2], w$statistic, w$p.value))
  bf <- anovaBF(y ~ condition, data = d, rscaleFixed = 0.5, progress = FALSE)
  cat(sprintf("Bayesian ANOVA (JZS, rscaleFixed = 0.5): BF10 = %.4g\n", exp(bf@bayesFactor$bf)))
  cat("Tukey HSD:\n")
  print(round(TukeyHSD(fit)$condition, 3))
  cat("Uncorrected two-sided t-tests vs baseline (pooled variance) with Hedges' g [95% CI]:\n")
  base <- d$y[d$condition == "ai"]
  for (c in levels(d$condition)[-1]) {
    x <- d$y[d$condition == c]
    tt <- t.test(x, base, var.equal = TRUE)
    g <- hedges_g(x, base)
    cat(sprintf("  %-16s t(%d) = %6.2f, p = %.3g, g = %+.2f [%+.2f, %+.2f]\n", c, tt$parameter, tt$statistic, tt$p.value, g$Hedges_g, g$CI_low, g$CI_high))
  }
  cat("\n")
}

# Score: directional and two-sided JZS t-test Bayes factors vs baseline (r = 0.707), as in tab:null
base <- pm$actual_score[pm$condition == "ai"]
for (c in levels(pm$condition)[-1]) {
  x <- pm$actual_score[pm$condition == c]
  bf_plus <- ttestBF(x = x, y = base, rscale = 0.707, nullInterval = c(0, Inf))
  bf_two <- ttestBF(x = x, y = base, rscale = 0.707)
  cat(sprintf("Score %-16s BF0+ = %.1f, two-sided BF01 = %.3g\n", c, 1 / exp(bf_plus@bayesFactor$bf[1]), 1 / exp(bf_two@bayesFactor$bf)))
}
cat("\n")

# Score without pause points: Bayesian ANOVA over the four remaining conditions
d4 <- droplevels(pm[pm$condition != "pause-points", c("actual_score", "condition")])
bf4 <- anovaBF(actual_score ~ condition, data = d4, rscaleFixed = 0.5, progress = FALSE)
cat(sprintf("Score without pause points: BF01 = %.3f\n\n", 1 / exp(bf4@bayesFactor$bf)))

# Reliance: per-participant follow rate (from the Python verdict parse)
rel <- read.csv("data/reliance_trials.csv", stringsAsFactors = FALSE)
rel$condition <- factor(rel$condition, levels = levels(pm$condition))
fr <- aggregate(followed ~ pid + condition, data = rel, FUN = mean)
fit <- aov(followed ~ condition, data = fr)
s <- summary(fit)[[1]]
cat(sprintf("Follow rate ANOVA: F(%d, %d) = %.2f, p = %.3g\n", s[1, "Df"], s[2, "Df"], s[1, "F value"], s[1, "Pr(>F)"]))
base <- fr$followed[fr$condition == "ai"]
for (c in levels(fr$condition)[-1]) {
  x <- fr$followed[fr$condition == c]
  tt <- t.test(x, base, var.equal = TRUE)
  g <- hedges_g(x, base)
  cat(sprintf("  %-16s M = %.3f, t(%d) = %6.2f, p = %.3g, g = %+.2f\n", c, mean(x), tt$parameter, tt$statistic, tt$p.value, g$Hedges_g))
}
cat("\n")
print(sessionInfo())
sink()
cat("wrote replicate_R_output.txt\n")
