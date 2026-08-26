"""Analyses required by the round-2 academic review (paper repo).

1.  (stats-1/theory-1/hci-1) H2 specification adjudication: binary vs continuous vs
    item-fixed-effects difficulty control; three-way model; BIC-approx BF and Wald
    CIs quantifying the interaction nulls.
2.  (stats-2/metacog-1) Continuous-difficulty control WITHIN the easy stratum.
3.  (stats-3) JZS Bayes-factor prior sensitivity at r = 0.5 / 0.707 / 1.0.
4.  (metacog-8/openscience-3) Manual 18-ID wave-1 exclusion-list sensitivity rerun.
5.  (design-4/theory-3) Card-implied expected-score benchmark + exposure dose-response.
6.  (design-3) Per-protocol gate sensitivity (high-gate-share halves), endogenous.
7.  (stats-5/metacog-3) Stratified-ns disclosure + chi-square on condition-differential
    exclusion of uniform-outcome participants.
8.  (metacog-5) Resolution ceiling of a perfectly difficulty-keyed observer.
9.  (design-1) Guessing-floor knowledge rate; lucky-guess share of correct trials.
10. (theory-6) H3 headroom: always-follow vs oracle-reliance expected scores from the
    pre-study scripted eval's per-item assistant accuracy.
11. (metacog-4) Per-participant type-2 AUC attenuation simulation at 12 trials.
12. (metacog-6) Signed estimation error by condition.

Writes ROUND2_ANALYSES.md. All exploratory/uncorrected unless stated.
"""

from __future__ import annotations

import json
import math
import re

import numpy as np
import pandas as pd
from scipy import stats
from scipy.integrate import quad

RNG = np.random.default_rng(2026)
OUT = []


def log(s: str = "") -> None:
    print(s)
    OUT.append(s)


def hedges_g(a, b):
    na, nb = len(a), len(b)
    sp = math.sqrt(((na - 1) * a.var(ddof=1) + (nb - 1) * b.var(ddof=1)) / (na + nb - 2))
    return (1 - 3 / (4 * (na + nb) - 9)) * (a.mean() - b.mean()) / sp


P = pd.read_csv("notebook_analysis_output/participant_metrics.csv")
T = pd.read_csv("notebook_analysis_output/task_metrics.csv")
P = P[~P["exclude_primary"].astype(bool)].copy()
T = T[T["participant_id"].isin(set(P["participant_id"]))].copy()
assert len(P) == 917 and len(T) == 917 * 12

CONDS = ["ai", "ai-reliability", "alternatives", "pause-points", "reflection-task"]
LAB = {"ai": "baseline", "ai-reliability": "cards", "alternatives": "alternatives",
       "pause-points": "pause", "reflection-task": "reflection"}
T["correct01"] = T["correct"].astype(float)
T["cond"] = pd.Categorical(T.condition, categories=CONDS)

base_acc = T[T.condition == "ai"].groupby("authored_order")["correct01"].mean()
order = base_acc.sort_values(ascending=False).index.tolist()
easy6, hard6 = set(order[:6]), set(order[6:])
T["stratum"] = np.where(T["authored_order"].isin(easy6), "easy", "hard")
T["diff_z"] = -((T.authored_order.map(base_acc) - base_acc.mean()) / base_acc.std())

log("# Round-2 review analyses\n")

# ---------- 1. H2 specification adjudication --------------------------------
log("## 1. H2 specification adjudication: how the correct x condition terms move\n")
import statsmodels.formula.api as smf

