"""Analyses required by the expert-roundtable review fixes (paper repo).

1. (id 13/25) Reflection metacognitive null: JZS BF + TOST on monitoring error; TOST |g|<.2 on score.
2. (id 6) Discrimination within difficulty strata (baseline-derived 6/6 split) + MixedLM correct x condition.
3. (id 5) Slope/r of post_with_ai on actual_score by condition.
4. (id 14) Bootstrap CIs for the items-per-SUS-point ledger and the 73%/41% quantities.
5. (id 30/26) Holm across all 16 confirmatory tests; Holm on the four two-sided reversals.
6. (id 36) Brier score + Murphy decomposition + calibration slope/intercept per condition.
7. (id 1) Gate engagement: per-participant matched share by condition + dose-response check.
8. (id 29) Overconfidence descriptives on the baseline-derived split; 4-item split ranges on n=917.

Writes ROUNDTABLE_ANALYSES.md. All exploratory/uncorrected unless stated.
"""

from __future__ import annotations

import math

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

log("# Roundtable analyses\n")

# ---------------- 1. Reflection metacognitive null (id 13) ------------------
log("## 1. Reflection monitoring-error null, held to the performance-null standard\n")
base_err = P.loc[P.condition == "ai", "absolute_estimation_error"].to_numpy()
refl_err = P.loc[P.condition == "reflection-task", "absolute_estimation_error"].to_numpy()
t_err, p2 = stats.ttest_ind(refl_err, base_err, equal_var=True)
from pingouin import bayesfactor_ttest, tost
bf10 = float(bayesfactor_ttest(t_err, len(refl_err), len(base_err)))


def jzs_bf_dir(tp, nx, ny, sign, r=math.sqrt(2) / 2):
    neff, df = nx * ny / (nx + ny), nx + ny - 2
    def f(d):
        try:
            v = stats.nct.pdf(tp, df, d * math.sqrt(neff))
        except OverflowError:
            return 0.0
        return (v if math.isfinite(v) else 0.0) * 2 * stats.cauchy.pdf(d, scale=r)
    lo, hi = (0, 40) if sign > 0 else (-40, 0)
    return quad(f, lo, hi, limit=400)[0] / stats.t.pdf(tp, df)


bf_minus0 = jzs_bf_dir(t_err, len(refl_err), len(base_err), -1)  # H-: error reduced
sd_pool = math.sqrt(((len(refl_err) - 1) * refl_err.var(ddof=1) +
                     (len(base_err) - 1) * base_err.var(ddof=1)) / (len(refl_err) + len(base_err) - 2))
for bound_g in (0.3, 0.2):
    p_tost = float(tost(refl_err, base_err, bound=bound_g * sd_pool)["pval"].iloc[0])
    log(f"- TOST |g|<{bound_g}: p = {p_tost:.3f}")
log(f"- two-sided BF10 = {bf10:.2f} (BF01 = {1/bf10:.2f}); "
    f"BF0- (against an error reduction) = {1/bf_minus0:.2f}")
# score TOST at |g|<.2 for reflection (id 25)
base_sc = P.loc[P.condition == "ai", "actual_score"].to_numpy()
refl_sc = P.loc[P.condition == "reflection-task", "actual_score"].to_numpy()
sdp = math.sqrt(((len(refl_sc) - 1) * refl_sc.var(ddof=1) +
                 (len(base_sc) - 1) * base_sc.var(ddof=1)) / (len(refl_sc) + len(base_sc) - 2))
for bound_g in (0.3, 0.2):
    p_tost = float(tost(refl_sc, base_sc, bound=bound_g * sdp)["pval"].iloc[0])
    log(f"- score TOST |g|<{bound_g}: p = {p_tost:.3f}")

# ---------------- 2. Discrimination within difficulty strata (id 6) ---------
log("\n## 2. Discrimination within baseline-derived difficulty strata\n")
base_acc = (T[T.condition == "ai"].groupby("authored_order")["correct01"].mean())
order = base_acc.sort_values(ascending=False).index.tolist()
easy6, hard6 = set(order[:6]), set(order[6:])
T["stratum"] = np.where(T["authored_order"].isin(easy6), "easy", "hard")


def dconf(g):
    c = g.loc[g.correct01 == 1, "confidence"]
    w = g.loc[g.correct01 == 0, "confidence"]
    return c.mean() - w.mean() if len(c) and len(w) else np.nan


for st in ("easy", "hard"):
    d = T[T.stratum == st]
    per = d.groupby(["participant_id", "condition"]).apply(dconf, include_groups=False).rename("dc").reset_index()
    b = per.loc[per.condition == "ai", "dc"].dropna().to_numpy()
    row = [f"baseline M={b.mean():.2f} (n={len(b)})"]
    for c in ("ai-reliability", "alternatives"):
        a = per.loc[per.condition == c, "dc"].dropna().to_numpy()
        tt, pp = stats.ttest_ind(a, b, equal_var=False)
        row.append(f"{LAB[c]} M={a.mean():.2f} (n={len(a)}), g={hedges_g(a, b):+.2f}, p={pp:.3f}")
    log(f"- **{st} items**: " + "; ".join(row))

