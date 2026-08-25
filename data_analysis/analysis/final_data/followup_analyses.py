#!/usr/bin/env python3
"""
Follow-up analyses for the MET-AI Interventions final dataset (meeting action items).

  A. Temporal: accuracy over presentation position; halves/thirds; contrasts excluding trial 1
  B. Easy vs hard items x condition (difficulty defined on the baseline condition only)
  C. Dunning-Kruger effect across conditions (+ regression-artifact checks)
  D. Trial-level mixed models (participant random effect, NFC covariate)
  E. Bayesian assertion of the performance null (JZS Bayes factors + TOST equivalence)

Reads notebook_analysis_output/{participant_metrics,task_metrics}.csv
(run deep_analysis_notebook.ipynb first). Prints results; writes summary CSVs
to notebook_analysis_output/.
"""

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests
import pingouin as pg
import warnings
warnings.filterwarnings("ignore")

OUT = "notebook_analysis_output"
CONDS = ["ai", "ai-reliability", "alternatives", "pause-points", "reflection-task"]
INTERVENTIONS = CONDS[1:]
BASELINE = "ai"

pm = pd.read_csv(f"{OUT}/participant_metrics.csv")
tm = pd.read_csv(f"{OUT}/task_metrics.csv")
df = pm[pm["exclude_primary"] == False].copy()
keep = set(df["participant_id"])
tm = tm[tm["participant_id"].isin(keep)].copy()

# Presentation position 1-12 = rank of interface slot within participant (order randomized)
tm["pos"] = tm.groupby("participant_id")["display_index"].rank().astype(int)
tm = tm.merge(df[["participant_id", "nfc_mean"]], on="participant_id", how="left")

def hedges_g(x, y):
    nx, ny = len(x), len(y)
    sp2 = ((nx - 1) * np.var(x, ddof=1) + (ny - 1) * np.var(y, ddof=1)) / (nx + ny - 2)
    J = 1 - 3 / (4 * (nx + ny) - 9)
    g = (np.mean(x) - np.mean(y)) / np.sqrt(sp2) * J
    se = np.sqrt((nx + ny) / (nx * ny) + g**2 / (2 * (nx + ny - 2)))
    return g, g - 1.96 * se, g + 1.96 * se

def fmt_p(p):
    if p < 0.001:
        return "< .001"
    if p > 0.999:
        return "> .999"
    return f"= .{f'{p:.3f}'.split('.')[1]}"

# =====================================================================================
print("=" * 92)
print("A. TEMPORAL ANALYSIS - does performance change over the 12 trials?")
print("=" * 92)

print("\nA1. Accuracy by presentation position (pooled):")
by_pos = tm.groupby("pos")["correct"].mean()
print("  " + "  ".join(f"{p}:{v:.3f}" for p, v in by_pos.items()))

print("\nA2. GEE logistic slope of accuracy on position (per condition, cluster = participant):")
slope_rows = []
for cond in CONDS:
    d = tm[tm["condition"] == cond].copy()
    d["pos_c"] = d["pos"] - 6.5
    m = sm.GEE.from_formula("correct ~ pos_c", groups="participant_id", data=d,
                            family=sm.families.Binomial(),
                            cov_struct=sm.cov_struct.Exchangeable()).fit()
    b, p = m.params["pos_c"], m.pvalues["pos_c"]
    slope_rows.append({"condition": cond, "logit_slope_per_pos": b,
                       "OR_per_pos": np.exp(b), "p": p})
    print(f"  {cond:18s} b = {b:+.4f}  OR/position = {np.exp(b):.3f}  p {fmt_p(p)}")

d_all = tm.copy(); d_all["pos_c"] = d_all["pos"] - 6.5
m_int = sm.GEE.from_formula("correct ~ C(condition, Treatment('ai')) * pos_c",
                            groups="participant_id", data=d_all,
                            family=sm.families.Binomial(),
                            cov_struct=sm.cov_struct.Exchangeable()).fit()
wt = m_int.wald_test_terms(skip_single=False, scalar=True).table
int_row = wt.loc[[i for i in wt.index if ":" in i][0]] if any(":" in i for i in wt.index) else None
int_name = [i for i in wt.index if ":" in i][0]
print(f"  Condition x position interaction: chi2({int(wt.loc[int_name,'df_constraint'])}) = "
      f"{wt.loc[int_name,'statistic']:.2f}, p {fmt_p(wt.loc[int_name,'pvalue'])}")

