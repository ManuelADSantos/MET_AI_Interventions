"""Recompute the descriptive and exploratory numbers quoted in Section 5 of the paper from the
exported data, so that every figure in the text can be traced to a computation.

Run:  ../../../.venv/bin/python verify_paper_numbers.py   (from final_data/)
Writes VERIFY_PAPER_NUMBERS.md next to this file.
"""
import json
import os
import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.environ.get("MET_DATA_DIR", os.path.join(HERE, "notebook_analysis_output"))
sys.path.insert(0, HERE)
ORDER = ["ai", "ai-reliability", "alternatives", "pause-points", "reflection-task"]
LAB = {"ai": "Base", "ai-reliability": "Cards", "alternatives": "Alts", "pause-points": "Pausep", "reflection-task": "Refl"}

L = ["# Paper numbers recomputed from the exported data", ""]


def sec(t):
    L.extend(["", f"## {t}", ""])


def row(*cells):
    L.append("| " + " | ".join(str(c) for c in cells) + " |")


pm = pd.read_csv(os.path.join(NB, "participant_metrics.csv"))
pm = pm[pm.exclude_primary == False].copy()
tm = pd.read_csv(os.path.join(NB, "task_metrics.csv"))
tm = tm[tm.participant_id.isin(pm.participant_id)].copy()
assert len(pm) == 917 and len(tm) == 917 * 12

# ----------------------------------------------------------------------------- sample
sec("Sample (tab:participants)")
row("condition", "n", "age M (SD)", "AI use M (SD)", "median completion min")
row("---", "---", "---", "---", "---")
for c in ORDER:
    d = pm[pm.condition == c]
    row(LAB[c], len(d), f"{d.age.mean():.1f} ({d.age.std():.1f})", f"{d.ai_use_frequency.mean():.1f} ({d.ai_use_frequency.std():.1f})",
        f"{d.completion_minutes.median():.1f}")
refl = pm[pm.condition == "reflection-task"]
L.append(f"\nReflection sessions over 60 min: {100 * (refl.completion_minutes > 60).mean():.0f}% (paper: 67%).")
L.append(f"AI use by condition (baseline vs others): {pm.groupby('condition').ai_use_frequency.mean().round(2).to_dict()}")

# ----------------------------------------------------------------------------- tasks
sec("Tasks")
acc_item = tm.groupby("task_name")["correct"].mean()
acc_item_base = tm[tm.condition == "ai"].groupby("task_name")["correct"].mean()
L.append(f"Pooled item accuracy range: {100 * acc_item.min():.0f}--{100 * acc_item.max():.0f}% (paper 18--78); baseline: "
         f"{100 * acc_item_base.min():.0f}--{100 * acc_item_base.max():.0f}% (paper 20--86).")
L.append(f"Items at or below 25% pooled: {(acc_item <= .25).sum()} (paper 3); by baseline accuracy: {(acc_item_base <= .25).sum()} (paper 2).")
L.append(f"Pooled participant accuracy: {100 * tm.correct.mean():.1f}% (paper 43.3); baseline: {100 * tm[tm.condition == 'ai'].correct.mean():.1f}% (paper 46.4).")
L.append(f"Every participant prompted on all 12 problems: {(pm.main_tasks_prompted == 12).all()}.")

# ----------------------------------------------------------------------------- exposure
sec("Manipulation and exposure checks")
cards = pm[pm.condition == "ai-reliability"]
L.append(f"Cards shown on all 12 problems: {100 * (cards.reliability_cards_presented >= 12).mean():.0f}% of participants (paper 90%); "
         f"share of problems with card: {100 * cards.reliability_cards_presented.clip(upper=12).sum() / (12 * len(cards)):.0f}% (paper 97%); "
         f"collapsed at least once: {100 * (cards.cards_hidden > 0).mean():.0f}% (paper 72%).")
pp = pm[pm.condition == "pause-points"]
L.append(f"Pause-points gate engaged share of problems: {100 * pp.gate_matched.sum() / (12 * len(pp)):.0f}% (paper 74%).")
L.append(f"Reflection pages answered median: {refl.reflection_pages_answered.median():.0f}/12; median words {refl.reflection_words.median():.0f} (paper 973).")
tok = pm.groupby("condition").assistant_output_tokens.mean()
L.append(f"Assistant output tokens per participant: {tok.round(0).to_dict()} (alternatives about double).")
L.append(f"Mean prompt words by condition: {pm.groupby('condition').mean_prompt_words.mean().round(0).to_dict()} (paper: pause 70 vs 122--166).")

