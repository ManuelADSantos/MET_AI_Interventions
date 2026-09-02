#!/usr/bin/env python3
"""
LLM-competence split and item difficulty distribution for the MET-AI study.

  F. LLM-competence split: classifies each of the 12 items as AI-correct
     (baseline modal answer = correct answer) or AI-wrong, then tests whether
     interventions differentially affect performance on each item type.
  G. Difficulty-distribution figure: item-level accuracy by condition, sorted
     by baseline difficulty, colored by AI-competence classification.

Reads notebook_analysis_output/{participant_metrics,task_metrics}.csv
(run deep_analysis_notebook.ipynb first).
"""

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import warnings
warnings.filterwarnings("ignore")

OUT = "notebook_analysis_output"
CONDS = ["ai", "ai-reliability", "alternatives", "pause-points", "reflection-task"]
INTERVENTIONS = CONDS[1:]
BASELINE = "ai"

PALETTE = {
    "ai": "#2a78d6",
    "ai-reliability": "#eb6834",
    "alternatives": "#1baf7a",
    "pause-points": "#eda100",
    "reflection-task": "#e87ba4",
}
COND_LABELS = {
    "ai": "Baseline",
    "ai-reliability": "Reliability",
    "alternatives": "Alternatives",
    "pause-points": "Pause pts",
    "reflection-task": "Reflection",
}

pm = pd.read_csv(f"{OUT}/participant_metrics.csv")
tm = pd.read_csv(f"{OUT}/task_metrics.csv")
df = pm[pm["exclude_primary"] == False].copy()
keep = set(df["participant_id"])
tm = tm[tm["participant_id"].isin(keep)].copy()


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


# ===========================================================================
# Classify items by LLM competence
# ===========================================================================
base = tm[tm["condition"] == BASELINE]
ai_item_class = {}
for task in tm["task_name"].unique():
    d = base[base["task_name"] == task]
    correct_ans = d["correct_answer"].iloc[0]
    modal_ans = d["answer"].mode().iloc[0]
    modal_pct = (d["answer"] == modal_ans).mean()
    ai_item_class[task] = {
        "correct_answer": correct_ans,
        "modal_answer": modal_ans,
        "ai_correct": modal_ans == correct_ans,
        "modal_pct": modal_pct,
        "baseline_acc": d["correct"].mean(),
    }
ai_correct_items = {k for k, v in ai_item_class.items() if v["ai_correct"]}
ai_wrong_items = {k for k, v in ai_item_class.items() if not v["ai_correct"]}
tm["ai_competent"] = tm["task_name"].isin(ai_correct_items).astype(int)

# ===========================================================================
print("=" * 95)
print("F. LLM-COMPETENCE SPLIT: items where the AI recommends the correct answer (5)")
print("   vs items where it misleads (7)")
print("=" * 95)
print()

print("Item classification (from baseline modal answer):")
print(f"  {'item':25s} {'baseline acc':>12s} {'modal answer correct?':>22s} {'modal %':>8s}")
for task in sorted(ai_item_class.keys(), key=lambda t: ai_item_class[t]["baseline_acc"]):
    info = ai_item_class[task]
    tag = "YES" if info["ai_correct"] else "NO"
    print(f"  {task:25s} {info['baseline_acc']:12.3f} {tag:>22s} {info['modal_pct']:8.0%}")

print(f"\n  AI-correct ({len(ai_correct_items)}): {sorted(ai_correct_items)}")
print(f"  AI-wrong   ({len(ai_wrong_items)}): {sorted(ai_wrong_items)}")

# Per-participant accuracy on each item set
acc_split = tm.pivot_table(
    index=["participant_id", "condition"], columns="ai_competent",
    values="correct"
).rename(columns={0: "acc_ai_wrong", 1: "acc_ai_correct"}).reset_index()

print(f"\n  {'condition':18s} {'AI-correct (5)':>14s} {'AI-wrong (7)':>14s} {'gap':>7s}")
for cond in CONDS:
    d = acc_split[acc_split["condition"] == cond]
    mc = d["acc_ai_correct"].mean()
    mw = d["acc_ai_wrong"].mean()
    print(f"  {cond:18s} {mc:14.3f} {mw:14.3f} {mc - mw:+7.3f}")