print("\nA3. Halves (positions 1-6 vs 7-12) - paired t within participant, per condition:")
acc_halves = tm.assign(half=np.where(tm["pos"] <= 6, "h1", "h2")) \
               .pivot_table(index=["participant_id", "condition"], columns="half", values="correct")
acc_halves = acc_halves.reset_index()
for cond in CONDS:
    d = acc_halves[acc_halves["condition"] == cond]
    t, p = stats.ttest_rel(d["h1"], d["h2"])
    print(f"  {cond:18s} M1 = {d['h1'].mean():.3f}  M2 = {d['h2'].mean():.3f}  "
          f"diff = {d['h2'].mean()-d['h1'].mean():+.3f}  t({len(d)-1}) = {t:+.2f}  p {fmt_p(p)}")
print("  (pooled thirds 1-4 / 5-8 / 9-12):")
tm["third"] = pd.cut(tm["pos"], [0, 4, 8, 12], labels=["T1", "T2", "T3"])
th = tm.groupby(["condition", "third"], observed=True)["correct"].mean().unstack()
for cond in CONDS:
    print(f"  {cond:18s} " + "  ".join(f"{c}: {th.loc[cond, c]:.3f}" for c in ["T1", "T2", "T3"]))

print("\nA4. Confirmatory score contrasts EXCLUDING trial 1 (score over positions 2-12, 0-11):")
s11 = tm[tm["pos"] > 1].groupby("participant_id")["correct"].sum().rename("score11")
df = df.merge(s11, on="participant_id")
base11 = df.loc[df["condition"] == BASELINE, "score11"]
base12 = df.loc[df["condition"] == BASELINE, "actual_score"]
rows = []
for cond in INTERVENTIONS:
    x11 = df.loc[df["condition"] == cond, "score11"]
    x12 = df.loc[df["condition"] == cond, "actual_score"]
    g11, _, _ = hedges_g(x11, base11)
    g12, _, _ = hedges_g(x12, base12)
    t, p = stats.ttest_ind(x11, base11, equal_var=False, alternative="greater")
    rows.append({"cond": cond, "g_full": g12, "g_excl1": g11, "p_dir": p})
for r in rows:
    print(f"  {r['cond']:18s} g(12 trials) = {r['g_full']:+.3f}   g(trials 2-12) = {r['g_excl1']:+.3f}"
          f"   directional p {fmt_p(r['p_dir'])}")
aov11 = pg.welch_anova(data=df, dv="score11", between="condition")
print(f"  Welch ANOVA on score(2-12): F({aov11['ddof1'][0]:.0f}, {aov11['ddof2'][0]:.1f}) = "
      f"{aov11['F'][0]:.2f}, p {fmt_p(aov11['p_unc'][0])}")
pd.DataFrame(slope_rows).to_csv(f"{OUT}/followup_temporal_slopes.csv", index=False)

# =====================================================================================
print("\n" + "=" * 92)
print("B. EASY vs HARD ITEMS x CONDITION (difficulty from BASELINE condition only)")
print("=" * 92)

base_p = tm[tm["condition"] == BASELINE].groupby("task_name")["correct"].mean()
median_p = base_p.median()
easy_items = set(base_p[base_p >= median_p].index)
hard_items = set(base_p[base_p < median_p].index)
tm["hard"] = tm["task_name"].isin(hard_items).astype(int)
tm["base_difficulty"] = tm["task_name"].map(1 - base_p)  # higher = harder
print(f"\nEasy (baseline p >= {median_p:.3f}): {sorted(easy_items)}")
print(f"Hard: {sorted(hard_items)}")

acc_eh = tm.pivot_table(index=["participant_id", "condition"], columns="hard",
                        values="correct").rename(columns={0: "acc_easy", 1: "acc_hard"}).reset_index()
print("\nB1. Accuracy by condition and difficulty half:")
print(f"  {'condition':18s} {'easy':>7s} {'hard':>7s} {'gap':>7s}")
for cond in CONDS:
    d = acc_eh[acc_eh["condition"] == cond]
    print(f"  {cond:18s} {d['acc_easy'].mean():7.3f} {d['acc_hard'].mean():7.3f} "
          f"{d['acc_easy'].mean()-d['acc_hard'].mean():7.3f}")

