"""APA-style inferential statistics for the empirical study (Robin's review, 2026-09-05).

Testing logic per outcome (paper), with robustness variants kept alongside:
  1. One-way ANOVA across the five conditions (F, df1, df2, p, omega^2); Welch ANOVA and Levene's test as checks.
  2. Post-hoc: Tukey HSD all pairs (t, df, corrected p, Hedges g); Games-Howell as check.
  3. Uncorrected two-sided pooled-variance t against baseline (t, df, p, g [95% CI]); Welch t kept under "welch".
  4. Default (JZS) Bayesian one-way ANOVA (Rouder et al., 2012): BF10 for the condition
     effect, r_fixed = 0.5 ("medium"), integrated numerically; BIC approximation as a check.
     Validated against pingouin (k = 2) and BayesFactor::anovaBF (publication_ready/replicate.R).

Reliance (verdict parse, verdict_parse.py):
  - per-participant follow rate ~ condition (OLS, baseline reference) + Welch ANOVA
  - trial-level GEE logit: followed ~ condition, followed ~ condition x AI-correct,
    followed ~ condition x item difficulty (exchangeable, clustered by participant)

Outputs: APA_RESULTS.md (tables) and apa_results.json (all numbers) next to this file.

Run:  ../../../.venv/bin/python apa_results.py
"""
import json
import math
import os
import sys
import warnings

import numpy as np
import pandas as pd
import pingouin as pg
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import integrate, stats

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.environ.get("MET_DATA_DIR", os.path.join(HERE, "notebook_analysis_output"))
sys.path.insert(0, HERE)

COND_ORDER = ["ai", "ai-reliability", "alternatives", "pause-points", "reflection-task"]
LABEL = {"ai": "Baseline", "ai-reliability": "Reliability cards", "alternatives": "Contrasting replies",
         "pause-points": "Pause points", "reflection-task": "Reflection"}
OUTCOMES = [  # column, label, family
    ("absolute_estimation_error", "Estimation error (abs.)", "primary"),
    ("signed_estimation_error", "Estimation error (signed)", "primary-aux"),
    ("confidence_discrimination", "Confidence discrimination (pp)", "primary"),
    ("actual_score", "Score (0-12)", "primary"),
    ("prompts_per_task", "Prompts per problem", "primary"),
    ("sus_score", "SUS", "experience"),
    ("ueq_overall", "UEQ-S", "experience"),
    ("tlx_mean", "NASA-TLX", "experience"),
    ("trust_mean", "Trust", "experience"),
]


# ----------------------------------------------------------------------------- helpers
def hedges_g(x, y):
    g = pg.compute_effsize(x, y, eftype="hedges")
    lo, hi = pg.compute_esci(stat=g, nx=len(x), ny=len(y), eftype="hedges", confidence=0.95)
    return g, lo, hi


def welch_t(x, y):
    """Two-sided Welch t of x (intervention) vs y (baseline)."""
    t = pg.ttest(x, y, correction=True).iloc[0]
    return float(t["T"]), float(t["dof"]), float(t["p_val"])


def student_t(x, y):
    """Two-sided pooled-variance (Student) t of x (intervention) vs y (baseline)."""
    t = pg.ttest(x, y, correction=False).iloc[0]
    return float(t["T"]), float(t["dof"]), float(t["p_val"])


def omega_sq(df, dv):
    a = pg.anova(data=df, dv=dv, between="condition", detailed=True)
    ss_b, ss_w = a.loc[0, "SS"], a.loc[1, "SS"]
    df_b, df_w = a.loc[0, "DF"], a.loc[1, "DF"]
    ms_w = ss_w / df_w
    return float((ss_b - df_b * ms_w) / (ss_b + ss_w + ms_w))


