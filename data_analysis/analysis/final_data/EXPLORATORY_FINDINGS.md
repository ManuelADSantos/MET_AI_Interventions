# Exploratory Findings — Beyond the Confirmatory Tests

Patterns surfaced from the MET-AI final dataset (n = 917) that go beyond the
preregistered hypothesis tests. All are exploratory and uncorrected unless noted.

---

## 1. Reliability cards selectively deflate confidence on hard items

The confidence drop relative to baseline is not uniform across problem difficulty.
Reliability cards reduce mean confidence by −15.8 pp on hard items (< 25% correct)
but only −3.3 pp on easy items (> 50% correct) — a selectivity gap of +12.4 pp.
Alternatives shows the same direction (+4.7 pp selectivity) but weaker. Pause points
and reflection reduce confidence roughly equally on hard and easy items (selectivity
≈ 0). This is notable because a blanket confidence deflation would lower confidence
everywhere equally; the selective pattern suggests reliability cards actually help
participants identify when the AI is more likely to be wrong.

| Intervention | Easy Δconf | Hard Δconf | Selectivity |
|---|---|---|---|
| Reliability cards | −3.3 pp | −15.8 pp | +12.4 |
| Alternatives | −6.9 pp | −11.6 pp | +4.7 |
| Pause points | −11.9 pp | −10.3 pp | −1.6 |
| Reflection task | −2.1 pp | −1.6 pp | −0.6 |

## 2. A pronounced hard-easy effect on calibration

Item difficulty varies from 18% to 80% correct across the 12 problems.
Overconfidence on hard items (problems with < 25% accuracy) reaches +42 to +58 pp
depending on condition, while on easy items it is only +8 to +16 pp. The hard-easy
gap is universal but largest under reflection (+49.9 pp) and baseline (+43.6 pp),
and smallest under reliability cards (+29.1 pp) — further evidence that reliability
cards help participants recalibrate specifically where it matters most.

## 3. Strong Dunning-Kruger pattern across all conditions

Actual score correlates r = −0.50 to −0.59 with signed estimation error in every
condition: low performers overestimate far more (bottom tertile: +4.8 items) than
high performers (+1.4 items). No intervention eliminates this gradient, though the
effective interventions compress it by pulling down the high-overestimators more.

| Tertile | Score M | Overestimation M | Confidence M |
|---|---|---|---|
| Low (n = 322) | 3.3 | +4.8 items | 70.2 |
| Mid (n = 385) | 5.5 | +3.2 items | 72.6 |
| High (n = 210) | 7.6 | +1.4 items | 75.2 |

## 4. Trust predicts overestimation, not performance

Trust in the AI correlates r = 0.36 (p < .001) with overestimation and r = 0.43
with mean confidence, but has essentially zero relationship with actual score
(r = −0.01 to +0.07 within conditions). In every condition, participants who
trust the AI more think they did better — but they did not. This suggests trust
operates as an amplifier of overconfidence rather than a facilitator of
AI-assisted performance.

## 5. Perceived AI superiority inflates — unless the intervention prevents it

Pre-study, participants across all conditions believe "AI alone" would outperform
"me without AI" by about 3 items. Post-study, this perceived AI advantage
*increases* significantly in baseline (+1.05, p < .001) and reflection (+1.48,
p < .001), but shows no shift in reliability cards (−0.13, n.s.) or alternatives
(−0.11, n.s.). The two interventions that improve metacognition are also the ones
that prevent the naive inflation of perceived AI superiority that happens by
default.

| Condition | Pre AI advantage | Post AI advantage | Shift |
|---|---|---|---|
| Baseline | 3.03 | 4.08 | +1.05 ** |
| Reliability cards | 2.68 | 2.71 | +0.03 |
| Alternatives | 3.09 | 3.05 | −0.01 |
| Pause points | 3.00 | 3.67 | +0.69 * |
| Reflection | 3.29 | 4.73 | +1.48 ** |

## 6. Better-than-average bias dissolves under pause points and alternatives

Pre-study, 56–66% of participants place themselves above the 50th percentile.
Post-study, this drops to 46% under pause points and 49% under alternatives —
effectively eliminating the better-than-average effect. Baseline stays at 63%.
The self-percentile shift is largest for pause points (−10.3 pp) and alternatives
(−8.6 pp), while baseline shows no significant shift (−1.2, p = .45).

AI-percentile estimates show a parallel story: pause points drives the largest
perceived AI downgrade (−14.0 pp, from 66.4 to 52.7), while baseline and
reflection maintain or slightly raise their AI estimates.

## 7. Cost-effectiveness: reliability cards is 5× more efficient than pause points

Computing metacognitive gain per SUS point sacrificed:

| Intervention | Error reduction | SUS cost | Efficiency |
|---|---|---|---|
| Reliability cards | −1.07 items | −4.9 pts | 0.217 items/pt |
| Alternatives | −1.46 items | −12.0 pts | 0.121 items/pt |
| Pause points | −0.81 items | −19.6 pts | 0.041 items/pt |
| Reflection task | −0.39 items | −6.7 pts | 0.058 items/pt |