# ----------------------------------------------------------------------------- calibration (tab:calib)
sec("Calibration profile (tab:calib)")
row("condition", "overestimating %", "signed error M (SD)", "delta with-AI estimate", "conf - acc (pp)", "delta (AI - self) gap")
row("---", "---", "---", "---", "---", "---")
tm["conf_minus_acc"] = tm.confidence - 100 * tm.correct
for c in ORDER:
    d = pm[pm.condition == c]
    t = tm[tm.condition == c]
    gap_pre = d.pre_ai_alone - d.pre_without_ai
    gap_post = d.post_ai_alone - d.post_without_ai
    row(LAB[c], f"{100 * (d.signed_estimation_error > 0).mean():.0f}", f"{d.signed_estimation_error.mean():+.2f} ({d.signed_estimation_error.std():.2f})",
        f"{d.estimate_shift_with_ai.mean():+.2f}", f"{t.conf_minus_acc.mean():+.1f}", f"{(gap_post - gap_pre).mean():+.2f}")
L.append(f"\nShare of all participants overestimating: {100 * (pm.signed_estimation_error > 0).mean():.0f}% (paper 82%).")

# ----------------------------------------------------------------------------- Brier / Murphy, type-2 AUC
sec("Proper scoring and type-2 AUC")


def murphy(t, bins=10):
    p = t.confidence.values / 100
    y = t.correct.values.astype(float)
    brier = np.mean((p - y) ** 2)
    ybar = y.mean()
    unc = ybar * (1 - ybar)
    b = np.clip((p * bins).astype(int), 0, bins - 1)
    rel = res = 0.0
    for k in range(bins):
        m = b == k
        if m.sum():
            rel += m.sum() * (p[m].mean() - y[m].mean()) ** 2
            res += m.sum() * (y[m].mean() - ybar) ** 2
    return brier, rel / len(p), res / len(p), unc


def type2_auc(t):
    cor = t.loc[t.correct == 1, "confidence"].values
    inc = t.loc[t.correct == 0, "confidence"].values
    if len(cor) == 0 or len(inc) == 0:
        return np.nan
    u = stats.mannwhitneyu(cor, inc, alternative="two-sided").statistic
    return u / (len(cor) * len(inc))


row("condition", "Brier", "reliability", "resolution", "uncertainty", "pooled type-2 AUC", "participant-mean AUC")
row("---", "---", "---", "---", "---", "---", "---")
auc_pp = tm.groupby(["participant_id", "condition"]).apply(type2_auc).reset_index(name="auc")
for c in ORDER:
    t = tm[tm.condition == c]
    br, rel, res, unc = murphy(t)
    row(LAB[c], f"{br:.3f}", f"{rel:.3f}", f"{res:.3f}", f"{unc:.3f}", f"{type2_auc(t):.3f}", f"{auc_pp[auc_pp.condition == c].auc.mean():.3f}")
base_auc = auc_pp[auc_pp.condition == "ai"].auc.dropna()
cards_auc = auc_pp[auc_pp.condition == "ai-reliability"].auc.dropna()
import pingouin as pg
tt = pg.ttest(cards_auc, base_auc, correction=True).iloc[0]
g = pg.compute_effsize(cards_auc, base_auc, eftype="hedges")
L.append(f"\nCards vs baseline on participant type-2 AUC: t({tt['dof']:.1f}) = {tt['T']:.2f}, p = {tt['p_val']:.3f}, g = {g:+.2f} (paper g = +0.36).")
# bootstrap CI for pooled baseline AUC
rng = np.random.default_rng(0)
tb = tm[tm.condition == "ai"]
boots = [type2_auc(tb.sample(len(tb), replace=True, random_state=int(rng.integers(1e9)))) for _ in range(1000)]
L.append(f"Pooled baseline type-2 AUC {type2_auc(tb):.3f} [{np.percentile(boots, 2.5):.3f}, {np.percentile(boots, 97.5):.3f}] (paper .516 [.493, .539]).")