def jzs_anova_bf10(y, groups, r=0.5):
    """Rouder et al. (2012) default Bayes factor for a one-way fixed-effects ANOVA.

    Model: y = mu + X theta + e, theta ~ N(0, g sigma^2 I) on the (k-1)-dim orthonormal
    sum-to-zero contrast space, g ~ InvGamma(1/2, r^2/2), Jeffreys prior on sigma^2, flat on mu.
    Returns BF10 (evidence for a condition effect). For k = 2 this equals the JZS t-test BF
    with scale r*sqrt(2), which validate() checks against pingouin.
    """
    y = np.asarray(y, float)
    groups = pd.Categorical(groups)
    k = len(groups.categories)
    N = len(y)
    D = pd.get_dummies(groups).values.astype(float)  # N x k indicator
    # orthonormal basis Q (k x (k-1)) of the sum-to-zero subspace
    Q, _ = np.linalg.qr(np.eye(k) - 1.0 / k)
    Q = Q[:, :k - 1]
    X = D @ Q
    X = X - X.mean(axis=0)  # remove intercept direction
    yc = y - y.mean()
    XtX = X.T @ X
    Xty = X.T @ yc
    sst = float(yc @ yc)
    p = k - 1

    def log_bf_g(g):
        M = np.eye(p) + g * XtX
        sign, logdet = np.linalg.slogdet(M)
        quad = float(Xty @ np.linalg.solve(XtX + np.eye(p) / g, Xty))
        return -0.5 * logdet - 0.5 * (N - 1) * np.log((sst - quad) / sst)

    a, b = 0.5, r ** 2 / 2  # InvGamma(shape a, scale b)

    def integrand(u):  # u = log g
        g = np.exp(u)
        log_prior = a * np.log(b) - math.lgamma(a) - (a + 1) * np.log(g) - b / g
        return np.exp(log_bf_g(g) + log_prior + u)  # + u: Jacobian of g = e^u

    val, _ = integrate.quad(integrand, -30, 30, limit=400)
    return float(val)


def jzs_ttest_bf10(t, nx, ny, r=0.707, alternative="two-sided"):
    """JZS Bayes factor for an independent-samples t statistic (Rouder et al., 2009), by numerical
    integration of the noncentral-t likelihood over a Cauchy(0, r) prior on the standardized effect.
    alternative="greater" restricts the prior to delta > 0 (the "improvement" alternative), matching
    BayesFactor::ttestBF(nullInterval = c(0, Inf)). Returns BF10 (or BF+0)."""
    dfree, neff = nx + ny - 2, nx * ny / (nx + ny)
    lo_v, hi_v = max(0.0, dfree - 12 * np.sqrt(2 * dfree)), dfree + 12 * np.sqrt(2 * dfree)

    def nct_pdf(ncp):  # noncentral-t density at t via its chi-square mixture; stable for large df
        f = lambda v: np.exp(stats.chi2.logpdf(v, dfree) + stats.norm.logpdf(t * np.sqrt(v / dfree) - ncp)) * np.sqrt(v / dfree)
        return integrate.quad(f, lo_v, hi_v, limit=200)[0]

    def integrand(d):
        return nct_pdf(d * np.sqrt(neff)) * stats.cauchy.pdf(d, scale=r)

    if alternative == "two-sided":
        num = integrate.quad(integrand, -3, 3, limit=200)[0]
    else:
        num = integrate.quad(integrand, 0, 3, limit=200)[0] / 0.5
    return float(num / stats.t.pdf(t, dfree))


def bic_bf01(df, dv):
    """Wagenmakers (2007) BIC approximation: BF01 = exp((BIC1 - BIC0)/2)."""
    m0 = smf.ols(f"{dv} ~ 1", data=df).fit()
    m1 = smf.ols(f"{dv} ~ C(condition)", data=df).fit()
    return float(np.exp((m1.bic - m0.bic) / 2))


def validate():
    """k = 2 check: ANOVA BF (r = 0.5) must equal the JZS t-test BF (r = 0.707)."""
    rng = np.random.default_rng(1)
    x = rng.normal(0, 1, 180)
    y = rng.normal(0.25, 1, 185)
    yy = np.concatenate([x, y])
    gg = np.array(["a"] * 180 + ["b"] * 185)
    bf_anova = jzs_anova_bf10(yy, gg, r=0.5)
    t, _, _ = welch_t(x, y)
    t_student = stats.ttest_ind(x, y).statistic
    bf_t = float(pg.bayesfactor_ttest(t_student, nx=180, ny=185, paired=False, r=0.5 * np.sqrt(2)))
    return bf_anova, bf_t