print("\nB2. Welch t vs baseline separately on easy and hard sets (two-sided, Holm within set):")
for setname, col in [("EASY", "acc_easy"), ("HARD", "acc_hard")]:
    base = acc_eh.loc[acc_eh["condition"] == BASELINE, col]
    ps, out = [], []
    for cond in INTERVENTIONS:
        x = acc_eh.loc[acc_eh["condition"] == cond, col]
        t, p = stats.ttest_ind(x, base, equal_var=False)
        g, lo, hi = hedges_g(x, base)
        ps.append(p); out.append((cond, x.mean(), g, p))
    holm = multipletests(ps, method="holm")[1]
    print(f"  {setname} (baseline M = {base.mean():.3f}):")
    for (cond, m, g, p), ph in zip(out, holm):
        sig = "*" if ph < 0.05 else " "
        print(f"    {cond:18s} M = {m:.3f}  g = {g:+.3f}  p {fmt_p(p)}  Holm p {fmt_p(ph)} {sig}")

print("\nB3. Formal interaction (GEE logit, cluster = participant):")
m_eh = sm.GEE.from_formula("correct ~ C(condition, Treatment('ai')) * hard",
                           groups="participant_id", data=tm,
                           family=sm.families.Binomial(),
                           cov_struct=sm.cov_struct.Exchangeable()).fit()
wt = m_eh.wald_test_terms(skip_single=False, scalar=True).table
iname = [i for i in wt.index if ":" in i][0]
print(f"  Omnibus condition x difficulty: chi2({int(wt.loc[iname,'df_constraint'])}) = "
      f"{wt.loc[iname,'statistic']:.2f}, p {fmt_p(wt.loc[iname,'pvalue'])}")
for cond in INTERVENTIONS:
    term = f"C(condition, Treatment('ai'))[T.{cond}]:hard"
    print(f"    {cond:18s} interaction b = {m_eh.params[term]:+.3f} (log-odds)  p {fmt_p(m_eh.pvalues[term])}")

# =====================================================================================
print("\n" + "=" * 92)
print("C. DUNNING-KRUGER ACROSS CONDITIONS")
print("=" * 92)

# Within-condition percentile rank of actual score; perceived percentile from post estimate
df["actual_pct"] = df.groupby("condition")["actual_score"] \
                     .transform(lambda s: stats.rankdata(s, method="average") / len(s) * 100)
df["perceived_pct"] = df["post_self_percentile"]
df["quartile"] = df.groupby("condition")["actual_pct"] \
                   .transform(lambda s: pd.qcut(s, 4, labels=["Q1", "Q2", "Q3", "Q4"]))

print("\nC1. Perceived vs actual percentile by within-condition score quartile:")
print(f"  {'condition':18s} " + " | ".join(f"{q}: act->perc (gap)" for q in ["Q1", "Q2", "Q3", "Q4"]))
dk_rows = []
for cond in CONDS:
    d = df[df["condition"] == cond]
    cells = []
    for q in ["Q1", "Q2", "Q3", "Q4"]:
        dq = d[d["quartile"] == q]
        a, p_ = dq["actual_pct"].mean(), dq["perceived_pct"].mean()
        cells.append(f"{a:4.1f}->{p_:4.1f} ({p_-a:+5.1f})")
        dk_rows.append({"condition": cond, "quartile": q, "n": len(dq),
                        "actual_pct": a, "perceived_pct": p_, "gap": p_ - a})
    print(f"  {cond:18s} " + " | ".join(cells))
pd.DataFrame(dk_rows).to_csv(f"{OUT}/followup_dunning_kruger.csv", index=False)

print("\nC2. Does condition modulate the DK slope? OLS perceived_pct ~ actual_pct x condition (HC3):")
m_dk = smf.ols("perceived_pct ~ actual_pct * C(condition, Treatment('ai'))", data=df) \
          .fit(cov_type="HC3")
wt = m_dk.wald_test_terms(skip_single=False, scalar=True).table
iname = [i for i in wt.index if ":" in i][0]
print(f"  Interaction: F-equiv chi2({int(wt.loc[iname,'df_constraint'])}) = "
      f"{wt.loc[iname,'statistic']:.2f}, p {fmt_p(wt.loc[iname,'pvalue'])}")
b0 = m_dk.params["actual_pct"]
print(f"  Baseline slope (perceived on actual pct): b = {b0:.3f} (1.0 = perfect calibration)")
for cond in INTERVENTIONS:
    term = f"actual_pct:C(condition, Treatment('ai'))[T.{cond}]"
    print(f"    {cond:18s} slope shift = {m_dk.params[term]:+.3f}  p {fmt_p(m_dk.pvalues[term])}")