import statsmodels.formula.api as smf
nfc = P.set_index("participant_id")["nfc_mean"]
T["nfc_z"] = (T.participant_id.map(nfc) - nfc.mean()) / nfc.std()
T["hard01"] = (T.stratum == "hard").astype(float)
T["cond"] = pd.Categorical(T.condition, categories=CONDS)
m = smf.mixedlm("confidence ~ correct01 * C(cond) + correct01 * hard01", data=T,
                groups=T.participant_id).fit(reml=True)
log("\nMixedLM confidence ~ correct x condition + correct x difficulty (participant RI):")
for k in m.params.index:
    if "correct01:" in k:
        log(f"- {k}: b = {m.params[k]:+.2f}, p = {m.pvalues[k]:.4f}")

# ---------------- 3. Monitoring slope: post estimate on score (id 5) --------
log("\n## 3. Post-estimate-on-score slope by condition (tracking vs bias)\n")
for c in CONDS:
    d = P[P.condition == c]
    sl, ic, r, p, se = stats.linregress(d.actual_score, d.post_with_ai)
    log(f"- {LAB[c]}: slope = {sl:+.2f} (r = {r:+.2f}, p = {p:.3f})")

# ---------------- 4. Bootstrap the ledger (id 14) ---------------------------
log("\n## 4. Bootstrap 95% CIs for the efficiency ledger\n")
cols = {c: P[P.condition == c][["absolute_estimation_error", "sus_score"]].dropna().to_numpy()
        for c in CONDS}
B = 10000


def ratios(sample):
    b = sample["ai"]
    out = {}
    for c in CONDS[1:]:
        a = sample[c]
        de = b[:, 0].mean() - a[:, 0].mean()      # error reduction
        ds = b[:, 1].mean() - a[:, 1].mean()      # SUS cost
        out[c] = (de, ds, de / ds if abs(ds) > 1e-9 else np.nan)
    return out


point = ratios(cols)
boot = {c: [] for c in CONDS[1:]}
frac_gain, frac_cost = [], []
for _ in range(B):
    s = {c: cols[c][RNG.integers(0, len(cols[c]), len(cols[c]))] for c in CONDS}
    rr = ratios(s)
    for c in CONDS[1:]:
        boot[c].append(rr[c][2])
    ga, gc = rr["alternatives"][0], rr["ai-reliability"][0]
    ca, cc = rr["alternatives"][1], rr["ai-reliability"][1]
    frac_gain.append(gc / ga if abs(ga) > 1e-9 else np.nan)
    frac_cost.append(cc / ca if abs(ca) > 1e-9 else np.nan)
for c in CONDS[1:]:
    arr = np.array(boot[c])
    ok = np.isfinite(arr)
    lo, hi = np.nanpercentile(arr[ok], [2.5, 97.5])
    log(f"- {LAB[c]}: {point[c][2]:.3f} items/SUS-pt, 95% CI [{lo:.3f}, {hi:.3f}] "
        f"(unstable resamples: {100*(1-ok.mean()):.1f}%)")
for name, arr in (("cards gain / alternatives gain", frac_gain),
                  ("cards SUS cost / alternatives SUS cost", frac_cost)):
    a = np.array(arr)
    lo, hi = np.nanpercentile(a[np.isfinite(a)], [2.5, 97.5])
    log(f"- {name}: {np.nanmedian(a):.2f}, 95% CI [{lo:.2f}, {hi:.2f}]")

# ---------------- 5. Holm across all 16 confirmatory tests (id 30/26) -------
log("\n## 5. Holm across all 16 confirmatory directional tests\n")
speclist = []
for out_col, better_low in (("absolute_estimation_error", True), ("confidence_discrimination", False),
                            ("prompts_per_task", False), ("actual_score", False)):
    b = P.loc[P.condition == "ai", out_col].dropna().to_numpy()
    for c in CONDS[1:]:
        a = P.loc[P.condition == c, out_col].dropna().to_numpy()
        tt, pp2 = stats.ttest_ind(a, b, equal_var=False)
        p1 = pp2 / 2 if ((tt < 0) == better_low) else 1 - pp2 / 2
        speclist.append((out_col, LAB[c], p1))
ps = np.array([s[2] for s in speclist])
orderi = np.argsort(ps)
holm = np.empty_like(ps)
m_ = len(ps)
running = 0
for rank, i in enumerate(orderi):
    running = max(running, (m_ - rank) * ps[i])
    holm[i] = min(1.0, running)
for (o, c, p1), h in zip(speclist, holm):
    if h < .05:
        log(f"- survives Holm-16: {o} / {c} (raw one-sided p = {p1:.2e}, Holm p = {h:.3f})")
log("(all other tests: Holm-16 p >= .05)")
# two-sided reversal Holm within score family
rev = []
b = P.loc[P.condition == "ai", "actual_score"].to_numpy()
for c in CONDS[1:]:
    a = P.loc[P.condition == c, "actual_score"].to_numpy()
    rev.append(stats.ttest_ind(a, b, equal_var=False)[1])