# ----------------------------------------------------------------------------- outcomes
def analyse_outcome(df, col):
    res = {"outcome": col}
    d = df[["condition", col]].dropna()
    d["condition"] = pd.Categorical(d["condition"], COND_ORDER)
    w = pg.welch_anova(data=d, dv=col, between="condition").iloc[0]
    res["welch"] = {"F": float(w["F"]), "df1": float(w["ddof1"]), "df2": float(w["ddof2"]),
                    "p": float(w["p_unc"]), "omega2": omega_sq(d, col)}
    a = pg.anova(data=d, dv=col, between="condition", detailed=True)
    res["anova"] = {"F": float(a.loc[0, "F"]), "df1": float(a.loc[0, "DF"]), "df2": float(a.loc[1, "DF"]),
                    "p": float(a.loc[0, "p_unc"]), "omega2": omega_sq(d, col), "eta2p": float(a.loc[0, "np2"])}
    bf_lev = pg.homoscedasticity(data=d, dv=col, group="condition", method="levene").iloc[0]
    res["levene"] = {"W": float(bf_lev["W"]), "p": float(bf_lev["pval"])}
    res["desc"] = {c: {"n": int(len(g)), "M": float(g.mean()), "SD": float(g.std(ddof=1))}
                   for c, g in d.groupby("condition", observed=True)[col]}
    # Games-Howell post hoc
    gh = pg.pairwise_gameshowell(data=d, dv=col, between="condition")
    res["games_howell"] = [{"A": r.A, "B": r.B, "t": float(r["T"]), "df": float(r["df"]),
                            "p": float(r["pval"]), "g": float(r["hedges"])} for _, r in gh.iterrows()]
    tk = pg.pairwise_tukey(data=d, dv=col, between="condition")
    res["tukey"] = [{"A": r.A, "B": r.B, "t": float(r["T"]), "df": float(len(d) - len(COND_ORDER)),
                     "p": float(r["p_tukey"]), "g": float(r["hedges"])} for _, r in tk.iterrows()]
    # uncorrected baseline contrasts
    base = d.loc[d.condition == "ai", col].values
    res["vs_baseline"] = {}
    for c in COND_ORDER[1:]:
        x = d.loc[d.condition == c, col].values
        t, dof, p = welch_t(x, base)
        ts, dofs, ps = student_t(x, base)
        g, lo, hi = hedges_g(x, base)
        res["vs_baseline"][c] = {"t": ts, "df": dofs, "p": ps, "g": g, "ci": [lo, hi],
                                 "welch": {"t": t, "df": dof, "p": p}}
    # Bayesian ANOVA
    bf10 = jzs_anova_bf10(d[col].values, d["condition"].astype(str).values, r=0.5)
    res["bayes"] = {"BF10": bf10, "BF01": 1 / bf10, "BF01_bic": bic_bf01(d, col)}
    return res