specs = {
    "binary (correct x hard01)":
        "confidence ~ correct01 * C(cond) + correct01 * hard01",
    "continuous (+ cond x diff_z)":
        "confidence ~ correct01 * C(cond) + correct01 * diff_z + C(cond) * diff_z",
    "item FE (correct x item)":
        "confidence ~ correct01 * C(cond) + correct01 * C(authored_order)",
    "item FE + cond x item":
        "confidence ~ correct01 * C(cond) + correct01 * C(authored_order) "
        "+ C(cond) * C(authored_order)",
    "three-way (correct x cond x diff_z)":
        "confidence ~ correct01 * C(cond) * diff_z",
}
T["hard01"] = (T.stratum == "hard").astype(float)
keyterms = ["correct01:C(cond)[T.ai-reliability]", "correct01:C(cond)[T.alternatives]"]
fitted = {}
for name, f in specs.items():
    m = smf.mixedlm(f, data=T, groups=T.participant_id).fit(reml=True)
    fitted[name] = m
    ci = m.conf_int()
    row = []
    for k in keyterms:
        row.append(f"{k.split('T.')[1][:-1]}: b = {m.params[k]:+.2f} "
                   f"[{ci.loc[k, 0]:+.2f}, {ci.loc[k, 1]:+.2f}], p = {m.pvalues[k]:.4f}")
    log(f"- **{name}**: " + "; ".join(row))
m3 = fitted["three-way (correct x cond x diff_z)"]
for k in m3.params.index:
    if k.startswith("correct01:C(cond)") and k.endswith(":diff_z"):
        log(f"  - three-way {k}: b = {m3.params[k]:+.2f}, p = {m3.pvalues[k]:.4f}")

# BIC-approximate BF for the correct x condition block in the maximal item-FE model
full_f = specs["item FE + cond x item"]
red_f = ("confidence ~ correct01 * C(authored_order) + C(cond) * C(authored_order)")
mf = smf.mixedlm(full_f, data=T, groups=T.participant_id).fit(reml=False)
mr = smf.mixedlm(red_f, data=T, groups=T.participant_id).fit(reml=False)
bf01 = math.exp((mf.bic - mr.bic) / 2)
log(f"\nBIC-approximate BF01 for dropping the correct x condition block from the "
    f"maximal item-FE model: {bf01:,.0f} (BIC full {mf.bic:.0f} vs reduced {mr.bic:.0f}; "
    f"Wagenmakers 2007 approximation)")

# ---------- 2. Continuous control within the easy stratum -------------------
log("\n## 2. Continuous-difficulty control WITHIN the easy stratum\n")
TE = T[T.stratum == "easy"].copy()
me = smf.mixedlm("confidence ~ correct01 * C(cond) + correct01 * diff_z + C(cond) * diff_z",
                 data=TE, groups=TE.participant_id).fit(reml=True)
for k in keyterms:
    log(f"- easy-only {k}: b = {me.params[k]:+.2f}, p = {me.pvalues[k]:.4f}")

# ---------- 3. JZS prior sensitivity -----------------------------------------
log("\n## 3. JZS Bayes-factor prior sensitivity (r = 0.5, 0.707, 1.0)\n")
from pingouin import bayesfactor_ttest


def jzs_bf_dir(tp, nx, ny, sign, r):
    neff, df = nx * ny / (nx + ny), nx + ny - 2
    def f(d):
        try:
            v = stats.nct.pdf(tp, df, d * math.sqrt(neff))
        except OverflowError:
            return 0.0
        return (v if math.isfinite(v) else 0.0) * 2 * stats.cauchy.pdf(d, scale=r)
    lo, hi = (0, 40) if sign > 0 else (-40, 0)
    return quad(f, lo, hi, limit=400)[0] / stats.t.pdf(tp, df)


base_sc = P.loc[P.condition == "ai", "actual_score"].to_numpy()
RS = (0.5, math.sqrt(2) / 2, 1.0)
log("| test | r=0.5 | r=0.707 | r=1.0 |")
log("|---|---|---|---|")
for c in CONDS[1:]:
    a = P.loc[P.condition == c, "actual_score"].to_numpy()
    tt, _ = stats.ttest_ind(a, base_sc, equal_var=True)
    vals = [1 / jzs_bf_dir(tt, len(a), len(base_sc), +1, r) for r in RS]
    log(f"| BF0+ score, {LAB[c]} vs baseline | " +
        " | ".join(f"{v:.1f}" for v in vals) + " |")