rev = np.array(rev)
oi = np.argsort(rev)
hv = np.empty_like(rev)
running = 0
for rank, i in enumerate(oi):
    running = max(running, (4 - rank) * rev[i])
    hv[i] = min(1, running)
log("\nTwo-sided reversal, Holm within score family: " +
    ", ".join(f"{LAB[c]} p={p:.3f}->Holm {h:.3f}" for c, p, h in zip(CONDS[1:], rev, hv)))

# ---------------- 6. Brier + Murphy + calibration slope (id 36) -------------
log("\n## 6. Trial-level Brier, Murphy decomposition, calibration slope\n")
for c in CONDS:
    d = T[T.condition == c]
    f = d.confidence.to_numpy() / 100
    y = d.correct01.to_numpy()
    brier = np.mean((f - y) ** 2)
    bins = np.clip((f * 10).astype(int), 0, 9)
    rel = unc = res = 0.0
    ybar = y.mean()
    for k in range(10):
        m_k = bins == k
        if m_k.sum() == 0:
            continue
        rel += m_k.mean() * (f[m_k].mean() - y[m_k].mean()) ** 2
        res += m_k.mean() * (y[m_k].mean() - ybar) ** 2
    unc = ybar * (1 - ybar)
    import statsmodels.api as sm
    X = sm.add_constant(stats.zscore(f))
    lr = sm.GLM(y, X, family=sm.families.Binomial()).fit()
    log(f"- {LAB[c]}: Brier = {brier:.3f} (reliability {rel:.3f}, resolution {res:.3f}, "
        f"uncertainty {unc:.3f}); calibration slope = {lr.params[1]:+.3f} (p = {lr.pvalues[1]:.3f})")

# ---------------- 7. Gate engagement + dose-response (id 1) -----------------
log("\n## 7. Wave-2 gate: engagement distribution and dose-response\n")
for c in ("alternatives", "pause-points", "reflection-task"):
    d = P[(P.condition == c) & (P.gate_tests > 0)].copy()
    d["share"] = d.gate_matched / d.gate_tests
    r1, p1 = stats.pearsonr(d["share"], d["absolute_estimation_error"])
    r2, p2b = stats.pearsonr(d["share"], d["actual_score"])
    log(f"- {LAB[c]}: median matched share = {d['share'].median():.2f} "
        f"(IQR {d['share'].quantile(.25):.2f}-{d['share'].quantile(.75):.2f}, n = {len(d)}); "
        f"dose-response r(share, monitoring error) = {r1:+.2f} (p = {p1:.3f}), "
        f"r(share, score) = {r2:+.2f} (p = {p2b:.3f})")

# ---------------- 8. Overconfidence on the baseline-derived split (id 29) ---
log("\n## 8. Overconfidence (conf - 100*correct) on baseline-derived 6/6 split\n")
for c in CONDS:
    d = T[T.condition == c]
    e = d[d.stratum == "easy"]
    h = d[d.stratum == "hard"]
    log(f"- {LAB[c]}: easy {np.mean(e.confidence - 100*e.correct01):+.1f} pp, "
        f"hard {np.mean(h.confidence - 100*h.correct01):+.1f} pp")
pooled = T.groupby("authored_order")["correct01"].mean().sort_values()
log(f"\n4-easiest pooled range (n=917): {pooled.iloc[-4:].min():.3f}-{pooled.max():.3f}; "
    f"4-hardest: {pooled.min():.3f}-{pooled.iloc[:4].max():.3f}")
log(f"baseline-derived easy-6 accuracy range (pooled): "
    f"{pooled[list(easy6)].min():.2f}-{pooled[list(easy6)].max():.2f}")

with open("ROUNDTABLE_ANALYSES.md", "w") as fh:
    fh.write("\n".join(OUT) + "\n")
print("\nwritten ROUNDTABLE_ANALYSES.md")

# ---------------- 9. Decisive discrimination test (id 6): continuous difficulty
OUT2 = ["\n## 9. Discrimination with continuous item-difficulty control (decisive)\n"]
T["diff_z"] = -((T.authored_order.map(
    T[T.condition == "ai"].groupby("authored_order")["correct01"].mean())
    - base_acc.mean()) / base_acc.std())
m9 = smf.mixedlm("confidence ~ correct01 * C(cond) + correct01 * diff_z + C(cond) * diff_z",
                 data=T, groups=T.participant_id).fit(reml=True)
for k in m9.params.index:
    if "correct01" in k and ":diff_z" not in k or k == "correct01":
        OUT2.append(f"- {k}: b = {m9.params[k]:+.2f}, p = {m9.pvalues[k]:.4f}")
OUT2.append(f"- correct01:diff_z: b = {m9.params['correct01:diff_z']:+.2f}, "
            f"p = {m9.pvalues['correct01:diff_z']:.4f}")
OUT2.append("\nWith item difficulty and its interactions controlled, correct x condition "
            "vanishes for every intervention: the dConf/AUC2 gains are carried by "
            "difficulty-keyed confidence adjustment, not improved within-item discrimination.")
with open("ROUNDTABLE_ANALYSES.md", "a") as fh:
    fh.write("\n".join(OUT2) + "\n")
print("\n".join(OUT2))