print("\nC3. Bottom-quartile miscalibration (the classic DK cell) by condition, Welch vs baseline:")
q1 = df[df["quartile"] == "Q1"]
base_gap = q1.loc[q1["condition"] == BASELINE, "perceived_pct"] - \
           q1.loc[q1["condition"] == BASELINE, "actual_pct"]
for cond in INTERVENTIONS:
    gp = q1.loc[q1["condition"] == cond, "perceived_pct"] - q1.loc[q1["condition"] == cond, "actual_pct"]
    t, p = stats.ttest_ind(gp, base_gap, equal_var=False)
    g, _, _ = hedges_g(gp, base_gap)
    print(f"  {cond:18s} Q1 gap = {gp.mean():+5.1f} (baseline {base_gap.mean():+5.1f})  "
          f"g = {g:+.2f}  p {fmt_p(p)}")

print("\nC4. Regression-artifact checks (Gignac & Zajenkowski 2020), pooled:")
df["score_z"] = (df["actual_score"] - df["actual_score"].mean()) / df["actual_score"].std()
m_quad = smf.ols("perceived_pct ~ score_z + I(score_z**2)", data=df).fit(cov_type="HC3")
print(f"  Quadratic term: b = {m_quad.params['I(score_z ** 2)']:+.3f}  "
      f"p {fmt_p(m_quad.pvalues['I(score_z ** 2)'])} "
      f"(n.s. = linear relation, consistent with regression-to-mean account)")
m_lin = smf.ols("perceived_pct ~ score_z", data=df).fit()
bp = sm.stats.diagnostic.het_breuschpagan(m_lin.resid, m_lin.model.exog)
print(f"  Breusch-Pagan heteroscedasticity: LM = {bp[0]:.2f}, p {fmt_p(bp[1])} "
      f"(sig = error variance differs across ability, the DK-as-artifact signature)")
r_dk = stats.pearsonr(df["actual_score"], df["signed_estimation_error"])
print(f"  Score x signed error (items): r = {r_dk[0]:.3f}, p {fmt_p(r_dk[1])}")

# =====================================================================================
print("\n" + "=" * 92)
print("D. TRIAL-LEVEL MIXED MODELS (participant random effect, NFC covariate)")
print("=" * 92)

tm["hard_z"] = (tm["base_difficulty"] - tm["base_difficulty"].mean()) / tm["base_difficulty"].std()
tm["pos_z"] = (tm["pos"] - tm["pos"].mean()) / tm["pos"].std()
tm["nfc_z"] = (tm["nfc_mean"] - tm["nfc_mean"].mean()) / tm["nfc_mean"].std()

print("\nD1. Confidence (0-100): MixedLM with random intercept per participant")
m_conf = smf.mixedlm("confidence ~ C(condition, Treatment('ai')) * hard_z + pos_z + nfc_z",
                     data=tm, groups=tm["participant_id"]).fit(reml=False)
print(f"  {'term':52s} {'b':>8s} {'p':>9s}")
for term in m_conf.params.index:
    if term in ("Group Var",):
        continue
    print(f"  {term:52s} {m_conf.params[term]:+8.2f}  {fmt_p(m_conf.pvalues[term]):>8s}")
icc = m_conf.cov_re.iloc[0, 0] / (m_conf.cov_re.iloc[0, 0] + m_conf.scale)
print(f"  ICC(participant) = {icc:.3f}")

print("\nD2. Accuracy (0/1): GEE logit, exchangeable working correlation, robust SE")
m_acc = sm.GEE.from_formula("correct ~ C(condition, Treatment('ai')) * hard_z + pos_z + nfc_z",
                            groups="participant_id", data=tm,
                            family=sm.families.Binomial(),
                            cov_struct=sm.cov_struct.Exchangeable()).fit()
print(f"  {'term':52s} {'OR':>7s} {'p':>9s}")
for term in m_acc.params.index:
    print(f"  {term:52s} {np.exp(m_acc.params[term]):7.3f}  {fmt_p(m_acc.pvalues[term]):>8s}")

print("\nD3. Robustness: Bayesian random-intercept logit (statsmodels BinomialBayesMixedGLM, VB)")
from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
mb = BinomialBayesMixedGLM.from_formula(
    "correct ~ C(condition, Treatment('ai')) + hard_z + pos_z + nfc_z",
    {"participant": "0 + C(participant_id)"}, tm).fit_vb()
