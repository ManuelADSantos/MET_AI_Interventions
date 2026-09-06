"""Figures for the empirical study (print-friendly, colorblind-safe, matplotlib only).

  effects_forest.pdf            16 intervention-vs-baseline contrasts (Hedges g, 95% CI)
  confidence_by_correctness.pdf mean confidence on correct vs incorrect answers by condition
  difficulty_profiles.pdf       accuracy and overconfidence per item, items ordered by baseline difficulty
  reliance_follow.pdf           share of problems on which participants followed the assistant,
                                split by whether the advice was correct

Run from final_data/:  ../../../.venv/bin/python make_figures.py [--pgf] [outdir ...]   (--pgf writes .pgf twins of the .pdf files)
Default outdir: ../publication_ready/figures and the paper's figs/ folder if it exists.
"""
import json
import os
import sys

import matplotlib
PGF = "--pgf" in sys.argv  # export .pgf (text typeset by LaTeX in the document font) instead of .pdf
sys.argv = [a for a in sys.argv if a != "--pgf"]
matplotlib.use("pgf" if PGF else "Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.environ.get("MET_DATA_DIR", os.path.join(HERE, "notebook_analysis_output"))
J = json.load(open(os.path.join(HERE, "apa_results.json")))
ORDER = ["ai", "ai-reliability", "alternatives", "pause-points", "reflection-task"]
NAME = {"ai": "Baseline", "ai-reliability": "Reliability cards", "alternatives": "Contrasting replies",
        "pause-points": "Pause points", "reflection-task": "Reflection"}
# Okabe-Ito, fixed assignment per condition (never cycled)
COL = {"ai": "#4d4d4d", "ai-reliability": "#0072B2", "alternatives": "#E69F00", "pause-points": "#D55E00", "reflection-task": "#009E73"}
plt.rcParams.update({"font.size": 8, "font.family": "sans-serif", "axes.spines.top": False, "axes.spines.right": False,
                     "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6, "pdf.fonttype": 42})
if PGF:  # same geometry and sizes; text set by LaTeX in the surrounding document font
    plt.rcParams.update({"pgf.texsystem": "pdflatex", "pgf.rcfonts": False, "font.family": "serif", "text.usetex": False,
                         "pgf.preamble": ""})
WIDE = 5.95 if PGF else 7.0  # acmart manuscript text width is 430pt = 5.95in; the .pdf keeps its 7in design width
OUTDIRS = sys.argv[1:] or [os.path.join(HERE, "..", "publication_ready", "figures"),
                           "/Users/dionism1/Desktop/CHI27_METAI_Interventions/archive/figs/results"]


def save(fig, name):
    for d in OUTDIRS:
        if os.path.isdir(d) or d.endswith("figures"):
            os.makedirs(d, exist_ok=True)
            fig.savefig(os.path.join(d, name.replace(".pdf", ".pgf") if PGF else name), bbox_inches="tight")
    plt.close(fig)


def lighten(hex_color, f=0.55):
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return (r + (1 - r) * f, g + (1 - g) * f, b + (1 - b) * f)


def ci95(x):
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    return stats.t.ppf(.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x))


# --------------------------------------------------------------------------- forest plot
def forest():
    outs = [("absolute_estimation_error", "Estimation error (H1)\nlower is better"), ("confidence_discrimination", "$\\Delta$Conf (H2)\nhigher is better"),
            ("actual_score", "Score (H3)\nhigher is better"), ("prompts_per_task", "Prompts per problem (H4)\n ")]
    res = {r["outcome"]: r for r in J["outcomes"]}
    fig, axes = plt.subplots(1, 4, figsize=(WIDE, 2.0), sharey=True)
    for ax, (o, title) in zip(axes, outs):
        r = res[o]
        tuk = {frozenset((t["A"], t["B"])): t["p"] for t in r["tukey"]}
        for i, c in enumerate(ORDER[1:]):
            v = r["vs_baseline"][c]
            y = 3 - i
            p_unc, p_tuk = v["p"], tuk[frozenset(("ai", c))]
            if p_tuk < .05:
                mfc, mec = COL[c], COL[c]
            elif p_unc < .05:
                mfc, mec = lighten(COL[c]), COL[c]
            else:
                mfc, mec = "white", COL[c]
            ax.plot(v["ci"], [y, y], color=COL[c], lw=1.2, solid_capstyle="round", zorder=2)
            ax.plot(v["g"], y, marker="o", ms=5, mfc=mfc, mec=mec, mew=1.2, ls="none", zorder=4)
            ax.text(v["ci"][1] + 0.05 if v["g"] >= 0 else v["ci"][0] - 0.05, y, f"{v['g']:+.2f}", va="center",
                    ha="left" if v["g"] >= 0 else "right", fontsize=6.5, color=COL[c])
        ax.axvline(0, color="#999999", lw=0.6, zorder=1)
        ax.set_title(title, fontsize=7.5, loc="left")
        ax.set_xlabel("Hedges' g vs. baseline", fontsize=7)
        lo = min(min(r["vs_baseline"][c]["ci"]) for c in ORDER[1:])
        hi = max(max(r["vs_baseline"][c]["ci"]) for c in ORDER[1:])
        pad = 0.35 * (hi - lo) + 0.15
        ax.set_xlim(min(lo - pad, -0.3), max(hi + pad, 0.3))
        ax.set_yticks(range(4))
        ax.set_yticklabels([NAME[c] for c in ORDER[1:]][::-1])
        ax.set_ylim(-0.7, 3.6)
        ax.tick_params(axis="y", length=0)
        ax.grid(axis="x", color="#eeeeee", lw=0.5, zorder=0)
    # legend
    h = [plt.Line2D([], [], marker="o", ms=5, mfc="#4d4d4d", mec="#4d4d4d", ls="none", label="p < .05, Tukey HSD vs. baseline"),
         plt.Line2D([], [], marker="o", ms=5, mfc="#bbbbbb", mec="#4d4d4d", ls="none", label="p < .05, uncorrected only"),
         plt.Line2D([], [], marker="o", ms=5, mfc="white", mec="#4d4d4d", ls="none", label="not significant")]
    fig.legend(handles=h, loc="lower center", ncol=3, frameon=False, fontsize=7, bbox_to_anchor=(0.5, -0.12))
    fig.tight_layout(w_pad=1.0)
    save(fig, "effects_forest.pdf")


# --------------------------------------------------------------------------- confidence by correctness
def confidence():
    pm = pd.read_csv(os.path.join(NB, "participant_metrics.csv"))
    pm = pm[pm.exclude_primary == False]
    fig, ax = plt.subplots(figsize=(3.73, 2.5))
    for i, c in enumerate(ORDER):
        d = pm[pm.condition == c]
        y = 4 - i
        mc, mi = d.mean_conf_correct.mean(), d.mean_conf_incorrect.mean()
        ax.plot([mi, mc], [y, y], color=COL[c], lw=1.4, zorder=2)
        ax.errorbar(mc, y, xerr=ci95(d.mean_conf_correct), fmt="o", ms=5, color=COL[c], mfc=COL[c], mec=COL[c], elinewidth=0.8, capsize=0, zorder=3)
        ax.errorbar(mi, y, xerr=ci95(d.mean_conf_incorrect), fmt="o", ms=5, color=COL[c], mfc="white", mec=COL[c], mew=1.2, elinewidth=0.8, capsize=0, zorder=3)
        ax.text(89, y, f"$\\Delta$ = {mc - mi:+.1f} pp", va="center", fontsize=6.5, color=COL[c])
        acc = 100 * d.actual_score.mean() / 12
        ax.plot(acc, y, marker="|", ms=9, color=COL[c], mew=1.2, ls="none", zorder=3)
    ax.set_yticks(range(5))
    ax.set_yticklabels([NAME[c] for c in ORDER][::-1])
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("Mean confidence (0–100)", fontsize=7)
    ax.set_xlim(30, 100)
    ax.set_xticks([30, 40, 50, 60, 70, 80, 90, 100])
    ax.set_ylim(-0.7, 4.6)
    ax.grid(axis="x", color="#eeeeee", lw=0.5, zorder=0)
    h = [plt.Line2D([], [], marker="o", ms=5, mfc="#4d4d4d", mec="#4d4d4d", ls="none", label="correct answers"),
         plt.Line2D([], [], marker="o", ms=5, mfc="white", mec="#4d4d4d", mew=1.2, ls="none", label="incorrect answers"),
         plt.Line2D([], [], marker="|", ms=9, color="#4d4d4d", mew=1.2, ls="none", label="accuracy (%)")]
    ax.legend(handles=h, loc="lower center", frameon=False, fontsize=6.5, ncol=3, bbox_to_anchor=(0.45, -0.62))
    fig.tight_layout()
    save(fig, "confidence_by_correctness.pdf")


# --------------------------------------------------------------------------- difficulty profiles
def difficulty():
    pm = pd.read_csv(os.path.join(NB, "participant_metrics.csv"))
    pm = pm[pm.exclude_primary == False]
    tm = pd.read_csv(os.path.join(NB, "task_metrics.csv"))
    tm = tm[tm.participant_id.isin(pm.participant_id)]
    base = tm[tm.condition == "ai"].groupby("task_name").correct.mean().sort_values(ascending=False)
    items = list(base.index)
    fig, axes = plt.subplots(1, 2, figsize=(WIDE, 2.2))
    for ax, (col, ylabel) in zip(axes, [("acc", "Accuracy (%)"), ("gap", "Confidence − accuracy (pp)")]):
        for c in ORDER:
            t = tm[tm.condition == c]
            g = t.groupby("task_name").agg(acc=("correct", "mean"), conf=("confidence", "mean")).reindex(items)
            yv = 100 * g.acc if col == "acc" else g.conf - 100 * g.acc
            ax.plot(range(12), yv, color=COL[c], lw=1.2 if c != "ai" else 1.6, marker="o", ms=2.5, zorder=3 if c != "ai" else 4, label=NAME[c])
        if col == "acc":
            ax.axhline(25, color="#999999", lw=0.6, ls=":", zorder=1)
            ax.text(0, 26.5, "guessing floor", fontsize=6, color="#777777")
        ax.set_xticks(range(12))
        ax.set_xticklabels([str(i + 1) for i in range(12)], fontsize=6)
        ax.set_xlabel("Items, easiest to hardest at baseline", fontsize=7)
        ax.set_ylabel(ylabel, fontsize=7)
        ax.set_xlim(-0.3, 11.3)
        ax.grid(axis="y", color="#eeeeee", lw=0.5, zorder=0)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=5, frameon=False, fontsize=7, bbox_to_anchor=(0.5, -0.06))
    fig.tight_layout(w_pad=1.5)
    save(fig, "difficulty_profiles.pdf")


# --------------------------------------------------------------------------- reliance
def reliance():
    R = pd.read_csv(os.path.join(NB, "reliance_trials.csv"))
    fig, ax = plt.subplots(figsize=(3.4, 2.5))
    for i, c in enumerate(ORDER):
        d = R[R.condition == c]
        y = 4 - i
        pc = d.groupby(["pid"]).apply(lambda x: x.loc[x.ai_correct == 1, "followed"].mean()).dropna()
        pw = d.groupby(["pid"]).apply(lambda x: x.loc[x.ai_correct == 0, "followed"].mean()).dropna()
        fc, fw = 100 * d.loc[d.ai_correct == 1, "followed"].mean(), 100 * d.loc[d.ai_correct == 0, "followed"].mean()
        ax.plot([fw, fc], [y, y], color=COL[c], lw=1.4, zorder=2)
        ax.errorbar(fc, y, xerr=100 * ci95(pc), fmt="o", ms=5, color=COL[c], mfc=COL[c], mec=COL[c], elinewidth=0.8, capsize=0, zorder=3)
        ax.errorbar(fw, y, xerr=100 * ci95(pw), fmt="o", ms=5, color=COL[c], mfc="white", mec=COL[c], mew=1.2, elinewidth=0.8, capsize=0, zorder=3)
        ax.text(101.5, y, f"{d.followed.mean() * 100:.0f}% overall", va="center", fontsize=6.5, color=COL[c])
    ax.set_yticks(range(5))
    ax.set_yticklabels([NAME[c] for c in ORDER][::-1])
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("Problems on which the final answer followed the assistant (%)", fontsize=7)
    ax.set_xlim(75, 112)
    ax.set_ylim(-0.7, 4.6)
    ax.set_xticks([80, 90, 100])
    ax.grid(axis="x", color="#eeeeee", lw=0.5, zorder=0)
    h = [plt.Line2D([], [], marker="o", ms=5, mfc="#4d4d4d", mec="#4d4d4d", ls="none", label="advice correct"),
         plt.Line2D([], [], marker="o", ms=5, mfc="white", mec="#4d4d4d", mew=1.2, ls="none", label="advice wrong")]
    ax.legend(handles=h, loc="lower center", frameon=False, fontsize=6.5, ncol=2, bbox_to_anchor=(0.45, -0.62))
    fig.tight_layout()
    save(fig, "reliance_follow.pdf")


if __name__ == "__main__":
    forest()
    confidence()
    difficulty()
    reliance()
    print("figures written to", OUTDIRS)
