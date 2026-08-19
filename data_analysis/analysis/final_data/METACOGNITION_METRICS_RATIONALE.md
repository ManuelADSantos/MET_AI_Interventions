# Should we use Rahnev's (2025) 17 metacognition measures on this data?

Rationale for adopting or rejecting each of the 17 measures of metacognition assessed in:

> Rahnev, D. (2025). **A comprehensive assessment of current methods for measuring metacognition.**
> *Nature Communications*. https://doi.org/10.1038/s41467-025-56117-0
> (open access: [PMC11735976](https://pmc.ncbi.nlm.nih.gov/articles/PMC11735976/); code: [OSF y5w2d](https://osf.io/y5w2d/))

Every empirical number quoted below is produced by
[`rahnev_metrics_notebook.ipynb`](rahnev_metrics_notebook.ipynb) (same folder), which implements
all measures, validates the SDT-based ones on simulated observers, and applies the applicable
ones to the merged final dataset.

## What the paper says, in brief

The paper assesses 17 measures of metacognitive sensitivity/efficiency on Confidence Database
datasets and simulations: the four **traditional type-2 measures** (ΔConf, AUC2, Gamma, Phi), the
**meta-d′ family** (meta-d′, M-Ratio, M-Diff), **eight new SDT-normalized variants** in which each
traditional measure is divided by (Ratio) or subtracted from (Diff) its expectation for an
SDT-ideal observer with the same type-1 sensitivity and criterion, and **two process-model
measures** (meta-noise, from Shekhar & Rahnev 2021; meta-uncertainty, from the CASANDRE model of
Boundy-Singer et al. 2022). Its headline conclusions: all 17 are valid with broadly similar
precision; traditional measures depend **strongly on type-1 task performance** (the problem the
Ratio variants and model-based measures largely fix); dependencies on response and metacognitive
bias are comparatively weak; split-half reliabilities are high but test–retest reliabilities are
mostly poor, with **ΔConf the most test-retest-reliable** measure; and no measure is best in all
contexts — the design should pick the measure.

## What this dataset offers

| Property | Value | Consequence |
|---|---|---|
| Trials per participant | **12** | far below the 50–400-trial regimes the paper evaluates; individual estimates are noisy, group comparisons remain unbiased |
| Task format | 4-option multiple choice (logic problems), chance = 25% | **no S1/S2 stimulus-class structure** → type-1 d′/criterion undefined → no SDT-based measure is estimable |
| Confidence | 0–100 slider per item | quasi-continuous; good for all four traditional measures |
| Accuracy | mean 43.3%; **0** participants at 0% or 100% | ΔConf and AUC2 defined for **all 917** analyzed participants |
| Constant-confidence participants | 15 of 917 (~1.6%) | Gamma and Phi undefined for them (defined n = 902) |
| Sessions | one per participant | the paper's test-retest findings can't be checked here, only imported |
| Design detail | conditions differ in accuracy (pause-points ≈ 1 problem below baseline) | the paper's performance-dependence warning is directly relevant to cross-condition comparisons |

Decision criteria applied per measure: **(C1)** structural computability on this data,
**(C2)** stability at 12 trials, **(C3)** robustness to the between-condition accuracy differences
(the paper's core concern), **(C4)** what the paper reports about the measure's behavior.

## Verdict summary

| # | Measure | Verdict | One-line reason |
|---|---|---|---|
| 1 | ΔConf | **Use — primary** | computable for all 917; identical to the study's preregistered `confidence_discrimination`; most test-retest-reliable measure in the paper |
| 2 | AUC2 | **Use — primary robustness check** | computable for all 917; rank-based, insensitive to confidence-scale usage |
| 3 | Gamma | Use with caution — secondary | computable (n = 902); r = .95 with AUC2, adds nothing beyond it |
| 4 | Phi | Use with caution — secondary | computable (n = 902); sensitive to scale usage and accuracy base rate |
| 5 | meta-d′ | **Do not use** | needs S1/S2 SDT structure + ≳100 trials; task has neither |
| 6 | M-Ratio | **Do not use** | inherits meta-d′'s requirements; ratios unstable at low trial counts |
| 7 | M-Diff | **Do not use** | inherits meta-d′'s requirements |
| 8 | ΔConf-Ratio | **Do not use** | SDT-expected baseline requires d′ and criterion — undefined for this task |
| 9 | AUC2-Ratio | **Do not use** | same |
| 10 | Gamma-Ratio | **Do not use** | same |
| 11 | Phi-Ratio | **Do not use** | same |
| 12 | ΔConf-Diff | **Do not use** | same |
| 13 | AUC2-Diff | **Do not use** | same |
| 14 | Gamma-Diff | **Do not use** | same |
| 15 | Phi-Diff | **Do not use** | same |
| 16 | meta-noise | **Do not use** | process-model fit not identifiable from 12 MCQ trials |
| 17 | meta-uncertainty | **Do not use** | CASANDRE requires graded stimulus strengths and many trials |

The intent of measures 8–15 — removing the type-1-performance confound — is adopted anyway,
through regression adjustment (see "The performance confound" below).

---

## 1. ΔConf — mean confidence on correct minus incorrect trials

**Use (primary).** Needs only correctness and confidence (C1 ✓), and is defined for every
analyzed participant because nobody scored 0/12 or 12/12. It is *by construction identical* to the
`confidence_discrimination` outcome the study already preregistered — the notebook confirms
agreement with the main analysis export to 7 × 10⁻¹⁵. The paper reports ΔConf as the measure with
the **highest test–retest reliability** (ICC ≈ .39/.53/.65/.75 at 50/100/200/400 trials), a
property that matters at our extreme 12-trial count (C2): whatever individual-level stability is
achievable here, ΔConf is the best-placed measure to achieve it. Its known weaknesses — it is
expressed in raw confidence units (so differences in scale usage between people add noise) and it
depends on type-1 performance — are handled by pairing it with AUC2 and by accuracy adjustment.
Result on this data: reliability cards g = +0.50 and alternatives g = +0.28 vs baseline
(Holm-significant), effects essentially unchanged after accuracy adjustment (+5.40 → +5.31 and
+3.25 → +3.17 points).

## 2. AUC2 — area under the type-2 ROC

**Use (primary robustness check).** Computable for all 917 (C1 ✓). As a rank-based measure it is
invariant to monotone transformations of the confidence scale, which directly addresses ΔConf's
scale-usage weakness — participants who compress or shift the 0–100 slider are measured
identically. It gives constant-confidence participants a defined, chance-level value (0.5) rather
than dropping them. The cost at 12 trials is coarseness (few distinct attainable values;
simulation in the notebook: SD ≈ 0.18 across identical simulated participants), so it should be
read at group level only (C2). On this data it confirms the reliability-cards effect
(0.60 vs 0.54, g = +0.36, Holm p = .002) but the alternatives effect does not survive Holm on
AUC2 (p = .10 uncorrected) — i.e., the alternatives advantage lives partly in confidence
*magnitude* separation (ΔConf) rather than pure rank ordering; report both.

## 3. Gamma — Goodman–Kruskal rank correlation

**Use with caution (secondary).** Computable (C1 ✓) but undefined for the 15 constant-confidence
participants, and empirically r = .95 with AUC2 on this data — it is the same information with a
different tie-handling convention (gamma discards tied pairs; AUC2 counts them as ½). The paper
treats it as one of the interchangeable traditional measures with no distinct advantage. Keep it
as a sensitivity check (it reproduces the reliability-cards effect, g = +0.27, Holm p = .042);
do not interpret it separately from AUC2.

## 4. Phi — accuracy–confidence Pearson correlation

**Use with caution (secondary).** Computable (C1 ✓, n = 902). As a point-biserial correlation it
re-introduces sensitivity to confidence-scale usage (unlike AUC2) and its maximum attainable value
depends on the accuracy base rate, which differs between conditions — exactly the kind of
artifact the paper warns about (C3). Empirically it tracks the other three (r ≥ .86) and adds no
discriminating power. Fine as a convergence check (reliability cards g = +0.29, Holm p = .027),
not as a headline measure.

## 5–7. meta-d′, M-Ratio, M-Diff

**Do not use.** These require the standard SDT setting: two stimulus classes (S1/S2) so that
type-1 d′ and criterion c are defined, plus response-conditional confidence distributions —
typically with ≥100 trials per participant for stable maximum-likelihood fits (C1 ✗, C2 ✗). This
study's problems are one-off, four-option logic scenarios: there is no signal/noise axis, no
hit/false-alarm structure, and no defensible binary collapse of the four answer options (any
pairing of "Only statement 1 / Only statement 2 / Both / Neither" into two pseudo-classes is
arbitrary and changes the answer). Twelve trials per participant rules out individual fits even
if the structure existed. The notebook still implements the full meta-d′ MLE and validates it on
simulated 2AFC observers (ideal observer recovered with M-Ratio = 1.005; metacognitive noise
correctly attenuates meta-d′), so the implementation is available for future studies with an
SDT-compatible design.

## 8–15. ΔConf/AUC2/Gamma/Phi-Ratio and -Diff (the paper's new SDT-normalized variants)

**Do not use — but adopt their purpose by regression.** Each variant divides (Ratio) or subtracts
(Diff) the measure's expectation for an SDT-ideal observer *with the observed d′ and criterion*.
That baseline is the blocker: without an SDT characterization of the task there is nothing to
normalize against (C1 ✗). The notebook validates the full pipeline on simulation — reproducing
the paper's central result that with metacognition held fixed, the traditional measures grow by a
factor of ~1.4–4.5 as type-1 accuracy rises from 60% to 90%, while the Ratio variants stay nearly
flat — and then addresses the same confound for our data the only way this design allows:
**re-estimating condition effects with actual score as a covariate**.

Two empirical facts make this workable here (C3): the conditions do differ in accuracy (so the
concern is real), but across participants the traditional measures are nearly uncorrelated with
actual score in this dataset (r = −.01 to −.07), and accordingly the adjusted condition effects
are almost identical to the unadjusted ones (e.g., ΔConf: reliability cards +5.40 → +5.31,
p < .001; alternatives +3.25 → +3.17, p = .008). The metacognitive advantages of the reliability
cards and alternatives interventions are therefore **not** artifacts of the accuracy differences.

## 16. meta-noise (Shekhar & Rahnev, 2021)

**Do not use.** A process-model measure: the σ of noise corrupting the confidence-generating
evidence, estimated by fitting a full SDT-plus-noise model to response-conditional confidence
distributions. It presupposes everything meta-d′ presupposes, plus a parametric confidence model
and enough trials to constrain an extra parameter (C1 ✗, C2 ✗). The notebook includes a
simplified Gaussian reduction (σₘ derived from M-Ratio via meta-d′ ≈ d′/√(1+σₘ²)) and shows on
simulation that even with 100,000 trials it recovers only the *ordering* of true meta-noise while
inflating its magnitude — a caution against using reduced forms as calibrated quantities.

## 17. meta-uncertainty (CASANDRE; Boundy-Singer et al., 2022)

**Do not use.** CASANDRE models confidence as a probability judgment made under uncertainty about
one's own sensory noise; fitting it requires a design with graded stimulus strengths or
reliability levels and many trials per level, so the uncertainty parameter is identifiable. This
study has a single task type, no stimulus-strength manipulation, and 12 trials (C1 ✗). (The
AI-reliability manipulation in one condition varies the *advisor*, not the participant's own
evidence, so it cannot stand in for stimulus reliability.) Documented as a stub in the notebook.

---

## The performance confound — why it matters here and what we do instead

The paper's most consequential finding for this study is that traditional type-2 measures rise
with type-1 performance even when metacognition is unchanged. Our conditions differ in accuracy
(pause-points ≈ −1.1 problems vs baseline), so *any* cross-condition difference in ΔConf/AUC2
could in principle be a performance artifact. Since the paper's remedy (Ratio variants) is
structurally unavailable (measures 8–15 above), the analysis:

1. **reproduces the confound on simulation** so its expected direction and size are explicit
   (notebook Section 5c);
2. **measures it empirically** — in this dataset the measure–accuracy correlations are ≈ 0
   (−.01…−.07), likely because individual accuracy differences here are dominated by AI-reliance
   strategies rather than a common evidence axis; and
3. **adjusts for it** — all condition effects are re-estimated with standardized actual score as
   a covariate; conclusions are unchanged (notebook Section 9).

## Bottom line for this study

* Report **ΔConf** (already preregistered as `confidence_discrimination`) as the primary
  item-level metacognition outcome, with **AUC2** as the scale-free robustness check; keep
  **Gamma/Phi** in the supplement as convergence checks. All four only at group level — a
  12-trial individual estimate is noise (simulation: SD across identical simulated participants
  ≈ 0.18 AUC2 units).
* Note when reporting: the reliability-cards effect replicates on all four measures; the
  alternatives effect is Holm-significant on ΔConf only, so describe it as confidence-magnitude
  separation rather than improved rank ordering.
* The pooled item-level analysis (notebook Section 10) shows baseline discrimination is barely
  above chance (pooled AUC2 0.516, CI [0.493, 0.539]) while reliability cards (0.573) and
  alternatives (0.565) are clearly above it — but pooled values mix within- and between-person
  variance, so they complement rather than replace the per-participant analysis.
* Skip all SDT-based and process-model measures (5–17): structurally unidentifiable here. If a
  follow-up study wants M-Ratio-style efficiency, it needs a two-class task (e.g., 2AFC
  statement verification) with ≥50–100 trials per participant — the notebook's validated
  implementations are ready for that design.
* The study's global-estimate outcomes (`absolute_estimation_error` etc.) are *not* among the
  paper's 17 measures (those are all item-level); they remain complementary evidence about
  metacognitive monitoring at the whole-task level.