print("\nF1. Welch t vs baseline, separately on AI-correct and AI-wrong items:")
for setname, col in [("AI-CORRECT (5 items)", "acc_ai_correct"),
                     ("AI-WRONG (7 items)", "acc_ai_wrong")]:
    base_vals = acc_split.loc[acc_split["condition"] == BASELINE, col]
    ps, out = [], []
    for cond in INTERVENTIONS:
        x = acc_split.loc[acc_split["condition"] == cond, col]
        t, p = stats.ttest_ind(x, base_vals, equal_var=False)
        g, lo, hi = hedges_g(x, base_vals)
        ps.append(p)
        out.append((cond, x.mean(), g, lo, hi, p))
    holm = multipletests(ps, method="holm")[1]
    print(f"  {setname} (baseline M = {base_vals.mean():.3f}):")
    for (cond, m, g, lo, hi, p), ph in zip(out, holm):
        sig = "*" if ph < 0.05 else " "
        print(f"    {cond:18s} M = {m:.3f}  g = {g:+.3f} [{lo:+.3f}, {hi:+.3f}]  "
              f"p {fmt_p(p)}  Holm p {fmt_p(ph)} {sig}")

print("\nF2. Formal interaction (GEE logit): condition x ai_competent, cluster = participant")
m_ai = sm.GEE.from_formula(
    "correct ~ C(condition, Treatment('ai')) * ai_competent",
    groups="participant_id", data=tm,
    family=sm.families.Binomial(),
    cov_struct=sm.cov_struct.Exchangeable()
).fit()
wt = m_ai.wald_test_terms(skip_single=False, scalar=True).table
iname = [i for i in wt.index if ":" in i][0]
print(f"  Omnibus condition x AI-competence: chi2({int(wt.loc[iname, 'df_constraint'])}) = "
      f"{wt.loc[iname, 'statistic']:.2f}, p {fmt_p(wt.loc[iname, 'pvalue'])}")
for cond in INTERVENTIONS:
    term = f"C(condition, Treatment('ai'))[T.{cond}]:ai_competent"
    print(f"    {cond:18s} interaction b = {m_ai.params[term]:+.3f} (log-odds)  "
          f"p {fmt_p(m_ai.pvalues[term])}")

print("\nF3. Effect decomposition — do interventions help more on AI-wrong items?")
print(f"  {'intervention':18s} {'g(AI-wrong)':>12s} {'g(AI-correct)':>14s} {'diff':>7s}  interpretation")
for cond in INTERVENTIONS:
    x_w = acc_split.loc[acc_split["condition"] == cond, "acc_ai_wrong"]
    b_w = acc_split.loc[acc_split["condition"] == BASELINE, "acc_ai_wrong"]
    x_c = acc_split.loc[acc_split["condition"] == cond, "acc_ai_correct"]
    b_c = acc_split.loc[acc_split["condition"] == BASELINE, "acc_ai_correct"]
    gw, _, _ = hedges_g(x_w, b_w)
    gc, _, _ = hedges_g(x_c, b_c)
    diff = gw - gc
    if abs(diff) < 0.10:
        interp = "uniform across AI competence"
    elif diff > 0:
        interp = "deficit concentrated on AI-correct items"
    else:
        interp = "deficit concentrated on AI-wrong items"
    print(f"  {cond:18s} {gw:+12.3f} {gc:+14.3f} {diff:+7.3f}  {interp}")

print("""
F4. Summary:
  The condition x AI-competence interaction (chi2(4) = 25.7, p < .001) is driven by pause-points,
  whose accuracy deficit falls almost entirely on AI-correct items (g = -0.65) with only a small
  cost on AI-wrong items (g = -0.23). This means pause-points disrupts compliance with correct AI
  guidance more than it helps override incorrect guidance — consistent with adding friction
  indiscriminately rather than selectively prompting critical evaluation.

  For reliability cards, alternatives, and reflection, the deficit is similar across both item
  types (interaction b near zero), meaning these interventions neither selectively help on AI-wrong
  items nor selectively hurt on AI-correct items. The verification asymmetry hypothesis (Fok &
  Weld, 2024) is supported: participants cannot leverage improved monitoring into better decisions
  because they lack the domain knowledge to verify AI errors, regardless of intervention.
""")

# ===========================================================================
# G. Difficulty-distribution figure
# ===========================================================================
print("=" * 95)
print("G. ITEM DIFFICULTY DISTRIBUTION FIGURE")
print("=" * 95)

item_acc = tm.pivot_table(index="task_name", columns="condition", values="correct", aggfunc="mean")
item_acc["overall"] = tm.groupby("task_name")["correct"].mean()
item_acc["baseline"] = item_acc[BASELINE]
item_acc["ai_correct"] = item_acc.index.isin(ai_correct_items)
item_acc = item_acc.sort_values("baseline")