# ----------------------------------------------------------------------------- reliance
def reliance(df):
    try:  # full parse from the raw chat logs (needs data_analysis/raw_data)
        import verdict_parse as vp
        trials = vp.run_parse()
        T = pd.DataFrame([{k: v for k, v in t.items() if k != "exchanges"} for t in trials])
        T["parsed"] = T["verdict"].notna()
        P = T[T.parsed].copy()
        P["followed"] = (P["answer"] == P["verdict"]).astype(int)
        P["ai_correct"] = (P["verdict"] == P["correct_option"]).astype(int)
        P["correct"] = P["answer_correct"].astype(int)
        coverage = {c: float(T[T.condition == c].parsed.mean()) for c in COND_ORDER}
    except Exception:  # publication folder: use the exported per-trial parse
        P = pd.read_csv(os.path.join(NB, "reliance_trials.csv"))
        n_trials = {c: 12 * int((df.condition == c).sum()) for c in COND_ORDER}
        coverage = {c: float((P.condition == c).sum() / n_trials[c]) for c in COND_ORDER}
    # item difficulty from baseline accuracy (all baseline trials, parsed or not)
    tm = pd.read_csv(os.path.join(NB, "task_metrics.csv"))
    inc = set(df.participant_id)
    tm = tm[tm.participant_id.isin(inc)]
    base_acc = tm[tm.condition == "ai"].groupby("task_name")["correct"].mean()
    P["difficulty_z"] = -((P["question"].map(base_acc) - base_acc.mean()) / base_acc.std(ddof=1))
    P["condition"] = pd.Categorical(P["condition"], COND_ORDER)

    out = {"coverage": coverage, "by_condition": {}}
    for c in COND_ORDER:
        pc = P[P.condition == c]
        fol = pc[pc.followed == 1]
        ovr = pc[pc.followed == 0]
        out["by_condition"][c] = {
            "n_parsed": int(len(pc)), "follow_rate": float(pc.followed.mean()),
            "follow_given_ai_correct": float(pc.loc[pc.ai_correct == 1, "followed"].mean()),
            "follow_given_ai_wrong": float(pc.loc[pc.ai_correct == 0, "followed"].mean()),
            "follow_success": float(fol.correct.mean()) if len(fol) else None,
            "override_success": float(ovr.correct.mean()) if len(ovr) else None,
            "ai_accuracy": float(pc.ai_correct.mean()),
        }
    # per-participant follow rate: OLS with baseline reference + Welch ANOVA
    pp = P.groupby(["pid", "condition"], observed=True)["followed"].agg(["mean", "size"]).reset_index()
    pp = pp.rename(columns={"mean": "follow_rate"})
    pp["condition"] = pd.Categorical(pp["condition"].astype(str), COND_ORDER)
    ols = smf.ols("follow_rate ~ C(condition, Treatment('ai'))", data=pp).fit()
    w = pg.welch_anova(data=pp, dv="follow_rate", between="condition").iloc[0]
    a = pg.anova(data=pp, dv="follow_rate", between="condition", detailed=True)
    out["participant_level"] = {
        "welch": {"F": float(w["F"]), "df1": float(w["ddof1"]), "df2": float(w["ddof2"]), "p": float(w["p_unc"])},
        "anova": {"F": float(a.loc[0, "F"]), "df1": float(a.loc[0, "DF"]), "df2": float(a.loc[1, "DF"]), "p": float(a.loc[0, "p_unc"]),
                  "omega2": omega_sq(pp, "follow_rate")},
        "desc": {c: {"n": int(len(g)), "M": float(g.mean()), "SD": float(g.std(ddof=1))}
                 for c, g in pp.groupby("condition", observed=True)["follow_rate"]},
        "ols": {name: {"b": float(ols.params[name]), "t": float(ols.tvalues[name]),
                       "df": float(ols.df_resid), "p": float(ols.pvalues[name])}
                for name in ols.params.index},
        "vs_baseline": {},
    }
    base = pp.loc[pp.condition == "ai", "follow_rate"].values
    for c in COND_ORDER[1:]:
        x = pp.loc[pp.condition == c, "follow_rate"].values
        t, dof, p = student_t(x, base)
        tw, dofw, pw = welch_t(x, base)
        g, lo, hi = hedges_g(x, base)
        out["participant_level"]["vs_baseline"][c] = {"t": t, "df": dof, "p": p, "g": g, "ci": [lo, hi], "welch": {"t": tw, "df": dofw, "p": pw}}
    # trial-level GEE logits
    fam, cov = sm.families.Binomial(), sm.cov_struct.Exchangeable()

    def gee(formula):
        m = smf.gee(formula, groups="pid", data=P, family=fam, cov_struct=cov).fit()
        return {name: {"b": float(m.params[name]), "OR": float(np.exp(m.params[name])),
                       "z": float(m.tvalues[name]), "p": float(m.pvalues[name])} for name in m.params.index}

    out["gee_followed"] = gee("followed ~ C(condition, Treatment('ai'))")
    out["gee_followed_x_aicorrect"] = gee("followed ~ C(condition, Treatment('ai')) * ai_correct")
    out["gee_followed_x_difficulty"] = gee("followed ~ C(condition, Treatment('ai')) * difficulty_z")
    out["gee_correct_given_override"] = None
    ovr = P[P.followed == 0]
    if len(ovr) > 50:
        m = smf.gee("correct ~ C(condition, Treatment('ai'))", groups="pid", data=ovr, family=fam, cov_struct=cov).fit()
        out["gee_correct_given_override"] = {name: {"OR": float(np.exp(m.params[name])), "z": float(m.tvalues[name]),
                                                    "p": float(m.pvalues[name])} for name in m.params.index}
    if not os.path.exists(os.path.join(NB, "reliance_trials.csv")):
        P.to_csv(os.path.join(NB, "reliance_trials.csv"), index=False)
    else:
        P.to_csv(os.path.join(NB, "reliance_trials.csv"), index=False)
    return out



