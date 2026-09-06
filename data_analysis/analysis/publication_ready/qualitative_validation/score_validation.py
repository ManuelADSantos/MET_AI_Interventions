#!/usr/bin/env python3
"""Score the lexical codebook (qualitative_coding.py) against the hand labels.

Protocol: the dev sample (n=160) was hand-labeled blind against codebook v1; v2 fixed the
rule gaps it exposed. The held-out sample (n=120, fresh, non-overlapping) was then hand-labeled
blind and scored once against v2 — those are the reportable reliability numbers.

Usage: python3 score_validation.py [dev|holdout|full] [--labels FILE --labels-col COL] [--compare FILE]
Standard library only.
"""
import csv, re, collections, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
# Machine codes come from the stored codebook-v2 output (../data/qualitative_codes_*.csv), keyed by participant and
# question type, so this script needs neither the raw chat logs nor qualitative_coding.py.
MACHINE = {}
for f, qt in [("strategies", "S"), ("manipulation", "M")]:
    for r in csv.DictReader(open(f"../data/qualitative_codes_{f}.csv")):
        MACHINE[(r["participant_id"], qt)] = {c for c in r["codes"].split(";") if c and c != "UNCODED"}

import argparse
ap = argparse.ArgumentParser()
ap.add_argument("which", nargs="?", default="holdout", choices=["dev", "holdout", "full"],
                help="full = every analysed answer (full_coding_sheet.csv; 814 strategy + 640 manipulation)")
ap.add_argument("--labels", default=None, help="CSV with vid and a label column (default: <which>_hand_labels.csv)")
ap.add_argument("--labels-col", default="hand_codes", help="column holding ';'-separated codes")
ap.add_argument("--compare", default=None, help="second label CSV (hand_codes column) to compute per-code Cohen's kappa against --labels")
args = ap.parse_args()
which = args.which
if which == "full":
    key = {r["vid"]: dict(r, qtype="S" if r["question"].startswith("STRATEGIES") else "M")
           for r in csv.DictReader(open("full_coding_sheet.csv"))}
    labels_file = args.labels or "full_coding_sheet.csv"
    if args.labels_col == "hand_codes":
        args.labels_col = "human_codes"
else:
    key = {r["vid"]: r for r in csv.DictReader(open(f"{which}_sample_key.csv"))}
    labels_file = args.labels or f"{which}_hand_labels.csv"
# shorthand accepted in the label column: a-k = strategy codes, 0-4 = manipulation codes (order as in CODEBOOK.md)
SHORT = dict(zip("abcdefghijk", ["full_reliance", "own_first_then_compare", "verify_against_source", "ai_self_verify",
                                 "reasoning_check", "effort_cost_time", "prompt_engineering", "manipulation_use",
                                 "overrode_ai", "unspecified_verification", "no_strategy"]))
SHORT.update(dict(zip("01234", ["no_change", "more_careful", "slowed_friction", "trust_more", "trust_less"])))
def parse(cell):
    out = set()
    for c in re.split(r"[;,\s]+", cell.strip().lower()):
        if not c:
            continue
        if c in SHORT:
            out.add(SHORT[c])
        elif all(ch in SHORT for ch in c):   # run of shorthand keys, e.g. "bd" or "01"
            out.update(SHORT[ch] for ch in c)
        else:
            out.add(c)
    return out
assert parse("b;d") == parse("bd") == parse("B, d") == {"own_first_then_compare", "ai_self_verify"}
assert parse("0") == {"no_change"} and parse("own_first_then_compare;1") == {"own_first_then_compare", "more_careful"}
assert parse("") == set()
MANIP = {"no_change", "more_careful", "slowed_friction", "trust_more", "trust_less"}
hand = {}
for r in csv.DictReader(open(labels_file)):
    hand[r["vid"]] = parse(r[args.labels_col])
    q = r.get("question", "")
    wrong = hand[r["vid"]] & MANIP if q.startswith("STRATEGIES") else hand[r["vid"]] - MANIP if q.startswith("MANIPULATION") else set()
    if wrong:
        print(f"WARNING {r['vid']}: codes {sorted(wrong)} do not belong to a {q.split(':')[0]} row")