pp_sc = P.loc[P.condition == "pause-points", "actual_score"].to_numpy()
tt_pp, _ = stats.ttest_ind(pp_sc, base_sc, equal_var=True)
vals = [float(bayesfactor_ttest(tt_pp, len(pp_sc), len(base_sc), r=r)) for r in RS]
log("| BF10 two-sided score, pause vs baseline | " +
    " | ".join(f"{v:.2e}" for v in vals) + " |")
refl_sc = P.loc[P.condition == "reflection-task", "actual_score"].to_numpy()
tt_r, _ = stats.ttest_ind(refl_sc, base_sc, equal_var=True)
vals = [1 / float(bayesfactor_ttest(tt_r, len(refl_sc), len(base_sc), r=r)) for r in RS]
log("| BF01 two-sided score, reflection vs baseline | " +
    " | ".join(f"{v:.1f}" for v in vals) + " |")
base_err = P.loc[P.condition == "ai", "absolute_estimation_error"].to_numpy()
refl_err = P.loc[P.condition == "reflection-task", "absolute_estimation_error"].to_numpy()
tt_re, _ = stats.ttest_ind(refl_err, base_err, equal_var=True)
vals = [1 / float(bayesfactor_ttest(tt_re, len(refl_err), len(base_err), r=r)) for r in RS]
log("| BF01 two-sided monitoring error, reflection vs baseline | " +
    " | ".join(f"{v:.1f}" for v in vals) + " |")

# ---------- 4. Manual 18-ID exclusion-list sensitivity ----------------------
log("\n## 4. Wave-1 manual exclusion list (18 IDs, not applied): sensitivity\n")
P2 = P[~P["exclude_manual"].astype(bool)].copy()
log(f"- flagged among analyzed N: {int(P['exclude_manual'].astype(bool).sum())} "
    f"(N drops 917 -> {len(P2)})")
deltas = []
for out_col in ("absolute_estimation_error", "confidence_discrimination",
                "prompts_per_task", "actual_score"):
    b0 = P.loc[P.condition == "ai", out_col].dropna().to_numpy()
    b1 = P2.loc[P2.condition == "ai", out_col].dropna().to_numpy()
    for c in CONDS[1:]:
        a0 = P.loc[P.condition == c, out_col].dropna().to_numpy()
        a1 = P2.loc[P2.condition == c, out_col].dropna().to_numpy()
        g0, g1 = hedges_g(a0, b0), hedges_g(a1, b1)
        deltas.append((out_col, LAB[c], g0, g1, abs(g1 - g0)))
worst = max(deltas, key=lambda x: x[4])
log(f"- max |delta-g| across the 16 confirmatory contrasts: {worst[4]:.3f} "
    f"({worst[0]} / {worst[1]}: g {worst[2]:+.3f} -> {worst[3]:+.3f})")
for out_col, c, g0, g1, d in deltas:
    if d > 0.02:
        log(f"  - {out_col} / {c}: g {g0:+.3f} -> {g1:+.3f}")

# ---------- 5. Card-implied benchmark + exposure dose-response --------------
log("\n## 5. Reliability cards: card-implied benchmark and exposure dose-response\n")
CARD_IMPLIED = 7.1  # sum over the 12 cards of (10 - errors)/10; errors from
# customizations/tasks/reliability_warnings.json at git 6c77ffe~1 (2,6,4,6,2,6,4,7,2,4,2,4)
cards = P[P.condition == "ai-reliability"]
base = P[P.condition == "ai"]
log(f"- card-implied expected score: {CARD_IMPLIED:.1f} of 12 "
    f"(the cards imply 59% assistant accuracy; scripted eval measured 41.7%)")
t1, p1 = stats.ttest_1samp(cards.post_with_ai, CARD_IMPLIED)
log(f"- cards post-estimate M = {cards.post_with_ai.mean():.2f} vs benchmark 7.1: "
    f"t = {t1:.2f}, p = {p1:.2e} (estimates sit ABOVE the card anchor)")