# ----------------------------------------------------------------------------- tab:null
def null_robustness(df):
    """Score under alternative specifications: directional and two-sided JZS t-test Bayes factors
    (r = 0.707), Welch TOST at |g| < .3, and a trial-level GEE-logit odds ratio of a correct answer
    vs baseline with participant clustering and covariates (need for cognition, display position)."""
    out = {}
    base = df.loc[df.condition == "ai", "actual_score"].values
    tm = pd.read_csv(os.path.join(NB, "task_metrics.csv"))
    tm = tm[tm.participant_id.isin(df.participant_id)].copy()
    tm = tm.merge(df[["participant_id", "nfc_mean"]], on="participant_id")
    tm["nfc_z"] = (tm.nfc_mean - tm.nfc_mean.mean()) / tm.nfc_mean.std(ddof=1)
    tm["condition"] = pd.Categorical(tm.condition, COND_ORDER)
    gee = smf.gee("correct ~ C(condition, Treatment('ai')) + nfc_z + display_index", groups="participant_id", data=tm,
                  family=sm.families.Binomial(), cov_struct=sm.cov_struct.Exchangeable()).fit()
    for c in COND_ORDER[1:]:
        x = df.loc[df.condition == c, "actual_score"].values
        t_student = stats.ttest_ind(x, base).statistic
        bf10_two = jzs_ttest_bf10(t_student, len(x), len(base), r=0.707, alternative="two-sided")
        bf10_plus = jzs_ttest_bf10(t_student, len(x), len(base), r=0.707, alternative="greater")
        sd_pool = np.sqrt(((len(x) - 1) * x.var(ddof=1) + (len(base) - 1) * base.var(ddof=1)) / (len(x) + len(base) - 2))
        tost_p = float(pg.tost(x, base, bound=0.3 * sd_pool, paired=False, correction=True).iloc[0]["pval"])
        name = f"C(condition, Treatment('ai'))[T.{c}]"
        g, lo, hi = hedges_g(x, base)
        out[c] = {"g": g, "BF0plus": 1 / bf10_plus, "BF01": 1 / bf10_two, "BF10": bf10_two, "tost_p": tost_p,
                  "gee_or": float(np.exp(gee.params[name])), "gee_z": float(gee.tvalues[name]), "gee_p": float(gee.pvalues[name])}
    return out


# ----------------------------------------------------------------------------- report
def fmt_p(p):
    return "< .001" if p < .001 else f"= {p:.3f}".replace("0.", ".")


def fmt_stat(x, nd=2):
    return f"{x:.{nd}f}".replace("-0.", "-.").replace("0.", ".") if abs(x) < 1 else f"{x:.{nd}f}"