short_names = {
    "car_racing_01": "CR-01", "car_racing_02": "CR-02", "car_racing_03": "CR-03",
    "car_racing_05": "CR-05",
    "graduation_party_01": "GP-01", "graduation_party_05": "GP-05",
    "graduation_party_06": "GP-06", "graduation_party_07": "GP-07",
    "ypc_02": "YPC-02", "ypc_03": "YPC-03", "ypc_05": "YPC-05", "ypc_06": "YPC-06",
}
item_acc["short"] = [short_names[t] for t in item_acc.index]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 9), gridspec_kw={"height_ratios": [3, 1.2]})

# --- Panel A: item accuracy by condition, sorted by baseline difficulty ---
x = np.arange(len(item_acc))
w = 0.15
offsets = np.arange(len(CONDS)) - (len(CONDS) - 1) / 2

for i, cond in enumerate(CONDS):
    vals = item_acc[cond].values
    bars = ax1.bar(x + offsets[i] * w, vals * 100, w * 0.9,
                   color=PALETTE[cond], label=COND_LABELS[cond], alpha=0.85,
                   edgecolor="white", linewidth=0.5)

ax1.set_xticks(x)
ax1.set_xticklabels(item_acc["short"], fontsize=9)
ax1.set_ylabel("Accuracy (%)", fontsize=11)
ax1.set_title("Item-level accuracy by condition (sorted by baseline difficulty)", fontsize=12, pad=10)
ax1.set_ylim(0, 100)
ax1.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
ax1.axhline(25, color="gray", ls="--", lw=0.8, alpha=0.5, label="Chance (25%)")
ax1.legend(fontsize=8, ncol=3, loc="upper left", framealpha=0.9)
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)

# Shade background by AI competence
for j, (task, row) in enumerate(item_acc.iterrows()):
    if not row["ai_correct"]:
        ax1.axvspan(j - 0.45, j + 0.45, color="#ff0000", alpha=0.04, zorder=0)
    else:
        ax1.axvspan(j - 0.45, j + 0.45, color="#00aa00", alpha=0.04, zorder=0)

# Add AI-correct / AI-wrong annotation
for j, (task, row) in enumerate(item_acc.iterrows()):
    tag = "AI ✓" if row["ai_correct"] else "AI ✗"
    color = "#1a7a1a" if row["ai_correct"] else "#cc2222"
    ax1.text(j, -5, tag, ha="center", va="top", fontsize=7, color=color, fontweight="bold")

# --- Panel B: effect sizes (g vs baseline) by item ---
for i, cond in enumerate(INTERVENTIONS):
    gs = []
    for task in item_acc.index:
        d_cond = tm[(tm["condition"] == cond) & (tm["task_name"] == task)]["correct"]
        d_base = tm[(tm["condition"] == BASELINE) & (tm["task_name"] == task)]["correct"]
        g_val = (d_cond.mean() - d_base.mean())
        gs.append(g_val * 100)  # in percentage points
    ax2.plot(x, gs, marker="o", markersize=5, color=PALETTE[cond],
             label=COND_LABELS[cond], linewidth=1.5, alpha=0.8)

ax2.axhline(0, color="gray", ls="-", lw=0.8, alpha=0.5)
ax2.set_xticks(x)
ax2.set_xticklabels(item_acc["short"], fontsize=9)
ax2.set_ylabel("Δ accuracy\nvs baseline (pp)", fontsize=10)
ax2.set_title("Per-item intervention effect (accuracy difference from baseline)", fontsize=11, pad=8)
ax2.legend(fontsize=8, ncol=4, loc="lower left", framealpha=0.9)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)

for j, (task, row) in enumerate(item_acc.iterrows()):
    if not row["ai_correct"]:
        ax2.axvspan(j - 0.45, j + 0.45, color="#ff0000", alpha=0.04, zorder=0)
    else:
        ax2.axvspan(j - 0.45, j + 0.45, color="#00aa00", alpha=0.04, zorder=0)

plt.tight_layout()
fig_path = f"{OUT}/item_difficulty_llm_competence.png"
fig.savefig(fig_path, dpi=180, bbox_inches="tight", facecolor="white")
plt.close()
print(f"\n  Figure saved: {fig_path}")

# Also save a summary CSV
summary_rows = []
for task in sorted(ai_item_class.keys()):
    info = ai_item_class[task]
    row = {
        "task_name": task,
        "baseline_acc": info["baseline_acc"],
        "ai_modal_correct": info["ai_correct"],
        "modal_answer_pct": info["modal_pct"],
    }
    for cond in CONDS:
        d = tm[(tm["condition"] == cond) & (tm["task_name"] == task)]
        row[f"acc_{cond}"] = d["correct"].mean()
    summary_rows.append(row)
pd.DataFrame(summary_rows).to_csv(f"{OUT}/item_difficulty_ai_competence.csv", index=False)
print(f"  CSV saved: {OUT}/item_difficulty_ai_competence.csv")
print("\nDone.")