# ----------------------------------------------------------------------------- difficulty
sec("Difficulty analyses")
base_acc = tm[tm.condition == "ai"].groupby("task_name")["correct"].mean()
tm["difficulty_z"] = -((tm.task_name.map(base_acc) - base_acc.mean()) / base_acc.std(ddof=1))
hard = base_acc.sort_values().index[:6]
tm["hard"] = tm.task_name.isin(hard)
row("condition", "conf-acc hard (pp)", "conf-acc easy (pp)", "acc hard %", "acc easy %")
row("---", "---", "---", "---", "---")
for c in ORDER:
    t = tm[tm.condition == c]
    row(LAB[c], f"{t[t.hard].conf_minus_acc.mean():+.0f}", f"{t[~t.hard].conf_minus_acc.mean():+.0f}",
        f"{100 * t[t.hard].correct.mean():.0f}", f"{100 * t[~t.hard].correct.mean():.0f}")
tm["condition"] = pd.Categorical(tm.condition, ORDER)
fam, cov = sm.families.Binomial(), sm.cov_struct.Exchangeable()
m = smf.gee("correct ~ C(condition, Treatment('ai')) * difficulty_z", groups="participant_id", data=tm, family=fam, cov_struct=cov).fit()
L.append("\nGEE logit correct ~ condition x difficulty_z (interaction terms):")
for name in m.params.index:
    if ":" in name:
        L.append(f"- {name}: b = {m.params[name]:+.2f}, z = {m.tvalues[name]:.2f}, p = {m.pvalues[name]:.3f}")
# easy-item score effect of pause points
easy_score = tm[~tm.hard].groupby(["participant_id", "condition"], observed=True).correct.sum().reset_index()
x = easy_score[easy_score.condition == "pause-points"].correct
y = easy_score[easy_score.condition == "ai"].correct
tt = pg.ttest(x, y, correction=True).iloc[0]
L.append(f"Pause points vs baseline on the six easy items: t({tt['dof']:.1f}) = {tt['T']:.2f}, p = {tt['p_val']:.2e}, g = {pg.compute_effsize(x, y, eftype='hedges'):+.2f} (paper g = -0.65).")
# confidence deflation slope with difficulty (item-level confidence ~ condition x difficulty)
mc = smf.gee("confidence ~ C(condition, Treatment('ai')) * difficulty_z", groups="participant_id", data=tm, family=sm.families.Gaussian(), cov_struct=cov).fit()
L.append("\nGEE linear confidence ~ condition x difficulty_z (interaction = extra pp of confidence per SD of difficulty vs baseline):")
for name in mc.params.index:
    if ":" in name:
        L.append(f"- {name}: b = {mc.params[name]:+.2f}, z = {mc.tvalues[name]:.2f}, p = {mc.pvalues[name]:.3f}")

# ----------------------------------------------------------------------------- time course
sec("Time course")
tm["pos"] = tm.display_index
r = stats.pearsonr(tm.pos, tm.correct)
L.append(f"Accuracy vs display position, pooled r = {r[0]:.3f}, p = {r[1]:.3f} (paper r = .001).")
half = tm.groupby(["participant_id", "condition", tm.pos >= tm.pos.median()], observed=True).correct.mean().unstack()
half.columns = ["first", "second"]
d = half["second"] - half["first"]
tt = stats.ttest_1samp(d, 0)
L.append(f"Second half minus first half accuracy: M = {d.mean():+.3f}, t({len(d) - 1}) = {tt.statistic:.2f}, p = {tt.pvalue:.3f}.")

# ----------------------------------------------------------------------------- card anchoring
sec("Card anchoring")
cd = pm[pm.condition == "ai-reliability"]
L.append(f"Cards: mean |estimate - 7.1| = {np.abs(cd.post_with_ai - 7.1).mean():.2f} vs |estimate - actual| = {cd.absolute_estimation_error.mean():.2f} (paper 1.9 vs 3.4); "
         f"paired t on the two distances: t({len(cd) - 1}) = {stats.ttest_rel(np.abs(cd.post_with_ai - 7.1), cd.absolute_estimation_error).statistic:.2f}, "
         f"p = {stats.ttest_rel(np.abs(cd.post_with_ai - 7.1), cd.absolute_estimation_error).pvalue:.2e}; "
         f"estimate above 7.1: one-sample t({len(cd) - 1}) = {stats.ttest_1samp(cd.post_with_ai, 7.1).statistic:.2f}, p = {stats.ttest_1samp(cd.post_with_ai, 7.1).pvalue:.2e}.")