Reliability cards delivers 80% of the metacognitive gain of alternatives at
40% of the SUS cost and none of the performance penalty beyond what alternatives
also shows.

## 8. High-confidence errors as a diagnostic pattern

Across all 11,004 trials, 34% are "high-confidence incorrect" (confidence ≥ 70,
answer wrong) — the costliest calibration failure. Reliability cards reduces
this rate to 29.0% from the baseline's 38.8%, a 10 pp improvement.
Simultaneously, "low-confidence correct" trials (the healthy uncertainty signal)
increase from 4.3% at baseline to 7.4% under reliability cards and 8.5% under
pause points.

| Condition | Hi-conf incorrect | Lo-conf correct |
|---|---|---|
| Baseline | 38.8% | 4.3% |
| Reliability cards | 29.0% | 7.4% |
| Alternatives | 31.0% | 8.0% |
| Pause points | 32.8% | 8.5% |
| Reflection | 37.1% | 5.8% |

## 9. Participant profiles from cluster analysis

K-means (k = 3) on score, confidence, overestimation, and discrimination yields
three interpretable profiles:

- **Calibrated skeptics** (n = 291, 32%): lower confidence (55), best
  discrimination (12 pp), lowest overestimation (2.3 items). Over-represented
  in reliability cards (43%) and alternatives (40%) vs baseline (19%).
- **Overconfident believers** (n = 321, 35%): high confidence (83), poor
  discrimination (1.6 pp), worst overestimation (6.1 items). Over-represented
  in baseline (44%) and reflection (38%).
- **Capable optimists** (n = 305, 33%): highest scores (6.7), high confidence
  (78) but well-calibrated overestimation (2.5 items). Over-represented in
  reflection (41%) and baseline (37%).

The condition × cluster association is significant (χ² = 47.5, p < .001):
reliability cards and alternatives shift the participant distribution toward the
calibrated-skeptic profile, while baseline and reflection load onto the
overconfident-believer profile.

## 10. Prompt behavior: length helps only at baseline

In the baseline condition, longer prompts predict higher scores (r = 0.21,
p = .005) — participants who write more detailed instructions to the AI get
better answers. Under alternatives the effect is weaker (r = 0.16, p = .030);
under the other three interventions it disappears entirely (|r| < 0.08). This
suggests the intervention structure compensates for prompt quality, standardizing
the interaction enough that individual prompting skill matters less.

## 11. Reflection effort does not predict outcomes

In the reflection condition, amount written (M = 1,118 words, range 116–2,582)
shows no significant correlation with actual score (r = −0.06), overestimation
(r = 0.11), or discrimination (r = −0.04). Tercile splits confirm: the
highest-effort third (M = 1,584 words) does not outperform the lowest (M = 792
words) on any outcome. The metacognitive value of reflection, such as it is,
seems driven by the task structure (pausing to reflect at all), not by
engagement depth.

## 12. Frequent AI users overestimate more

AI use frequency correlates positively with overestimation (r = 0.12,
p < .001) but not with actual score (r = 0.02, n.s.). People who use AI more
often in daily life are not better at solving problems with AI, but they think
they are. Similarly, Need for Cognition correlates with overestimation
(r = 0.11, p < .001) but not with score (r = 0.00) — people who enjoy
thinking overestimate their performance just as much as others.

## 13. Time-on-task helps only at baseline

In the baseline condition, more time predicts better scores (r = 0.18, p = .014)
and less overestimation (r = −0.18, p = .015). In every intervention condition,
both relationships vanish (|r| < 0.12, n.s.). The interventions impose their own
pacing structure, making raw time-on-task irrelevant as a predictor.

## 14. No within-session learning or confidence drift

Mean confidence shows no meaningful trend over the 12-problem sequence
(r = −0.005, p = .61, collapsed). The one exception: reliability cards shows a
slight decline (r = −0.056, p = .009), consistent with gradual updating from
the reliability information. Accuracy also shows no reliable position trend.
Participants do not measurably learn from one problem to the next.

## 15. Dwell time and prompting do not predict accuracy

There is no meaningful speed-accuracy tradeoff at the trial level: dwell time ×
correctness r is effectively zero in every condition (|r| < 0.03). Number of
prompts per task also does not predict whether the answer is correct (prompts
on correct vs incorrect trials differ by < 0.05 turns in all conditions except
pause points, where the mechanical extra turns create a +0.21 difference).

## 16. Extreme scores and score distribution

No participant scored 0/12 or 12/12 — the task set avoids both floor and ceiling.
The distribution is roughly symmetric (median 5, IQR 4–7) except under pause
points, which shows positive skew (0.74) with its lowered mean of 4.49. 82% of
participants overestimate their score; only 10.5% underestimate. The 68 exact
calibrators (7.4%) tend to be higher scorers (M = 6.0 vs 5.2 overall) with lower
confidence (M = 62 vs 72 overall).

---

*All analyses use the standard analysis sample (n = 917) and the task_metrics /
participant_metrics exports from deep_analysis_notebook.ipynb. Cluster analysis
uses sklearn KMeans (k = 3, random_state = 42). No multiple-comparison correction
is applied to the exploratory correlations — treat them as hypothesis-generating.*
