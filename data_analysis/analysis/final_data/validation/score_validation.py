#!/usr/bin/env python3
"""Score the lexical codebook (qualitative_coding.py) against the hand labels.

Protocol: the dev sample (n=160) was hand-labeled blind against codebook v1; v2 fixed the
rule gaps it exposed. The held-out sample (n=120, fresh, non-overlapping) was then hand-labeled
blind and scored once against v2 — those are the reportable reliability numbers.

Usage: python3 score_validation.py [dev|holdout]
"""
import csv, collections, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.dirname(HERE))          # qualitative_coding uses paths relative to final_data/
sys.path.insert(0, os.path.dirname(HERE))
from qualitative_coding import code_strategy, code_manip
os.chdir(HERE)

which = sys.argv[1] if len(sys.argv) > 1 else "holdout"
prefix = {"dev": "dev", "holdout": "holdout"}[which]
key = {r["vid"]: r for r in csv.DictReader(open(f"{prefix}_sample_key.csv"))}
hand = {r["vid"]: set(filter(None, r["hand_codes"].split(";")))
        for r in csv.DictReader(open(f"{prefix}_hand_labels.csv"))}
for v in hand.values():
    v.discard("selective_reliance")  # retired after dev round

stats = collections.defaultdict(lambda: [0, 0, 0])
exact, jac, n = {"S": 0, "M": 0}, {"S": 0.0, "M": 0.0}, {"S": 0, "M": 0}
for vid, k in key.items():
    qt = k["qtype"]
    if qt == "S":
        machine = code_strategy(k["text"], k["condition"])
    else:
        machine = code_manip(k["text"].lower())
        if "no_change" in machine and len(machine) > 1:
            machine.discard("no_change")
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

print(f"{which} sample:")
print(f"{'code':<26s} {'TP':>3s} {'FP':>3s} {'FN':>3s} {'prec':>6s} {'rec':>6s}")
for c, (tp, fp, fn) in sorted(stats.items()):
    prec = tp / (tp + fp) if tp + fp else float("nan")
    rec = tp / (tp + fn) if tp + fn else float("nan")
    print(f"{c:<26s} {tp:3d} {fp:3d} {fn:3d} {prec:6.2f} {rec:6.2f}")
for qt, name in [("S", "strategies"), ("M", "manipulation")]:
    print(f"{name}: exact {exact[qt]}/{n[qt]}, mean Jaccard {jac[qt]/n[qt]:.2f}")