log(f"- baseline post-estimate M = {base.post_with_ai.mean():.2f}; actual scores: "
    f"cards {cards.actual_score.mean():.2f}, baseline {base.actual_score.mean():.2f}")
d_anchor = (cards.post_with_ai - CARD_IMPLIED).abs()
d_own = (cards.post_with_ai - cards.actual_score).abs()
log(f"- cards |estimate - anchor| M = {d_anchor.mean():.2f} vs "
    f"|estimate - own score| M = {d_own.mean():.2f} "
    f"(paired t = {stats.ttest_rel(d_anchor, d_own)[0]:.2f}, "
    f"p = {stats.ttest_rel(d_anchor, d_own)[1]:.2e})")
expo = cards["reliability_cards_presented"]
log(f"- card exposure: median {expo.median():.0f}/12 presented, "
    f"{(expo == 12).mean() * 100:.0f}% saw all 12, min {expo.min():.0f}")
for out_col, lab in (("absolute_estimation_error", "monitoring error"),
                     ("post_with_ai", "post estimate"),
                     ("confidence_discrimination", "dConf")):
    r, p = stats.pearsonr(expo, cards[out_col])
    log(f"- dose-response r(cards shown, {lab}) = {r:+.2f} (p = {p:.3f})")

# ---------- 6. Per-protocol gate sensitivity (endogenous) -------------------
log("\n## 6. Per-protocol gate sensitivity: high-gate-share halves vs baseline\n")
log("(endogenous split: gate share depends on participant prompt style)\n")
for c in ("alternatives", "pause-points", "reflection-task"):
    d = P[(P.condition == c) & (P.gate_tests > 0)].copy()
    d["share"] = d.gate_matched / d.gate_tests
    hi = d[d.share >= d.share.median()]
    row = []
    for out_col, lab in (("absolute_estimation_error", "error"), ("actual_score", "score")):
        a = hi[out_col].dropna().to_numpy()
        b = P.loc[P.condition == "ai", out_col].dropna().to_numpy()
        tt, pp = stats.ttest_ind(a, b, equal_var=False)
        row.append(f"{lab} g = {hedges_g(a, b):+.2f} (p = {pp:.3f})")
    log(f"- {LAB[c]} high-share half (n = {len(hi)}, "
        f"median share {d.share.median():.2f}): " + "; ".join(row))

# ---------- 7. Stratified ns + differential-exclusion test ------------------
log("\n## 7. Stratified dConf: per-stratum ns and condition-differential exclusion\n")


def dconf(g):
    c = g.loc[g.correct01 == 1, "confidence"]
    w = g.loc[g.correct01 == 0, "confidence"]
    return c.mean() - w.mean() if len(c) and len(w) else np.nan


for st in ("easy", "hard"):
    d = T[T.stratum == st]
    per = d.groupby(["participant_id", "condition"]).apply(
        dconf, include_groups=False).rename("dc").reset_index()
    tab = []
    for c in ("ai", "ai-reliability", "alternatives"):
        s = per[per.condition == c]["dc"]
        tab.append((LAB[c], s.notna().sum(), len(s)))
    log(f"- {st}: " + "; ".join(f"{l} {n}/{tot}" for l, n, tot in tab))
    cont = np.array([[n, tot - n] for _, n, tot in tab])
    chi, pchi = stats.chi2_contingency(cont)[:2]
    log(f"  chi-square on defined-vs-dropped rates: chi2 = {chi:.2f}, p = {pchi:.3f}")

# ---------- 8. Resolution ceiling of a difficulty-keyed observer -------------
log("\n## 8. Murphy resolution ceiling: perfectly difficulty-keyed observer\n")
for c in CONDS:
    d = T[T.condition == c]
    pk = d.groupby("authored_order")["correct01"].mean()
    ybar = d.correct01.mean()
    ceiling = float(((pk - ybar) ** 2).mean())  # equal trials per item
    log(f"- {LAB[c]}: ceiling resolution = {ceiling:.4f} "
        f"(a confidence = item base-rate observer)")

