#!/usr/bin/env python3
"""
Qualitative coding of the post-study free-text responses.

Corpus: the post-questionnaire free-text items extracted from the raw JSONs into
notebook_analysis_output/free_text_responses.csv (extraction included below, rerun-safe).

Two coded questions:
  1. STRATEGIES (all conditions): "Which strategies did you use to solve the tasks, check your
     answers, or improve your performance, if any?"  -> 12-code multi-label codebook, derived
     inductively from a stratified sample of ~90 responses, implemented as transparent lexical
     rules (auditable, reproducible). A response can carry several codes.
  2. MANIPULATION ("How, if at all, did <the manipulation> change ..."): 5-code codebook.

Caveat: lexical coding undercounts paraphrases and cannot resolve deep ambiguity; validate a
subsample by hand before publishing numbers (VALIDATE=True prints per-code samples).
"""

import csv, json, re, collections
import numpy as np
from scipy.stats import chi2_contingency

OUT = "notebook_analysis_output"
CONDS = ["ai", "ai-reliability", "alternatives", "pause-points", "reflection-task"]
VALIDATE = False

# ---------------------------------------------------------------- extraction --
def extract():
    rows = []
    for f, postq in [("ai.json", "21"), ("ai_reliability.json", "21"),
                     ("alternatives.json", "21"), ("pause_points.json", "21"),
                     ("reflection_task.json", "33")]:
        with open(f"../../../data_analysis/raw_data/data/final_data/{f}") as fh:
            data = json.load(fh)
        for p in data["participants"]:
            for key, r in p["tasks"].get(postq, {}).get("responses", {}).items():
                a = r.get("answer")
                if a is None or re.fullmatch(r"\d+", str(a).strip()):
                    continue
                rows.append({"participant_id": p["participantId"], "condition": p["condition"],
                             "item": key, "question": (r.get("question") or "").strip(),
                             "text": str(a).strip()})
    with open(f"{OUT}/free_text_responses.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["participant_id", "condition", "item", "question", "text"])
        w.writeheader(); w.writerows(rows)
    return rows

try:
    rows = list(csv.DictReader(open(f"{OUT}/free_text_responses.csv")))
except FileNotFoundError:
    rows = extract()

# ------------------------------------------------------- strategy codebook --
# label -> (description, [regexes]); text is lowercased before matching
STRATEGY_CODES = {
    "full_reliance": ("Relied on / trusted the AI wholly", [
        r"\b(relied|rely|relying|leaned|leant|depend(ed|ing)?)\b[^.]{0,25}\bai\b",
        r"\btrust(ed)?\b[^.]{0,15}\bai\b",
        r"\bwent with (the )?ai\b", r"\baccept(ed)? (the )?ai",
        r"\bai (did|do|to do) (it|most|everything|the work)",
        r"\b(just|simply|only) (copied|pasted|asked|used) ", r"copied and pasted the (questions|scenario)",
        r"\bused? (the )?ai (exclusively|fully|solely|for (most|everything|all))",
        r"relied (heavily|mostly|mainly|completely|solely|fully|entirely)",
    ]),
    "own_first_then_compare": ("Formed own answer first, then compared with the AI", [
        r"\b(my|our) own (answer|conclusion|logic|thought|thinking|reasoning|response)",
        r"\bmyself[^.]{0,45}\b(then|before|compar|check|ai)\b",
        r"\b(answer|solve|work(ed)?( it| them)? out|figure(d)?( it| them)? out|read)[^.]{0,20}\b(myself|my ?self|on my own|first)\b[^.]{0,40}\bai\b",
        r"\b(first|before)[^.]{0,40}\b(asking|checking|consulting|using)[^.]{0,15}ai",
        r"compar(e|ed|ing) (my|our) (answers?|conclusions?|results?)",
    ]),
    "verify_against_source": ("Checked the AI's answer against the scenario/brief text", [
        r"\b(back|refer(red)?|return(ed)?|went back|check(ed)?|cross.?check(ed)?|re.?read)[^.]{0,35}\b(scenario|text|brief|source|passage|original|information (given|provided)|the details)",
        r"\b(scenario|text|brief|information)\b[^.]{0,35}\b(check|compar|verify|confirm)",
        r"against (the )?(scenario|text|information|details)",
    ]),
    "ai_self_verify": ("Verification delegated to the AI itself (double-check, re-ask, confidence)", [
        r"\b(ask(ed|ing)?|made|make|got|tell|told|prompt(ed)?|had|have|request(ed)?)\b[^.]{0,30}\bai\b[^.]{0,45}\b(double.?check|check|verify|confirm|review|re.?view|sure|confiden|certain)",
        r"\bai\b[^.]{0,25}\b(double.?check|check(ed)?) (it(self|s own)?|its (answers?|reasoning|work|findings))",
        r"\bask(ed|ing)?\b[^.]{0,30}\b(again|multiple times|several times|twice|repeatedly|to be sure)",
        r"\b(re.?asked|re.?prompt|regenerat)", r"asked (the )?ai (how )?(its |it was )?confiden",
    ]),
    "reasoning_check": ("Read/critiqued the AI's reasoning or logic", [
        r"\b(check|read|review|follow|evaluate|assess|examin|scan|oversee|critiq|scrutin|interrogat)\w*\b[^.]{0,35}\b(reasoning|logic|thinking|rationale|explanation|justification|working)",
        r"\b(reasoning|logic|explanation|rationale)s?\b[^.]{0,35}\b(check|made sense|makes sense|sound|correct|seemed)",
        r"logical fallac", r"see if [^.]{0,25}ma(k|d)e[s]? sense",
    ]),
    "effort_cost_time": ("Workload/time pressure given as reason for reliance", [
        r"\b(too|very|quite|really|far too) (time.?consum\w*|long|complicated|complex|hard|difficult|demanding|taxing|overwhelm\w*|intense|much)",
        r"time (limit|constraint|pressure|allowed)", r"\bsave(d)? time", r"\bquick(er|ly)\b",
        r"mentally (demanding|taxing|draining|challenging)", r"too much (to read|information|reading|text)",
        r"information (dump|overload)", r"(no|not have|ran out of|short on) time", r"\boverwhelm",
    ]),
    "selective_reliance": ("Did easy items alone, used AI for hard ones (or vice versa)", [
        r"\b(easier|easy|simple)\b[^.]{0,30}\b(myself|my own|alone|without)",
        r"\b(hard(er)?|difficult|too (hard|difficult|complex))\b[^.]{0,35}\b(ai|assistant|help)", r"challenging(?! the ai)[^.]{0,25}\b(ai|assistant|help)",
        r"myself[^.]{0,45}(hard(er)?|difficult|challenging)[^.]{0,25}(ai|assistant)",
        r"\bsometimes\b[^.]{0,25}\b(myself|own)\b[^.]{0,35}\bai\b",
    ]),
    "prompt_engineering": ("Structured the interaction: decomposition, rephrasing, context hygiene", [
        r"\bbr(eak|oke|eaking)( it| the task| things)? down", r"one (question|task|statement|thing) at a time",
        r"\bstep.?by.?step\b", r"simpl(er|ify|ified|e) (language|terms|words)",
        r"\bre.?(phrase|word(ed)?|explain(ed)?)", r"\bstructur(e|ed|ing)\b[^.]{0,15}(prompt|question)",
        r"new (chat|conversation)", r"clear(ing|ed)? (the )?(chat|context|conversation|old)",
        r"\berasing\b", r"paste[d]? (each|separately|one)", r"\bsummaris|\bsummariz|\bsimplif", r"\btables?\b",
        r"\bnotes?\b[^.]{0,15}(down|paper)|wrote (down|notes)|writing things down|noted down",
    ]),
    "manipulation_use": ("Used the condition's own feature as a strategy (own condition only)", []),
    "overrode_ai": ("Disagreed with / overruled / challenged the AI", [
        r"\bover.?(rul|rode|ride|ruled)", r"\bdisagree", r"\bchalleng(ed|ing)",
        r"\b(went|go|going) against", r"\bquestion(ed)? (the )?ai",
        r"\b(did ?n[o']t|didn.t|never) (agree|accept|rely|follow|trust)",
        r"\bcorrect(ed)? (the )?ai", r"\bwrong\b[^.]{0,25}\b(ai|it was)",
    ]),
    "unspecified_verification": ("Double-checked / verified without saying how (residual)", [
        r"double.?check", r"\bcheck(ed)?\b[^.]{0,10}\b(my|the|each|every|all)\b[^.]{0,15}\b(answers?|results?|options?|work|times?|schedules?)",
        r"\bmanually check", r"check(ed)?( it| them)? myself", r"\bverif(y|ied)\b", r"\bfact.?check",
    ]),
    "no_strategy": ("Explicitly no strategy / gut feeling (short answers only)", [
        r"^(none|no|n/?a|nothing|not really|no strategy|no strategies|gut (reaction|feeling)|nope)[.!\s]*$",
    ]),
}
# own-condition feature lexicons for manipulation_use
FEATURE_LEX = {
    "ai-reliability": [r"\breliabilit", r"confidence (score|information|level|rating)", r"\bpercentage", r"\b\d{1,3}\s?%"],
    "alternatives": [r"\b(both|two|different|each) (ai|answers?|responses?|replies|models?|assistants?|options?)",
                      r"response[s]? a and b", r"\b(a and b|a & b)\b", r"\bagree(d)?\b", r"\bmatch(ed)?\b",
                      r"\bconsistent", r"\bconflict", r"\bdiscrepanc", r"\bdiffered\b", r"compare[d]? (the )?(answers|responses|replies)"],
    "pause-points": [r"\bstep", r"\bpause"],
    "reflection-task": [r"\breflect"],
    "ai": [],
}
NEGATION = re.compile(r"(did ?n[o']t|didn.t|never|not) (rely|trust|depend)")

def code_strategy(text, cond):
    t = text.lower()
    codes = set()
    for label, (_, pats) in STRATEGY_CODES.items():
        if label == "manipulation_use":
            pats = FEATURE_LEX.get(cond, [])
        elif label == "prompt_engineering" and cond == "pause-points":
            pats = [p for p in pats if "step" not in p]
        for p in pats:
            if re.search(p, t):
                codes.add(label); break
    if "full_reliance" in codes and NEGATION.search(t):
        codes.discard("full_reliance")
    if "no_strategy" in codes and len(codes) > 1:
        codes.discard("no_strategy")
    if "unspecified_verification" in codes and codes & {
            "verify_against_source", "ai_self_verify", "reasoning_check", "own_first_then_compare"}:
        codes.discard("unspecified_verification")
    return codes

# --------------------------------------------------- manipulation codebook --
MANIP_CODES = {
    "no_change": [r"^(no|none|n/?a|not at all|nothing|it did ?n[o']?t|didn.?t|no,? (it|not))\b.{0,40}$",
                  r"did ?n[o']t (really )?(change|affect|alter|make)", r"didn.t (really )?(change|affect|alter|make)",
                  r"no (real |big |much )?(change|difference|impact|effect)", r"\bignored?\b", r"same as (usual|always|before)"],
    "more_careful": [r"more (careful|cautious|critical|attentive|aware|thorough|alert|vigilant|sceptical|skeptical)",
                     r"\bcarefully\b", r"double.?check", r"\bevaluate", r"\bscrutin", r"\bverify",
                     r"question(ed)? (it|things|the ai)? ?more", r"less likely to (just )?accept",
                     r"made me (think|check|read|look|consider|pause)", r"pay (more )?attention", r"slow(ed)? down and (think|check)"],
    "slowed_friction": [r"slow(ed|er)? (me |it |things )?down", r"took (much |a lot |far )?longer",
                        r"\btedious\b", r"\bannoy", r"\bfrustrat", r"\bcumbersome", r"\birritat",
                        r"more (time|effort|steps|work|prompts|questions)", r"had to (keep|repeatedly|constantly)",
                        r"extra (steps|prompts|questions|work)", r"\blonge?r process", r"time.?consuming"],
    "trust_more": [r"trust(ed)? (it|the ai|them)? ?more", r"more trust", r"increas(ed|ing) (my )?trust",
                   r"more confiden(t|ce) in (the )?ai", r"\breassur", r"felt (more )?(safe|secure|confident)"],
    "trust_less": [r"trust(ed)? (it|the ai|them)? ?less", r"less trust", r"(lost|reduced|decreased|lowered) (my )?trust",
                   r"\bdoubt", r"\bsceptic|\bskeptic", r"\bwary\b", r"\bsuspicious", r"less confiden(t|ce) in (the )?ai",
                   r"made me (question|distrust)", r"couldn.t trust|could not trust"],
}
def code_manip(text):
    t = text.lower()
    codes = {label for label, pats in MANIP_CODES.items() if any(re.search(p, t) for p in pats)}
    if "no_change" in codes and len(codes) > 1 and len(t) > 60:
        codes.discard("no_change")
    return codes

# --------------------------------------------------------------- run coding --
strat_rows = [r for r in rows if r["question"].startswith("Which strategies")]
manip_rows = [r for r in rows if r["question"].startswith("How, if at all")]
# drop the 3 wave-2-baseline answers to an intervention-worded manipulation question
manip_rows = [r for r in manip_rows if r["condition"] != "ai"]

coded = []
for r in strat_rows:
    codes = code_strategy(r["text"], r["condition"])
    coded.append({**r, "codes": ";".join(sorted(codes)) if codes else "UNCODED"})
with open(f"{OUT}/qualitative_codes_strategies.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(coded[0].keys())); w.writeheader(); w.writerows(coded)

# participant level: pool a participant's manipulation answers (ai-reliability has two items)
by_pid = collections.defaultdict(list)
for r in manip_rows:
    by_pid[(r["participant_id"], r["condition"])].append(r["text"])
coded_m = []
for (pid, cond), texts in by_pid.items():
    codes = set()
    for t in texts:
        codes |= code_manip(t)
    if "no_change" in codes and len(codes) > 1:
        codes.discard("no_change")
    coded_m.append({"participant_id": pid, "condition": cond, "item": "pooled",
                    "question": "manipulation (pooled)", "text": " || ".join(texts),
                    "codes": ";".join(sorted(codes)) if codes else "UNCODED"})
with open(f"{OUT}/qualitative_codes_manipulation.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(coded_m[0].keys())); w.writeheader(); w.writerows(coded_m)

# ------------------------------------------------------------------ report --
n_by_cond = collections.Counter(r["condition"] for r in strat_rows)
print("=" * 100)
print("STRATEGIES QUESTION - code prevalence (% of respondents per condition; multi-label)")
print(f"Respondents: {dict(n_by_cond)}  |  uncoded: "
      f"{sum(1 for c in coded if c['codes']=='UNCODED')}/{len(coded)}")
print("=" * 100)
hdr = f"{'code':<24s}" + "".join(f"{c[:10]:>12s}" for c in CONDS) + f"{'chi2(4)':>9s}{'p':>8s}"
print(hdr); print("-" * 100)
for label in STRATEGY_CODES:
    row = f"{label:<24s}"
    counts, tots = [], []
    for c in CONDS:
        n = sum(1 for r in coded if r["condition"] == c and label in r["codes"].split(";"))
        counts.append(n); tots.append(n_by_cond[c])
        row += f"{100*n/n_by_cond[c]:11.1f}%"
    obs = np.array([counts, [t - k for t, k in zip(tots, counts)]])
    try:
        chi2, p, _, _ = chi2_contingency(obs)
        row += f"{chi2:9.2f}{p:8.3f}" + (" *" if p < 0.05 else "")
    except ValueError:
        row += "        -       -"
    print(row)

print()
print("=" * 100)
print("MANIPULATION QUESTION - code prevalence (% of respondents; own condition's wording)")
n_by_cond_m = collections.Counter(r["condition"] for r in coded_m)
print(f"Respondents: {dict(n_by_cond_m)}  |  uncoded: "
      f"{sum(1 for c in coded_m if c['codes']=='UNCODED')}/{len(coded_m)}")
print("=" * 100)
hdr = f"{'code':<24s}" + "".join(f"{c[:10]:>14s}" for c in CONDS if c != "ai")
print(hdr); print("-" * 100)
for label in MANIP_CODES:
    row = f"{label:<24s}"
    for c in CONDS:
        if c == "ai": continue
        n = sum(1 for r in coded_m if r["condition"] == c and label in r["codes"].split(";"))
        row += f"{100*n/n_by_cond_m[c]:13.1f}%"
    print(row)

# validation samples
if VALIDATE:
    import random
    random.seed(7)
    print("\n" + "=" * 100 + "\nVALIDATION SAMPLES (6 per code)\n" + "=" * 100)
    for label in STRATEGY_CODES:
        hits = [r for r in coded if label in r["codes"].split(";")]
        print(f"\n--- {label} (n={len(hits)}) ---")
        for r in random.sample(hits, min(6, len(hits))):
            print(f"  [{r['condition'][:8]}] {r['text'][:150]}")
    unc = [r for r in coded if r["codes"] == "UNCODED"]
    print(f"\n--- UNCODED (n={len(unc)}) ---")
    for r in random.sample(unc, min(12, len(unc))):
        print(f"  [{r['condition'][:8]}] {r['text'][:150]}")
