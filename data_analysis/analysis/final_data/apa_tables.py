r"""Render LaTeX tables for the paper from apa_results.json (run apa_results.py first).

Writes apa_tables.tex next to this file. Condition macros (\Base, \Cards, ...) are the paper's.
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
J = json.load(open(os.path.join(HERE, "apa_results.json")))
MACRO = {"ai": r"\Base", "ai-reliability": r"\Cards", "alternatives": r"\Alts",
         "pause-points": r"\Pausep", "reflection-task": r"\Refl"}
ORDER = ["ai", "ai-reliability", "alternatives", "pause-points", "reflection-task"]
NAME = {"absolute_estimation_error": "Estimation error (0--12)", "signed_estimation_error": "Signed estimation error",
        "confidence_discrimination": r"$\Delta$Conf (pp)", "actual_score": "Score (0--12)",
        "prompts_per_task": "Prompts per problem", "sus_score": "SUS (0--100)", "ueq_overall": "UEQ-S ($-3$..$+3$)",
        "tlx_mean": "NASA-TLX (0--20)", "trust_mean": "Trust (1--5)"}


def p_fmt(p):
    return "$<.001$" if p < .001 else f"${p:.3f}$".replace("0.", ".")


def num(x, nd=2, sign=False):
    s = f"{x:+.{nd}f}" if sign else f"{x:.{nd}f}"
    return s.replace("-", "$-$") if not sign else s.replace("+", "$+$").replace("-", "$-$")


def block(res, first):
    w = res["anova"]
    rows = []
    omnibus = (f"$F({w['df1']:.0f}, {w['df2']:.0f}) = {w['F']:.2f}$, $p {p_fmt(w['p']).strip('$')}$, "
               f"$\\omega^2 = {w['omega2']:.3f}$".replace("= .", "= .").replace("$p <.001$", "$p < .001$"))
    omnibus = omnibus.replace("$p .", "$p = .")
    bf10 = res['bayes']['BF10']
    bf = f"$BF_{{10}} > 10^{{{int(np.floor(np.log10(bf10)))}}}$" if bf10 > 1000 else f"$BF_{{10}} = {bf10:.2f}$"
    rows.append(f"    \\multicolumn{{6}}{{l}}{{\\textit{{{NAME[res['outcome']]}}}: {omnibus}; JZS {bf}}} \\\\")
    for c in ORDER:
        d = res["desc"][c]
        if c == "ai":
            rows.append(f"    \\quad {MACRO[c]} & {d['n']} & {d['M']:.2f} ({d['SD']:.2f}) & --- & --- & --- \\\\")
        else:
            v = res["vs_baseline"][c]
            rows.append(f"    \\quad {MACRO[c]} & {d['n']} & {d['M']:.2f} ({d['SD']:.2f}) & "
                        f"${v['t']:.2f}$ ({v['df']:.0f}) & {p_fmt(v['p'])} & "
                        f"{num(v['g'], sign=True)} [{num(v['ci'][0], sign=True)}, {num(v['ci'][1], sign=True)}] \\\\".replace("$-", "$-").replace("$$", ""))
    return rows


def table(outcomes, label, caption):
    L = [r"\begin{table*}[ht]", f"  \\caption{{{caption}}}", f"  \\label{{{label}}}", r"  \footnotesize",
         r"  \setlength{\tabcolsep}{4pt}", r"  \begin{tabular}{lrrrrl}", r"    \toprule",
         r"    Outcome / condition & $n$ & $M$ ($SD$) & $t$ ($df$) vs.\ \base & $p$ & Hedges' $g$ [95\% CI] \\", r"    \midrule"]
    res_by = {r["outcome"]: r for r in J["outcomes"]}
    for i, o in enumerate(outcomes):
        if i:
            L.append(r"    \addlinespace[3pt]")
        L += block(res_by[o], i == 0)
    L += [r"    \bottomrule", r"  \end{tabular}", r"\end{table*}", ""]
    return L


def games_howell(outcome):
    res = {r["outcome"]: r for r in J["outcomes"]}[outcome]
    L = [f"% Tukey HSD all pairs for {outcome} (df = {res['tukey'][0]['df']:.0f})"]
    for r in res["tukey"]:
        L.append(f"% {MACRO[r['A']]} vs {MACRO[r['B']]}: t({r['df']:.1f}) = {r['t']:.2f}, p = {r['p']:.3f}, g = {r['g']:+.2f}")
    return L + [""]


def reliance_table():
    R = J["reliance"]
    L = [r"\begin{table}[ht]",
         r"  \caption{Behavioral reliance from the parsed assistant verdicts: share of problems with a parsed verdict (coverage); share of covered problems on which the final answer followed the verdict, overall and split by whether the verdict was correct; accuracy when following and when overriding; accuracy of the parsed advice. \Alts verdicts exist only where both replies agreed.}",
         r"  \label{tab:reliance}", r"  \footnotesize", r"  \setlength{\tabcolsep}{3.5pt}", r"  \begin{tabular}{lrrrrrrr}", r"    \toprule",
         r"    Condition & Coverage & Followed & \multicolumn{2}{c}{Followed when advice was} & Correct if & Correct if & Advice \\",
         r"    & & & correct & wrong & followed & overrode & correct \\", r"    \midrule"]
    for c in ORDER:
        b = R["by_condition"][c]
        L.append(f"    {MACRO[c]} & {100*R['coverage'][c]:.0f}\\% & {100*b['follow_rate']:.1f}\\% & {100*b['follow_given_ai_correct']:.1f}\\% & "
                 f"{100*b['follow_given_ai_wrong']:.1f}\\% & {100*b['follow_success']:.1f}\\% & {100*b['override_success']:.1f}\\% & {100*b['ai_accuracy']:.1f}\\% \\\\")
    L += [r"    \bottomrule", r"  \end{tabular}", r"\end{table}", ""]
    pl = R["participant_level"]
    L.append(f"% per-participant follow rate: Welch F({pl['welch']['df1']:.0f}, {pl['welch']['df2']:.1f}) = {pl['welch']['F']:.2f}, p = {pl['welch']['p']:.2e}")
    for c in ORDER:
        d = pl["desc"][c]
        s = f"% {MACRO[c]}: M = {d['M']:.3f} (SD {d['SD']:.3f}), n = {d['n']}"
        if c != "ai":
            v = pl["vs_baseline"][c]
            s += f"; t({v['df']:.1f}) = {v['t']:.2f}, p = {v['p']:.3f}, g = {v['g']:+.2f} [{v['ci'][0]:+.2f}, {v['ci'][1]:+.2f}]"
        L.append(s)
    for key in ["gee_followed", "gee_followed_x_aicorrect", "gee_followed_x_difficulty", "gee_correct_given_override"]:
        L.append(f"% {key}")
        for k, v in R[key].items():
            L.append(f"%   {k}: OR = {v['OR']:.2f}, z = {v['z']:.2f}, p = {v['p']:.3f}")
    return L


def null_table():
    N = J["extra"]["null_robustness"]
    L = [r"\begin{table}[ht]",
         r"  \caption{The performance result (score, 0--12) under alternative specifications. $BF_{0+}$: JZS Bayes factor favouring no improvement over a directional improvement ($r = 0.707$); two-sided $BF$: $BF_{01}$ for no difference, or $BF_{10}$ for a difference (\pausep); TOST: Welch equivalence test at $|g| < .3$; OR: GEE-logit odds ratio of a correct answer vs.\ baseline, with participant clustering and need for cognition and display position as covariates.}",
         r"  \label{tab:null}", r"  \small", r"  \begin{tabular}{lrrlrr}", r"    \toprule",
         r"    Condition & $g$ & $BF_{0+}$ & Two-sided $BF$ & TOST $p$ & GEE OR \\", r"    \midrule"]
    for c in ORDER[1:]:
        v = N[c]
        if v["BF10"] > 100:
            mant, ex = f"{v['BF10']:.1e}".split("e")
            two = f"$BF_{{10}} = {mant} \\times 10^{{{int(ex)}}}$"
        else:
            two = f"$BF_{{01}} = {v['BF01']:.1f}$"
        pt = "$<.001$" if v["tost_p"] < .001 else f"{v['tost_p']:.3f}".replace("0.", ".")
        L.append(f"    {MACRO[c]} & ${v['g']:.2f}$ & {v['BF0plus']:.1f} & {two} & {pt} & {v['gee_or']:.2f} \\\\")
    L += [r"    \bottomrule", r"  \end{tabular}", r"\end{table}", ""]
    return L


def main():
    out = []
    out += table(["absolute_estimation_error", "confidence_discrimination", "actual_score", "prompts_per_task"], "tab:effects",
                 r"Primary and secondary outcomes by condition: $M$ ($SD$), the one-way ANOVA across the five conditions with $\omega^2$ and the default Bayesian ANOVA $BF_{10}$ for a condition effect (JZS, $r = 0.5$), and the uncorrected two-sided $t$-test of each intervention against \base with Hedges' $g$ and its 95\% CI. Tukey HSD post-hoc tests are reported in the text.")
    out += table(["sus_score", "ueq_overall", "tlx_mean", "trust_mean"], "tab:ux",
                 r"Experience, workload, and trust by condition: $M$ ($SD$), the one-way ANOVA with $\omega^2$ and $BF_{10}$, and the uncorrected two-sided $t$-test of each intervention against \base with Hedges' $g$ [95\% CI]. Higher SUS and UEQ-S are better; higher NASA-TLX is worse.")
    for o in ["absolute_estimation_error", "confidence_discrimination", "actual_score", "prompts_per_task", "sus_score", "ueq_overall", "tlx_mean", "trust_mean"]:
        out += games_howell(o)
    out += reliance_table()
    out += null_table()
    open(os.path.join(HERE, "apa_tables.tex"), "w").write("\n".join(out) + "\n")
    print("wrote apa_tables.tex")


if __name__ == "__main__":
    main()