def write_report(results, rel, val):
    L = ["# APA-style results (generated by apa_results.py)", "",
         f"Validation: k = 2 JZS ANOVA BF10 = {val[0]:.3f} vs JZS t-test BF10 (r = .707) = {val[1]:.3f}.", ""]
    for res in results:
        w = res["welch"]
        L += [f"## {res['outcome']}", "",
              f"Welch ANOVA: F({w['df1']:.0f}, {w['df2']:.1f}) = {w['F']:.2f}, p {fmt_p(w['p'])}, omega^2 = {w['omega2']:.3f}. "
              f"JZS ANOVA BF01 = {res['bayes']['BF01']:.3g} (BF10 = {res['bayes']['BF10']:.3g}; BIC approx. BF01 = {res['bayes']['BF01_bic']:.3g}).", "",
              "| Condition | n | M (SD) | vs. baseline: t (df) | p (uncorrected) | g [95% CI] |", "|---|---|---|---|---|---|"]
        for c in COND_ORDER:
            d = res["desc"][c]
            if c == "ai":
                L.append(f"| {LABEL[c]} | {d['n']} | {d['M']:.2f} ({d['SD']:.2f}) | — | — | — |")
            else:
                v = res["vs_baseline"][c]
                L.append(f"| {LABEL[c]} | {d['n']} | {d['M']:.2f} ({d['SD']:.2f}) | t({v['df']:.1f}) = {v['t']:.2f} | {fmt_p(v['p'])} | "
                         f"{v['g']:+.2f} [{v['ci'][0]:+.2f}, {v['ci'][1]:+.2f}] |")
        L += ["", "Games-Howell post hoc (all pairs):", "", "| A | B | t (df) | p | g |", "|---|---|---|---|---|"]
        for r in res["games_howell"]:
            L.append(f"| {LABEL[r['A']]} | {LABEL[r['B']]} | t({r['df']:.1f}) = {r['t']:.2f} | {fmt_p(r['p'])} | {r['g']:+.2f} |")
        L.append("")
    # reliance
    L += ["## Reliance (parsed AI verdicts; verdict_parse.py)", "",
          "| Condition | coverage | n trials | follow rate | follow given AI correct | follow given AI wrong | P(correct given follow) | P(correct given override) | AI accuracy |",
          "|---|---|---|---|---|---|---|---|---|"]
    for c in COND_ORDER:
        b = rel["by_condition"][c]
        L.append(f"| {LABEL[c]} | {100*rel['coverage'][c]:.0f}% | {b['n_parsed']} | {100*b['follow_rate']:.1f}% | "
                 f"{100*b['follow_given_ai_correct']:.1f}% | {100*b['follow_given_ai_wrong']:.1f}% | "
                 f"{100*b['follow_success']:.1f}% | {100*b['override_success']:.1f}% | {100*b['ai_accuracy']:.1f}% |")
    pl = rel["participant_level"]
    w = pl["welch"]
    L += ["", f"Per-participant follow rate: Welch F({w['df1']:.0f}, {w['df2']:.1f}) = {w['F']:.2f}, p {fmt_p(w['p'])}.", "",
          "| Condition | n | M (SD) | t (df) vs baseline | p | g [95% CI] |", "|---|---|---|---|---|---|"]
    for c in COND_ORDER:
        d = pl["desc"][c]
        if c == "ai":
            L.append(f"| {LABEL[c]} | {d['n']} | {d['M']:.3f} ({d['SD']:.3f}) | — | — | — |")
        else:
            v = pl["vs_baseline"][c]
            L.append(f"| {LABEL[c]} | {d['n']} | {d['M']:.3f} ({d['SD']:.3f}) | t({v['df']:.1f}) = {v['t']:.2f} | {fmt_p(v['p'])} | {v['g']:+.2f} [{v['ci'][0]:+.2f}, {v['ci'][1]:+.2f}] |")
    L += ["", "OLS follow_rate ~ condition (baseline reference):", ""]
    for k, v in pl["ols"].items():
        L.append(f"- {k}: b = {v['b']:+.3f}, t({v['df']:.0f}) = {v['t']:.2f}, p {fmt_p(v['p'])}")
    for key, title in [("gee_followed", "GEE logit: followed ~ condition"),
                       ("gee_followed_x_aicorrect", "GEE logit: followed ~ condition x AI-correct"),
                       ("gee_followed_x_difficulty", "GEE logit: followed ~ condition x difficulty (z, baseline-derived)"),
                       ("gee_correct_given_override", "GEE logit on override trials: correct ~ condition")]:
        if rel.get(key):
            L += ["", f"{title}:", ""]
            for k, v in rel[key].items():
                L.append(f"- {k}: OR = {v['OR']:.2f}, z = {v['z']:.2f}, p {fmt_p(v['p'])}")
    with open(os.path.join(HERE, "APA_RESULTS.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")


def main():
    df = pd.read_csv(os.path.join(NB, "participant_metrics.csv"))
    df = df[df.exclude_primary == False].copy()
    assert len(df) == 917, len(df)
    val = validate()
    results = [analyse_outcome(df, col) for col, _, _ in OUTCOMES]
    rel = reliance(df)
    # Bayesian ANOVA on score without the pause-points arm (the four conditions that did not differ)
    d4 = df[df.condition != "pause-points"]
    bf10_4 = jzs_anova_bf10(d4.actual_score.values, d4.condition.values, r=0.5)
    extra = {"score_bf_without_pause": {"BF10": bf10_4, "BF01": 1 / bf10_4, "BF01_bic": bic_bf01(d4, "actual_score")},
             "null_robustness": null_robustness(df)}
    write_report(results, rel, val)
    with open(os.path.join(HERE, "apa_results.json"), "w") as fh:
        json.dump({"validation": val, "outcomes": results, "reliance": rel, "extra": extra}, fh, indent=1, default=str)
    print("validation (k=2): ANOVA BF10 =", round(val[0], 3), " t-test BF10 =", round(val[1], 3))
    for r in results:
        print(f"{r['outcome']:28s} F={r['welch']['F']:.2f} p={r['welch']['p']:.2e} BF01={r['bayes']['BF01']:.3g}")


if __name__ == "__main__":
    main()