names = mb.model.exog_names
for nm, mean, sd in zip(names, mb.fe_mean, mb.fe_sd):
    print(f"  {nm:52s} b = {mean:+.3f} (sd {sd:.3f})")

# =====================================================================================
print("\n" + "=" * 92)
print("E. ASSERTING THE PERFORMANCE NULL - JZS Bayes factors and TOST equivalence")
print("=" * 92)

print(f"\n  {'intervention':18s} {'diff':>6s} {'g':>7s} {'p(2s)':>8s} {'BF01':>7s} "
      f"{'TOST p (|g|<.3)':>16s} {'TOST p (|g|<.2)':>16s}")
base = df.loc[df["condition"] == BASELINE, "actual_score"].values
bf_rows = []
for cond in INTERVENTIONS:
    x = df.loc[df["condition"] == cond, "actual_score"].values
    nx, ny = len(x), len(base)
    t_pooled, p2 = stats.ttest_ind(x, base, equal_var=True)
    bf10 = float(pg.bayesfactor_ttest(t_pooled, nx, ny, paired=False, r=0.707))
    g, _, _ = hedges_g(x, base)
    # Welch TOST at |g| < bound
    sp = np.sqrt(((nx-1)*np.var(x, ddof=1) + (ny-1)*np.var(base, ddof=1)) / (nx+ny-2))
    se_w = np.sqrt(np.var(x, ddof=1)/nx + np.var(base, ddof=1)/ny)
    dfw = se_w**4 / ((np.var(x, ddof=1)/nx)**2/(nx-1) + (np.var(base, ddof=1)/ny)**2/(ny-1))
    diff = np.mean(x) - np.mean(base)
    tost_ps = {}
    for bound_g in (0.3, 0.2):
        delta = bound_g * sp
        t_low = (diff + delta) / se_w   # H0: diff <= -delta
        t_up  = (diff - delta) / se_w   # H0: diff >= +delta
        p_low = 1 - stats.t.cdf(t_low, dfw)
        p_up  = stats.t.cdf(t_up, dfw)
        tost_ps[bound_g] = max(p_low, p_up)
    bf01 = 1.0 / bf10
    bf_rows.append({"condition": cond, "diff": diff, "g": g, "p_two_sided": p2,
                    "BF01": bf01, "tost_p_g03": tost_ps[0.3], "tost_p_g02": tost_ps[0.2]})
    print(f"  {cond:18s} {diff:+6.2f} {g:+7.3f} {fmt_p(p2):>8s} {bf01:7.2f} "
          f"{fmt_p(tost_ps[0.3]):>16s} {fmt_p(tost_ps[0.2]):>16s}")
print("\n  E2. Directional Bayes factors vs the preregistered H1 (intervention > baseline):")
from scipy.integrate import quad
from scipy.stats import nct as nct_dist, t as t_dist, cauchy
for i, cond in enumerate(INTERVENTIONS):
    x = df.loc[df["condition"] == cond, "actual_score"].values
    nx, ny = len(x), len(base)
    t_obs, _ = stats.ttest_ind(x, base, equal_var=True)
    dfree = nx + ny - 2
    neff = nx * ny / (nx + ny)
    r_scale = 0.707
    def integrand(delta):
        try:
            like = nct_dist.pdf(t_obs, dfree, delta * np.sqrt(neff))
        except (OverflowError, FloatingPointError):
            like = 0.0
        if not np.isfinite(like):
            like = 0.0
        return like * 2 * cauchy.pdf(delta, 0, r_scale)
    # finite range: at delta > 2 the likelihood of these t values is ~0 and Cauchy mass is small
    m1, _ = quad(integrand, 0, 2.0, limit=400)
    m0 = t_dist.pdf(t_obs, dfree)
    bf_plus0 = m1 / m0
    bf0_plus = 1.0 / bf_plus0
    bf_rows[i]["BF0plus"] = bf0_plus
    print(f"    {cond:18s} BF0+ = {bf0_plus:8.1f}   "
          f"(evidence for 'no improvement' over 'improvement')")
pd.DataFrame(bf_rows).to_csv(f"{OUT}/followup_bayes_null.csv", index=False)
print("""
  Reading: BF01 > 3 = moderate evidence FOR the null (no difference); BF01 < 1/3 = evidence
  AGAINST it. TOST p < .05 = the effect is statistically within +/-bound (equivalence).
""")
print("Done. CSVs written to notebook_analysis_output/followup_*.csv")