# ---------- 9. Guessing contamination ----------------------------------------
log("\n## 9. Four-option guessing floor: knowledge rate and lucky-guess share\n")
for c in CONDS + ["pooled"]:
    a = (T.correct01.mean() if c == "pooled"
         else T.loc[T.condition == c, "correct01"].mean())
    k = max(0.0, (4 * a - 1) / 3)
    luck = 0.25 * (1 - k) / a
    log(f"- {LAB.get(c, c)}: accuracy {a:.3f}, knowledge rate k = {k:.3f}, "
        f"lucky-guess share of correct trials = {luck * 100:.0f}%")
pooled_item = T.groupby("authored_order")["correct01"].mean().sort_values()
log(f"- items at or below the 25% floor (pooled): "
    f"{(pooled_item <= 0.255).sum()} of 12 (range {pooled_item.min():.3f}-"
    f"{pooled_item.iloc[3]:.3f} for the 4 hardest)")

# ---------- 10. H3 headroom under the parity regime ---------------------------
log("\n## 10. H3 headroom: always-follow vs oracle-reliance expected scores\n")
ev = json.load(open("../../../model_evaluation/eval_results/continue.json"))
ai_runs = [r for r in ev if r["condition"] == "ai"]
per_item = pd.DataFrame(ai_runs).groupby("task")["correct"].mean()
always = per_item.sum()
oracle = (per_item + (1 - per_item) * 0.25).sum()
log(f"- scripted-eval per-item assistant accuracy (n = 3 reps/item, patient sweep): "
    f"mean {per_item.mean():.3f}")
log(f"- expected score always-follow = {always:.2f}/12; "
    f"oracle reliance (follow when right, guess otherwise) = {oracle:.2f}/12; "
    f"headroom = {oracle - always:.2f} problems ({(oracle - always) / 12 * 100:.0f} pp)")
log(f"- observed condition means: " + ", ".join(
    f"{LAB[c]} {P.loc[P.condition == c, 'actual_score'].mean():.2f}" for c in CONDS))
log("- (oracle assumes perfect trial-level error detection AND 25% chance on "
    "rejected trials; real headroom is smaller)")

# ---------- 11. AUC2 attenuation at 12 trials ---------------------------------
log("\n## 11. Per-participant type-2 AUC attenuation at 12 trials (simulation)\n")
conf_grid = T.loc[T.condition == "ai", "confidence"].to_numpy()
acc = float(T.loc[T.condition == "ai", "correct01"].mean())


def sim_auc2(true_auc, nsim=4000):
    d = math.sqrt(2) * stats.norm.ppf(true_auc)
    out = []
    for _ in range(nsim):
        y = RNG.random(12) < acc
        e = RNG.normal(0, 1, 12) + d * y
        # map latent evidence through the empirical confidence distribution
        conf = np.quantile(conf_grid, stats.norm.cdf(e / math.sqrt(1 + d * d / 4)))
        conf = np.round(conf / 5) * 5  # observed 5-point grid
        c1, c0 = conf[y], conf[~y]
        if len(c1) == 0 or len(c0) == 0:
            continue
        u = stats.mannwhitneyu(c1, c0, alternative="two-sided")[0]
        out.append(u / (len(c1) * len(c0)))
    return float(np.mean(out))


for ta in (0.55, 0.60, 0.65, 0.70):
    log(f"- true AUC2 = {ta:.2f} -> mean 12-trial estimate = {sim_auc2(ta):.3f}")

# ---------- 12. Signed estimation error by condition --------------------------
log("\n## 12. Signed estimation error (post estimate - actual score) by condition\n")
for c in CONDS:
    s = P.loc[P.condition == c, "signed_estimation_error"]
    log(f"- {LAB[c]}: M = {s.mean():+.2f} (SD {s.std():.2f})")

with open("ROUND2_ANALYSES.md", "w") as fh:
    fh.write("\n".join(OUT) + "\n")
print("\nwritten ROUND2_ANALYSES.md")