if args.compare:
    other = {r["vid"]: parse(r["hand_codes"]) for r in csv.DictReader(open(args.compare))}
    codes = sorted({c for v in list(hand.values()) + list(other.values()) for c in v})
    print(f"Cohen's kappa, {labels_file} vs {args.compare} (n = {len(hand)}):")
    for c in codes:
        a = [c in hand[v] for v in hand]; b = [c in other.get(v, set()) for v in hand]
        po = sum(x == y for x, y in zip(a, b)) / len(a)
        pe = (sum(a) / len(a)) * (sum(b) / len(b)) + (1 - sum(a) / len(a)) * (1 - sum(b) / len(b))
        kappa = (po - pe) / (1 - pe) if pe < 1 else float("nan")
        print(f"  {c:28s} kappa = {kappa:.2f} (n coded: {sum(a)} vs {sum(b)})")
    print()
for v in hand.values():
    v.discard("selective_reliance")  # retired after dev round

stats = collections.defaultdict(lambda: [0, 0, 0])
exact, jac, n = {"S": 0, "M": 0}, {"S": 0.0, "M": 0.0}, {"S": 0, "M": 0}
for vid, k in key.items():
    qt = k["qtype"]
    machine = MACHINE[(k["participant_id"], qt)]
    h = hand.get(vid, set())
    n[qt] += 1
    if machine == h:
        exact[qt] += 1
    u = machine | h
    jac[qt] += len(machine & h) / len(u) if u else 1.0
    for c in u:
        if c in machine and c in h: stats[c][0] += 1
        elif c in machine: stats[c][1] += 1
        else: stats[c][2] += 1

if which == "full":
    coded = sum(1 for v in key if (hand.get(v) is not None))
    print(f"full set: {len(key)} answers, {coded} rows present in the label file")
    # tab:qual from the human codes: prevalence (%) per condition and code
    by = collections.defaultdict(lambda: collections.defaultdict(int)); nn = collections.defaultdict(int)
    for vid, k in key.items():
        nn[(k["qtype"], k["condition"])] += 1
        for c in hand.get(vid, set()):
            by[(k["qtype"], c)][k["condition"]] += 1
    conds = ["ai", "ai-reliability", "alternatives", "pause-points", "reflection-task"]
    for qt, name in [("S", "strategies"), ("M", "manipulation")]:
        cs = [c for c in conds if nn[(qt, c)]]
        print(f"\nhuman-coded prevalence (%), {name}; n = " + ", ".join(f"{c} {nn[(qt, c)]}" for c in cs))
        for (q, code), d in sorted(by.items()):
            if q == qt:
                print(f"  {code:28s} " + " ".join(f"{100 * d[c] / nn[(qt, c)]:5.1f}" for c in cs))
print(f"{which} sample, codebook vs labels:")
print(f"{'code':<26s} {'TP':>3s} {'FP':>3s} {'FN':>3s} {'prec':>6s} {'rec':>6s}")
for c, (tp, fp, fn) in sorted(stats.items()):
    prec = tp / (tp + fp) if tp + fp else float("nan")
    rec = tp / (tp + fn) if tp + fn else float("nan")
    print(f"{c:<26s} {tp:3d} {fp:3d} {fn:3d} {prec:6.2f} {rec:6.2f}")
for qt, name in [("S", "strategies"), ("M", "manipulation")]:
    print(f"{name}: exact {exact[qt]}/{n[qt]}, mean Jaccard {jac[qt]/n[qt]:.2f}")
f1s = [2 * tp / (2 * tp + fp + fn) for tp, fp, fn in stats.values() if tp + fp + fn]
print(f"macro-F1 over {len(f1s)} codes: {sum(f1s) / len(f1s):.2f}")