# ----------------------------------------------------------------------------- trust correlations
sec("Trust correlations (appendix)")
for col, name in [("absolute_estimation_error", "abs. estimation error"), ("signed_estimation_error", "signed error"),
                  ("mean_confidence", "confidence"), ("actual_score", "score")]:
    rr = stats.pearsonr(pm.trust_mean, pm[col])
    L.append(f"- trust vs {name}: r = {rr[0]:.2f}, p = {rr[1]:.3g}")


# ----------------------------------------------------------------------------- qualitative codes (tab:qual)
sec("Qualitative codes on the analysed sample (tab:qual)")
from scipy.stats import chi2_contingency
inc = set(pm.participant_id)
for f, title in [("strategies", "Strategies"), ("manipulation", "Effect of the manipulation")]:
    Q = pd.read_csv(os.path.join(NB, f"qualitative_codes_{f}.csv"))
    Q = Q[Q.participant_id.isin(inc)].copy()
    Q["codes"] = Q["codes"].fillna("")
    conds = [o for o in ORDER if o in Q.condition.unique()]
    L.append(f"{title}: N = {len(Q)} (per condition {Q.condition.value_counts().reindex(conds).tolist()}); "
             f"uncoded {[round(100 * x, 1) for x in Q.groupby('condition').apply(lambda d: (d.codes == '').mean()).reindex(conds)]}%")
    row("code", *[LAB[c] for c in conds], "chi2 (df)", "p", "Cramer's V", "N")
    row("---", *["---"] * len(conds), "---", "---", "---", "---")
    for c in sorted({x for s_ in Q.codes for x in s_.split(";") if x}):
        Q[c] = Q.codes.str.split(";").apply(lambda lst: int(c in lst))
        sub = Q if c != "manipulation_use" else Q[Q.condition != "ai"]
        cs = [o for o in conds if o in sub.condition.unique()]
        tab = pd.crosstab(sub.condition, sub[c]).reindex(cs).fillna(0)
        chi, pval, dof, _ = chi2_contingency(tab.values)
        n = int(tab.values.sum())
        V = np.sqrt(chi / (n * (min(tab.shape) - 1)))
        pct = (Q.groupby("condition")[c].mean().reindex(conds) * 100).round(1).tolist()
        row(c, *pct, f"{chi:.2f} ({dof})", f"{pval:.3f}", f"{V:.3f}", n)
    L.append("")
# macro-F1 of the lexical codebook vs the held-out annotation, over all 16 codes (paper) and the codes with F1 >= .7
try:
    import subprocess
    out = subprocess.run([sys.executable, os.path.join(HERE, "validation", "score_validation.py"), "holdout"], capture_output=True, text=True, cwd=os.path.join(HERE, "validation")).stdout
    f1s = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 6 and parts[1].isdigit():
            tp, fp, fn = map(int, parts[1:4])
            f1s[parts[0]] = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
    L.append(f"Held-out validation: macro-F1 over all {len(f1s)} codes = {np.mean(list(f1s.values())):.2f} (paper .61); "
             f"codes with F1 >= .7: {sorted(k for k, v in f1s.items() if v >= .7)}")
except Exception as e:  # pragma: no cover
    L.append(f"(validation scoring not run: {e})")

# ----------------------------------------------------------------------------- headroom
sec("Headroom (Discussion)")
R = pd.read_csv(os.path.join(NB, "reliance_trials.csv"))
ai_acc = R[R.condition == "ai"].ai_correct.mean()
L.append(f"Baseline parsed advice accuracy {100 * ai_acc:.1f}%; always following yields {12 * ai_acc:.2f} of 12 (paper 5.65 at 47%).")

open(os.path.join(HERE, "VERIFY_PAPER_NUMBERS.md"), "w").write("\n".join(L) + "\n")
print("\n".join(L))
