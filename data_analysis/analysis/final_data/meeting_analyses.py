"""Meeting-requested analyses (2026-08-25).

1. Temporal: accuracy over display position; drop-first-trial re-analysis; halves/thirds.
2. Difficulty: easy vs hard items x condition, on accuracy and overconfidence.
3. Dunning-Kruger: skill-error gradient per condition + condition modulation test.
4. Trial-level mixed models (participant random intercept, NFC covariate).
5. Bayesian quantification of the performance null (JZS Bayes factors).

Reads notebook_analysis_output/{participant_metrics,task_metrics}.csv
(regenerate with: jupyter nbconvert --to notebook --execute deep_analysis_notebook.ipynb).
Writes MEETING_ANALYSES.md next to this script. All analyses exploratory/uncorrected
unless stated.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy import stats

OUT = []


def log(line: str = "") -> None:
    print(line)
    OUT.append(line)


def hedges_g(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = len(a), len(b)
    sp = math.sqrt(((na - 1) * a.var(ddof=1) + (nb - 1) * b.var(ddof=1)) / (na + nb - 2))
    j = 1 - 3 / (4 * (na + nb) - 9)
    return j * (a.mean() - b.mean()) / sp


def welch(a: np.ndarray, b: np.ndarray) -> tuple[float, float]:
    t, p = stats.ttest_ind(a, b, equal_var=False)
    return float(t), float(p)


# ---------------------------------------------------------------- load
P = pd.read_csv("notebook_analysis_output/participant_metrics.csv")
T = pd.read_csv("notebook_analysis_output/task_metrics.csv")
P = P[~P["exclude_primary"].astype(bool)].copy()
_pid_col = "participant_id" if "participant_id" in T.columns else "participantId"
_keep = set(P["participant_id" if "participant_id" in P.columns else "participantId"])
T = T[T[_pid_col].isin(_keep)].copy()

CONDS = ["ai", "ai-reliability", "alternatives", "pause-points", "reflection-task"]
LABEL = {"ai": "baseline", "ai-reliability": "reliability cards", "alternatives": "alternatives",
         "pause-points": "pause points", "reflection-task": "reflection"}


def col(df: pd.DataFrame, *cands: str) -> str:
    for c in cands:
        if c in df.columns:
            return c
    for c in df.columns:  # fuzzy fallback
        if any(k.lower() in c.lower() for k in cands):
            return c
    raise KeyError(cands)


pid_t = col(T, "participant_id", "participantId", "pid")
cond_t = col(T, "condition")
corr_c = col(T, "correct")
conf_c = col(T, "confidence")
disp_c = col(T, "display_index", "display_order")
auth_c = col(T, "authored_order", "source_index", "authored")

pid_p = col(P, "participant_id", "participantId", "pid")
cond_p = col(P, "condition")
score_c = col(P, "actual_score")
serr_c = col(P, "signed_estimation_error")
nfc_c = col(P, "nfc")

assert set(T[cond_t].unique()) == set(CONDS), T[cond_t].unique()
assert len(P) == 917 and len(T) == 917 * 12, (len(P), len(T))
# display_index is the raw page index (reflection pages create gaps);
# convert to within-participant display rank 1..12
T[disp_c] = T.groupby(pid_t)[disp_c].rank(method="first").astype(int)
assert set(T[disp_c].unique()) == set(range(1, 13))

T["correct01"] = T[corr_c].astype(float)
log("# Meeting analyses (2026-08-25)\n")
log(f"n = {len(P)} participants, {len(T)} trials. Exploratory/uncorrected unless stated.\n")

# ---------------------------------------------------------------- 1. temporal
log("## 1. Temporal analysis\n")
log("### Accuracy by display position (proportion correct)\n")
pos = T.pivot_table(index=cond_t, columns=disp_c, values="correct01").reindex(CONDS)
log("| condition | " + " | ".join(f"p{i}" for i in range(1, 13)) + " |")
log("|---|" + "---|" * 12)
for c in CONDS:
    log(f"| {LABEL[c]} | " + " | ".join(f"{pos.loc[c, i]:.2f}" for i in range(1, 13)) + " |")

log("\n### Within-participant trend (per-trial correctness vs position)\n")
log("| condition | pooled r(position, correct) | p |")
log("|---|---|---|")
for c in CONDS + [None]:
    d = T if c is None else T[T[cond_t] == c]
    r, p = stats.pearsonr(d[disp_c], d["correct01"])
    log(f"| {'ALL' if c is None else LABEL[c]} | {r:+.3f} | {p:.3f} |")

log("\n### Score excluding the first displayed trial (0-11) vs full score: Welch vs baseline\n")
s11 = (T[T[disp_c] > 1].groupby([pid_t, cond_t])["correct01"].sum()
       .rename("score11").reset_index())
base11 = s11.loc[s11[cond_t] == "ai", "score11"].to_numpy()
log("| intervention | M(0-11) | g vs baseline | two-sided p | full-score g (ref) |")
log("|---|---|---|---|---|")
FULL_G = {}
base_full = P.loc[P[cond_p] == "ai", score_c].to_numpy()
for c in CONDS[1:]:
    FULL_G[c] = hedges_g(P.loc[P[cond_p] == c, score_c].to_numpy(), base_full)
for c in CONDS[1:]:
    a = s11.loc[s11[cond_t] == c, "score11"].to_numpy()
    t, p = welch(a, base11)
    log(f"| {LABEL[c]} | {a.mean():.2f} | {hedges_g(a, base11):+.2f} | {p:.3f} | {FULL_G[c]:+.2f} |")

log("\n### Halves and thirds (proportion correct per block, within participant)\n")
for name, blocks in [("halves", [(1, 6), (7, 12)]), ("thirds", [(1, 4), (5, 8), (9, 12)])]:
    log(f"\n**{name}**\n")
    log("| condition | " + " | ".join(f"pos {a}-{b}" for a, b in blocks) +
        " | last-first Δ | paired p |")
    log("|---|" + "---|" * (len(blocks) + 2))
    deltas = {}
    for c in CONDS:
        d = T[T[cond_t] == c]
        means, per = [], []
        for a, b in blocks:
            blk = d[(d[disp_c] >= a) & (d[disp_c] <= b)].groupby(pid_t)["correct01"].mean()
            per.append(blk)
            means.append(blk.mean())
        delta = (per[-1] - per[0]).dropna()
        deltas[c] = delta
        tt, pp = stats.ttest_rel(per[-1], per[0])
        log(f"| {LABEL[c]} | " + " | ".join(f"{m:.3f}" for m in means) +
            f" | {delta.mean():+.3f} | {pp:.3f} |")
    fw = stats.f_oneway(*[deltas[c].to_numpy() for c in CONDS])
    log(f"\nCondition differences in last-minus-first change ({name}): "
        f"F = {fw.statistic:.2f}, p = {fw.pvalue:.3f}")

# ---------------------------------------------------------------- 2. difficulty
log("\n## 2. Easy vs hard items x condition\n")
diff = T.groupby(auth_c)["correct01"].mean().rename("item_p")
T = T.merge(diff, on=auth_c)
ter = diff.rank(method="first")
easy_items = set(diff.nlargest(4).index)
hard_items = set(diff.nsmallest(4).index)
T["bucket"] = np.select([T[auth_c].isin(hard_items), T[auth_c].isin(easy_items)],
                        ["hard", "easy"], default="mid")
log(f"Item difficulty (pooled p correct) range {diff.min():.2f}-{diff.max():.2f}; "
    f"easy = 4 easiest items, hard = 4 hardest.\n")
log("| condition | acc easy | acc hard | overconf easy (pp) | overconf hard (pp) |")
log("|---|---|---|---|---|")
for c in CONDS:
    d = T[T[cond_t] == c]
    row = []
    for b in ["easy", "hard"]:
        db = d[d["bucket"] == b]
        row.append(f"{db['correct01'].mean():.3f}")
    for b in ["easy", "hard"]:
        db = d[d["bucket"] == b]
        row.append(f"{(db[conf_c] - 100 * db['correct01']).mean():+.1f}")
    log(f"| {LABEL[c]} | " + " | ".join(row) + " |")

log("\n### Does any intervention help differentially on easy vs hard? (accuracy)\n")
per_pb = (T[T["bucket"] != "mid"].groupby([pid_t, cond_t, "bucket"])["correct01"]
          .mean().unstack("bucket").reset_index())
per_pb["gap"] = per_pb["easy"] - per_pb["hard"]
base_gap = per_pb.loc[per_pb[cond_t] == "ai", "gap"].to_numpy()
log("| intervention | easy-hard gap | Δgap vs baseline (g) | two-sided p |")
log("|---|---|---|---|")
for c in CONDS[1:]:
    a = per_pb.loc[per_pb[cond_t] == c, "gap"].to_numpy()
    t, p = welch(a, base_gap)
    log(f"| {LABEL[c]} | {a.mean():.3f} | {hedges_g(a, base_gap):+.2f} | {p:.3f} |")
log(f"\nbaseline easy-hard gap = {base_gap.mean():.3f}")

# ---------------------------------------------------------------- 3. Dunning-Kruger
log("\n## 3. Dunning-Kruger across conditions\n")
log("signed error = post estimate - actual score (positive = overestimation).\n")
log("| condition | r(score, signed error) | OLS slope |")
log("|---|---|---|")
for c in CONDS:
    d = P[P[cond_p] == c]
    r, p = stats.pearsonr(d[score_c], d[serr_c])
    sl = np.polyfit(d[score_c], d[serr_c], 1)[0]
    log(f"| {LABEL[c]} | {r:+.3f} | {sl:+.3f} |")

import statsmodels.formula.api as smf  # noqa: E402

P2 = P.rename(columns={score_c: "score", serr_c: "serr", cond_p: "cond"}).copy()
P2["cond"] = pd.Categorical(P2["cond"], categories=CONDS)
m_dk = smf.ols("serr ~ score * C(cond)", data=P2).fit(cov_type="HC3")
inter = {k: (v, m_dk.pvalues[k]) for k, v in m_dk.params.items() if "score:" in k}
log("\nModulation test — OLS signed error ~ score x condition (HC3 SEs), interaction terms:\n")
log("| term | b | p |")
log("|---|---|---|")
for k, (b, p) in inter.items():
    log(f"| {k} | {b:+.3f} | {p:.3f} |")
from statsmodels.stats.anova import anova_lm  # noqa: E402
m0 = smf.ols("serr ~ score + C(cond)", data=P2).fit()
m1 = smf.ols("serr ~ score * C(cond)", data=P2).fit()
an = anova_lm(m0, m1)
log(f"\nJoint interaction test: F = {an['F'][1]:.2f}, p = {an['Pr(>F)'][1]:.3f} "
    "(gradient modulation by condition)")
log("\nNote: estimate-score regression toward the mean inflates this gradient "
    "mechanically; the condition-modulation test is the informative part.")

# ---------------------------------------------------------------- 4. mixed models
log("\n## 4. Trial-level linear mixed models (participant random intercept)\n")
nfc_map = P.set_index(pid_p)[nfc_c]
T["nfc_z"] = ((T[pid_t].map(nfc_map) - nfc_map.mean()) / nfc_map.std())
T["pos_z"] = (T[disp_c] - T[disp_c].mean()) / T[disp_c].std()
T["conf"] = T[conf_c]
T["cond"] = pd.Categorical(T[cond_t], categories=CONDS)
ok = T.dropna(subset=["nfc_z", "conf"])
log(f"Trials in models: {len(ok)} (NFC or confidence missing on {len(T) - len(ok)}).\n")
for dv, label in [("correct01", "correctness (linear probability model)"),
                  ("conf", "confidence (0-100)")]:
    m = smf.mixedlm(f"{dv} ~ C(cond) + pos_z + nfc_z", data=ok,
                    groups=ok[pid_t]).fit(reml=True)
    log(f"### {label}\n")
    log("| term | b | p |")
    log("|---|---|---|")
    for k in m.params.index:
        if k in ("Group Var",):
            continue
        log(f"| {k} | {m.params[k]:+.3f} | {m.pvalues[k]:.3f} |")
    log("")
# GEE logit robustness for correctness
import statsmodels.api as sm  # noqa: E402
gee = smf.gee("correct01 ~ C(cond) + pos_z + nfc_z", groups=pid_t, data=ok,
              family=sm.families.Binomial(),
              cov_struct=sm.cov_struct.Exchangeable()).fit()
log("### correctness robustness: GEE logit (exchangeable)\n")
log("| term | OR | p |")
log("|---|---|---|")
for k in gee.params.index:
    log(f"| {k} | {math.exp(gee.params[k]):.3f} | {gee.pvalues[k]:.3f} |")

# ---------------------------------------------------------------- 5. Bayesian null
log("\n## 5. Bayesian evidence on the performance null (JZS, r = 0.707)\n")
from pingouin import bayesfactor_ttest  # noqa: E402


def jzs_bf10_twosided(t: float, nx: int, ny: int, r: float = math.sqrt(2) / 2) -> float:
    """Rouder et al. (2009) two-sample JZS BF10 via numerical integration.
    Self-check against pingouin below."""
    from scipy.integrate import quad
    neff = nx * ny / (nx + ny)
    df = nx + ny - 2

    def f(g):
        return (1 + neff * g * r**2) ** -0.5 * (
            1 + t**2 / ((1 + neff * g * r**2) * df)) ** (-(df + 1) / 2) * (
            (2 * math.pi) ** -0.5 * g ** -1.5 * math.exp(-1 / (2 * g)))

    num = quad(f, 0, np.inf, limit=200)[0]
    den = (1 + t**2 / df) ** (-(df + 1) / 2)
    return num / den


base = P.loc[P[cond_p] == "ai", score_c].to_numpy()
log("| intervention | t | BF10 (two-sided) | BF01 | BF0+ (vs improvement) |")
log("|---|---|---|---|---|")
for c in CONDS[1:]:
    a = P.loc[P[cond_p] == c, score_c].to_numpy()
    t, _ = welch(a, base)  # direction: intervention minus baseline
    # pingouin uses pooled-variance t; recompute for consistency with its BF
    tp, _ = stats.ttest_ind(a, base, equal_var=True)
    bf10 = float(bayesfactor_ttest(tp, len(a), len(base)))
    # self-check the implementation once
    mine = jzs_bf10_twosided(tp, len(a), len(base))
    assert abs(mine - bf10) / bf10 < 0.01, (mine, bf10)
    # one-sided BF for H+: delta > 0 (improvement), via truncated prior:
    # BF+0 = BF10 * 2 * P(delta > 0 | data) approximated by posterior mass sign;
    # use the t-statistic sign shortcut: for symmetric priors,
    # BF+0 = BF10 * (posterior mass > 0). Approximate posterior mass with
    # the classical one-sided p complement under the fitted noncentrality.
    from scipy.integrate import quad
    neff = len(a) * len(base) / (len(a) + len(base))
    df = len(a) + len(base) - 2
    r = math.sqrt(2) / 2

    def marg(delta_sign):
        def f(d):
            try:  # nct.pdf overflows at extreme noncentrality; density is ~0 there
                v = stats.nct.pdf(tp, df, d * math.sqrt(neff))
            except OverflowError:
                return 0.0
            return (0.0 if not math.isfinite(v) else v) * 2 * stats.cauchy.pdf(d, scale=r)
        lo, hi = (0, 40) if delta_sign > 0 else (-40, 0)  # Cauchy tail beyond |40| negligible
        return quad(f, lo, hi, limit=400)[0]

    bf_plus0 = marg(+1) / stats.t.pdf(tp, df)
    log(f"| {LABEL[c]} | {tp:+.2f} | {bf10:.2f} | {1 / bf10:.2f} | {1 / bf_plus0:.1f} |")
log("\nBF0+ > 10 = strong evidence against a performance improvement; "
    "BF01 quantifies the two-sided (any difference) comparison.")

with open("MEETING_ANALYSES.md", "w") as fh:
    fh.write("\n".join(OUT) + "\n")
print("\nwritten: MEETING_ANALYSES.md")
