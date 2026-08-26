#!/usr/bin/env python3
"""Parse the AI assistant's final per-problem verdict from participant chat logs and
compute behavioral reliance measures by condition.

Reads the raw per-condition JSONs (data_analysis/raw_data/data/final_data/*.json),
extracts the AI's recommended option (A/B/C/D) for each (participant, problem), and
compares it with the participant's submitted answer (task_metrics.csv, analyzed
sample only: exclude_primary == False).

Usage:
    python verdict_parse.py                    # writes VERDICT_PARSE.md next to this file
    python verdict_parse.py --validation-dump  # print the hand-check samples (seeded)

Parsing approach (see VERDICT_PARSE.md for the full write-up):
- All 12 scored problems share the same four options:
    A = Only statement 1 is correct.       B = Only statement 2 is correct.
    C = Both statements are correct.       D = Neither of the two statements is correct.
- Each assistant message is scanned for (a) full-option verdicts (verbatim or
  paraphrased), and (b) per-statement truth-value claims ("statement 1 is false",
  "1. True", "Statement 2: incorrect", block headings followed by a bare polarity).
- Messages are folded in chronological order into a per-task state (latest claim per
  statement wins), so revisions ("actually, statement 2 is true") override earlier
  verdicts, and one-statement-at-a-time conversations (common under pause-points) are
  combined across messages.
- A bare-polarity reply ("**True.**") with no statement reference is tied to a
  statement only when the immediately preceding user message quotes exactly one of the
  two known statement texts verbatim.
- A trial's parse is CONFIDENT only when both statements end with a known truth value
  (equivalently: exactly one option is implied). Internally conflicting messages
  (>1 option implied) contribute nothing.
- ALTERNATIVES condition: the assistant sent two replies per prompt (columns a/b) that
  often disagree by design. Each column is folded separately; a trial has a verdict
  only when BOTH columns parse and AGREE. Both-parse-but-disagree is recorded as
  'disagree' (undefined verdict, by design). Reported separately.
"""
import argparse
import json
import os
import random
import re
import unicodedata
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
RAW = os.path.join(REPO, 'data_analysis', 'raw_data', 'data', 'final_data')
NB = os.path.join(HERE, 'notebook_analysis_output')
TASKS_DIR = os.path.join(REPO, 'src', 'customizations', 'tasks')

COND_FILES = {'ai': 'ai', 'ai-reliability': 'ai_reliability', 'alternatives': 'alternatives',
              'pause-points': 'pause_points', 'reflection-task': 'reflection_task'}
COND_ORDER = ['ai', 'ai-reliability', 'pause-points', 'reflection-task', 'alternatives']
QUIZ = ["ypc_02", "ypc_03", "ypc_05", "ypc_06", "car_racing_01", "car_racing_02",
        "car_racing_03", "car_racing_05", "graduation_party_01", "graduation_party_05",
        "graduation_party_06", "graduation_party_07"]
CORRECT = {"ypc_02": "D", "ypc_03": "B", "ypc_05": "A", "ypc_06": "A",
           "car_racing_01": "D", "car_racing_02": "C", "car_racing_03": "B",
           "car_racing_05": "A", "graduation_party_01": "B", "graduation_party_05": "A",
           "graduation_party_06": "D", "graduation_party_07": "B"}
ANSWER_TEXT_TO_LETTER = {
    "Only statement 1 is correct.": "A", "Only statement 2 is correct.": "B",
    "Both statements are correct.": "C", "Neither of the two statements is correct.": "D"}
LETTER = {(True, False): 'A', (False, True): 'B', (True, True): 'C', (False, False): 'D'}
IMPLIES = {v: k for k, v in LETTER.items()}

TRUE_W = (r"(?:true|correct|right|accurate|possible|feasible|valid|holds)")
FALSE_W = (r"(?:false|incorrect|wrong|inaccurate|impossible|infeasible|invalid|untrue"
           r"|not\s+(?:true|correct|right|possible|feasible|valid)"
           r"|doesn'?t\s+hold|does\s+not\s+hold)")
# narrower polarity set for line-start "1. False — ..." rule (avoids "1. Possible schedule: ...")
NARROW_T = r"(?:true|correct|right|yes)"
NARROW_F = r"(?:false|incorrect|wrong|no|not\s+(?:true|correct|right))"
STMT = r"(?:statement|claim|sentence)"
NUM1 = r"(?:1|one|first)"
NUM2 = r"(?:2|two|second)"


# ---------------------------------------------------------------- text utilities
def normalize(t):
    t = unicodedata.normalize('NFKC', t)
    t = (t.replace('’', "'").replace('‘', "'")
          .replace('“', '"').replace('”', '"')
          .replace('–', '-').replace('—', '-').replace('→', '->'))
    t = re.sub(r'[*_`]+', '', t)                    # markdown emphasis
    t = re.sub(r'^#{1,6}\s*', '', t, flags=re.M)    # headings
    t = re.sub(r'^>\s?', '', t, flags=re.M)         # blockquotes
    return t.lower()


def squash(t):
    return re.sub(r'\s+', ' ', normalize(t)).strip()


def polarity_of(word):
    if re.fullmatch(FALSE_W, word) or re.fullmatch(NARROW_F, word):
        return False
    if re.fullmatch(TRUE_W, word) or re.fullmatch(NARROW_T, word):
        return True
    return None


# ------------------------------------------------- statement texts per question
def load_statements(md_file):
    """(s1, s2) per scored option block; first returned pair is the practice trial."""
    txt = open(os.path.join(TASKS_DIR, md_file)).read()
    opt_pos = [m.start() for m in re.finditer(
        r'\$option;\s*\n\s*Only statement 1 is correct', txt)]
    pair_re = re.compile(r'^> 1\. (.+)$\n(?:^>\s*$\n)*^> 2\. (.+)$', flags=re.M)
    pairs = [(m.start(), m.group(1), m.group(2)) for m in pair_re.finditer(txt)]
    out = []
    for pos in opt_pos:
        prev = [p for p in pairs if p[0] < pos]
        out.append((prev[-1][1], prev[-1][2]))
    return out


def build_statements():
    ai_pairs = load_statements('ai_tasks.md')
    assert len(ai_pairs) == 13, f"expected trial + 12 scored blocks, got {len(ai_pairs)}"
    stmts = {q: (squash(a), squash(b)) for q, (a, b) in zip(QUIZ, ai_pairs[1:])}
    for f in ('pause_points_tasks.md', 'reflection_task_tasks.md', 'alternatives_tasks.md'):
        other = load_statements(f)
        assert [(squash(a), squash(b)) for a, b in other[1:]] == [stmts[q] for q in QUIZ], \
            f"statement texts differ in {f}"
    for q, (a, b) in stmts.items():
        assert a not in b and b not in a, f"within-pair containment for {q}"
    return stmts


STATEMENTS = build_statements()


# ---------------------------------------------------------------- message parse
QUAL = r"(?:also\s+|probably\s+|likely\s+|definitely\s+|indeed\s+|in\s+fact\s+|actually\s+|still\s+|therefore\s+|thus\s+)?"


def parse_message(raw):
    """Scan one assistant message.
    Returns {'verdicts': set of option letters, 'pol': {1: set, 2: set}, 'bare': bool|None}.
    """
    t = normalize(raw)
    verdicts = set()
    pol = {1: set(), 2: set()}

    def n_of(g):
        return 1 if g in ('1', 'one', 'first') else 2

    # ---- full-option verdicts ----
    for m in re.finditer(rf"only\s+(?:the\s+)?{STMT}\s*({NUM1}|{NUM2})\s+is\s+{QUAL}{TRUE_W}", t):
        verdicts.add('A' if n_of(m.group(1)) == 1 else 'B')
    for m in re.finditer(rf"only\s+the\s+(first|second)\s+(?:{STMT}|one)\s+is\s+{QUAL}{TRUE_W}", t):
        verdicts.add('A' if m.group(1) == 'first' else 'B')
    for m in re.finditer(
            rf"(?:choice|answer|option|verdict|conclusion|assessment)\s*"
            rf"(?:is|would\s+be|:)\s*(?:the\s+)?only\s+{STMT}\s*({NUM1}|{NUM2})\b", t):
        verdicts.add('A' if n_of(m.group(1)) == 1 else 'B')
    for m in re.finditer(rf"{STMT}\s*({NUM1}|{NUM2})\s+is\s+the\s+only\s+{TRUE_W}", t):
        verdicts.add('A' if n_of(m.group(1)) == 1 else 'B')
    # both / neither
    for m in re.finditer(
            rf"both\s+(?:of\s+the\s+)?{STMT}s?\s+(?:are|is|were)\s+"
            rf"(?:in\s+fact\s+|indeed\s+|actually\s+)?({TRUE_W}|{FALSE_W})", t):
        p = polarity_of(m.group(1))
        if p is not None:
            verdicts.add('C' if p else 'D')
    for m in re.finditer(r"both\s+are\s+(true|false|correct|incorrect|wrong|right)\b", t):
        p = polarity_of(m.group(1))
        if p is not None:
            verdicts.add('C' if p else 'D')
    for m in re.finditer(rf"{STMT}s\s+1\s+and\s+2\s+are\s+(?:both\s+)?({TRUE_W}|{FALSE_W})", t):
        p = polarity_of(m.group(1))
        if p is not None:
            verdicts.add('C' if p else 'D')
    if re.search(rf"neither\s+(?:of\s+the\s+(?:two\s+)?)?(?:{STMT}s?\s+)?(?:is|are)\s+{QUAL}{TRUE_W}", t):
        verdicts.add('D')
    if re.search(rf"neither\s+(?:{STMT}\s+)?{NUM1}\s+nor\s+(?:{STMT}\s+)?{NUM2}\s+is\s+{TRUE_W}", t):
        verdicts.add('D')
    # "the correct statement is (number) 2 (only)" / "best guess is statement 1"
    for m in re.finditer(
            rf"(?:the\s+)?{TRUE_W}\s+{STMT}\s+is\s+(?:{STMT}\s+)?(?:number\s+)?({NUM1}|{NUM2})\b", t):
        verdicts.add('A' if n_of(m.group(1)) == 1 else 'B')
    for m in re.finditer(
            rf"(?:best\s+guess|my\s+guess|answer)\s+(?:is|would\s+be)\s+"
            rf"(?:{STMT}\s+)?({NUM1}|{NUM2})\b(?!\s*(?:and|,|\+|or))", t):
        verdicts.add('A' if n_of(m.group(1)) == 1 else 'B')

    # ---- per-statement truth values ----
    for m in re.finditer(
            rf"(?<!only ){STMT}\s*({NUM1}|{NUM2})\s+is\s+{QUAL}({TRUE_W}|{FALSE_W})", t):
        p = polarity_of(m.group(2))
        if p is not None:
            pol[n_of(m.group(1))].add(p)
    for m in re.finditer(
            rf"the\s+(first|second)\s+(?:{STMT}|one)\s+is\s+{QUAL}({TRUE_W}|{FALSE_W})", t):
        p = polarity_of(m.group(2))
        if p is not None:
            pol[1 if m.group(1) == 'first' else 2].add(p)
    # elided negation: "the first one is not." / "statement 2 is not."
    for m in re.finditer(rf"the\s+(first|second)\s+(?:{STMT}|one)\s+is\s+not\s*[.,;:!]", t):
        pol[1 if m.group(1) == 'first' else 2].add(False)
    for m in re.finditer(rf"{STMT}\s*({NUM1}|{NUM2})\s+is\s+not\s*[.,;:!]", t):
        pol[n_of(m.group(1))].add(False)
    # colon form: "Statement 1: true" / "- statement 2: not correct"
    for m in re.finditer(rf"{STMT}\s*([12])\s*[:\-]+\s*(?:is\s+)?({TRUE_W}|{FALSE_W})\b", t):
        p = polarity_of(m.group(2))
        if p is not None:
            pol[int(m.group(1))].add(p)
    # line-start numbered verdicts: "1. False — ..." / "2) True" / "statement 1. incorrect"
    for m in re.finditer(
            rf"^\s*(?:{STMT}\s*)?([12])[.):\-]\s*({NARROW_T}|{NARROW_F})\b(?=[\s.,:;!\-]|$)",
            t, flags=re.M):
        p = polarity_of(m.group(2))
        if p is not None:
            pol[int(m.group(1))].add(p)
    # block form: heading line "statement 1" / "1." then a standalone polarity line soon after
    lines = t.split('\n')
    ctx, ctx_age = None, 0
    for ln in lines:
        s = ln.strip()
        if re.match(rf"(?:{STMT}\s*[12]\b|[12][.)]\s)", s):
            hm = re.fullmatch(rf"(?:{STMT}\s*([12])|([12])[.)]?)\s*[:.]?(?:\s*\"?.{{0,300}}\"?)?", s)
            if hm:
                ctx, ctx_age = int(hm.group(1) or hm.group(2)), 0
                continue
        if ctx is not None:
            ctx_age += 1
            if ctx_age > 4:
                ctx = None
                continue
            pm = re.fullmatch(rf"(?:yes\s*[-,:]?\s*|no\s*[-,:]?\s*)?({TRUE_W}|{FALSE_W})[.! ]*", s)
            if pm:
                p = polarity_of(pm.group(1))
                if p is not None:
                    pol[ctx].add(p)
                ctx = None

    # combined per-statement polarity implies a full verdict
    s1 = next(iter(pol[1])) if len(pol[1]) == 1 else None
    s2 = next(iter(pol[2])) if len(pol[2]) == 1 else None
    if s1 is not None and s2 is not None:
        verdicts.add(LETTER[(s1, s2)])

    # bare polarity (statement-agnostic), only when nothing else was found
    bare = None
    if not verdicts and not pol[1] and not pol[2]:
        first = next((ln.strip() for ln in lines if ln.strip()), '')
        m = re.match(rf"(?:yes|no)?[\s,\-:]*(?:th(?:e|is|at)\s+statement\s+is\s+)?"
                     rf"({TRUE_W}|{FALSE_W})\b[.!]?", first)
        if m and len(first) < 80:
            bare = polarity_of(m.group(1))
        if bare is None:
            m2 = re.search(rf"th(?:e|is|at)\s+statement\s+is\s+{QUAL}({TRUE_W}|{FALSE_W})", t)
            if m2:
                bare = polarity_of(m2.group(1))
        if bare is None:
            fm = re.fullmatch(r"(yes|no)[.!\s]*", first)
            if fm:
                bare = fm.group(1) == 'yes'
    return {'verdicts': verdicts, 'pol': pol, 'bare': bare}


def which_statement_in(user_text, qname):
    """1 or 2 when the user message verbatim-contains exactly one statement text."""
    if not user_text:
        return None
    u = squash(user_text)
    s1, s2 = STATEMENTS[qname]
    in1, in2 = s1 in u, s2 in u
    if in1 and not in2:
        return 1
    if in2 and not in1:
        return 2
    return None


def fold_task(exchanges, qname):
    """Fold one task's exchanges [(role, column, content), ...] chronologically.
    Returns (verdict letter or None, mode) where mode in
    {'full', 'combined', 'partial', 'none'}."""
    state = {1: None, 2: None}
    last_user = None
    modes = []
    for role, _col, content in exchanges:
        if role == 'user':
            last_user = content
            continue
        r = parse_message(content)
        if len(r['verdicts']) > 1:
            continue  # internally conflicting message: contributes nothing
        if len(r['verdicts']) == 1:
            v = next(iter(r['verdicts']))
            state[1], state[2] = IMPLIES[v]
            modes.append('full')
            continue
        updated = False
        for n in (1, 2):
            if len(r['pol'][n]) == 1:
                state[n] = next(iter(r['pol'][n]))
                updated = True
        if updated:
            modes.append('numbered')
            continue
        if r['bare'] is not None:
            n = which_statement_in(last_user, qname)
            if n is not None:
                state[n] = r['bare']
                modes.append('bare-tied')
    if state[1] is not None and state[2] is not None:
        mode = 'full' if (modes and modes[-1] == 'full') else 'combined'
        return LETTER[(state[1], state[2])], mode
    return None, ('partial' if (state[1] is not None or state[2] is not None) else 'none')


def exchanges_by_task(p):
    by = defaultdict(list)
    for m in p['messages']:
        if not m:
            continue
        if m.get('role') == 'user':
            by[m.get('task')].append(('user', None, m.get('content') or ''))
        else:
            c = (m.get('choices') or [{}])[0].get('message', {}).get('content', '') or ''
            if c.strip():
                by[m.get('survey_index')].append(('assistant', m.get('column'), c))
    return by


def parse_trial(exchanges, qname, cond):
    """Returns (verdict letter or None, mode)."""
    if cond != 'alternatives':
        return fold_task(exchanges, qname)
    ex_a = [e for e in exchanges if e[0] == 'user' or e[1] == 'a']
    ex_b = [e for e in exchanges if e[0] == 'user' or e[1] == 'b']
    va, _ = fold_task(ex_a, qname)
    vb, _ = fold_task(ex_b, qname)
    if va and vb:
        return (va, 'agree') if va == vb else (None, 'disagree')
    if va or vb:
        return None, 'one-column'  # not confident: the unparsed column may disagree
    return None, 'none'


# --------------------------------------------------------------------- pipeline
def load_included():
    """pid -> condition for exclude_primary == False, and (pid, task_id) -> (answer letter, correct)."""
    import csv
    included = {}
    with open(os.path.join(NB, 'participant_metrics.csv')) as fh:
        for r in csv.DictReader(fh):
            if r['exclude_primary'] == 'False':
                included[r['participant_id']] = r['condition']
    answers = {}
    with open(os.path.join(NB, 'task_metrics.csv')) as fh:
        for r in csv.DictReader(fh):
            answers[(r['participant_id'], int(r['task_id']))] = (
                ANSWER_TEXT_TO_LETTER[r['answer']], float(r['correct']) == 1.0,
                r['task_name'])
    return included, answers


def run_parse():
    included, answers = load_included()
    trials = []  # dicts
    for cond, fname in COND_FILES.items():
        data = json.load(open(os.path.join(RAW, f'{fname}.json')))
        tids = list(range(6, 29, 2)) if cond == 'reflection-task' else list(range(6, 18))
        for p in data['participants']:
            pid = p['participantId']
            if included.get(pid) != cond:
                continue  # not in the analyzed sample (or excluded / repeat record)
            by = exchanges_by_task(p)
            for tid, q in zip(tids, QUIZ):
                ex = by.get(tid, [])
                verdict, mode = parse_trial(ex, q, cond)
                ans_letter, ans_correct, tname = answers[(pid, tid)]
                assert tname == q
                trials.append({
                    'condition': cond, 'pid': pid, 'task_id': tid, 'question': q,
                    'verdict': verdict, 'mode': mode, 'answer': ans_letter,
                    'answer_correct': ans_correct, 'correct_option': CORRECT[q],
                    'n_assistant_msgs': sum(1 for e in ex if e[0] == 'assistant'),
                    'exchanges': ex,
                })
    return trials


def fmt_pct(x, n):
    return f"{100 * x / n:.1f}%" if n else "--"


def condition_stats(trials, cond):
    T = [t for t in trials if t['condition'] == cond]
    n_trials = len(T)
    parsed = [t for t in T if t['verdict'] is not None]
    followed = [t for t in parsed if t['answer'] == t['verdict']]
    overrode = [t for t in parsed if t['answer'] != t['verdict']]
    st = {
        'n_participants': len({t['pid'] for t in T}),
        'n_trials': n_trials,
        'n_parsed': len(parsed),
        'coverage': len(parsed) / n_trials if n_trials else 0,
        'n_follow': len(followed),
        'n_override': len(overrode),
        'agree_rate': len(followed) / len(parsed) if parsed else None,
        'override_rate': len(overrode) / len(parsed) if parsed else None,
        'follow_success': (sum(t['answer_correct'] for t in followed) / len(followed)
                           if followed else None),
        'override_success': (sum(t['answer_correct'] for t in overrode) / len(overrode)
                             if overrode else None),
        'ai_accuracy': (sum(t['verdict'] == t['correct_option'] for t in parsed) / len(parsed)
                        if parsed else None),
        'modes': Counter(t['mode'] for t in T),
    }
    # mean per-participant agreement (participants with >= 1 parsed trial)
    per = defaultdict(lambda: [0, 0])
    for t in parsed:
        per[t['pid']][0] += t['answer'] == t['verdict']
        per[t['pid']][1] += 1
    rates = [a / b for a, b in per.values()]
    st['mean_pp_agreement'] = sum(rates) / len(rates) if rates else None
    st['n_pp_with_parse'] = len(rates)
    return st


# ------------------------------------------------------ validation hand-check
# Seeded stratified samples. Each key is (pid, task_id); value is the human judgment
# recorded after reading the transcript: True = parsed verdict is what the assistant's
# final stance actually was; False = parse error. NO_PARSE_REASONS classifies why
# sampled unparsed trials had no confident verdict.
VALIDATION_SEED = 20260826

HAND_CHECK = {
    # 40 stratified parsed trials, judged by reading the printed transcripts
    # (python verdict_parse.py --validation-dump). True = verdict matches the
    # assistant's final stance in the transcript.
    # -- ai --
    ('69ea247da4f33d963f6377bd', 9): True,   # revised to s2-false; final D correct
    ('6a0c2610d6081bf92e4be74d', 7): True,   # revised s2 true after challenge -> C
    ('6a0c2610d6081bf92e4be74d', 13): True,  # 500-vs-1000 discussion ends both-false -> D
    ('6a1c0a74391cb03e607159f3', 6): True,   # full msg concludes "Only statement 1"
    ('6a4da2ed98dcae617c8a7857', 6): True,
    ('5ca9106716aa84001725d880', 6): True,
    ('5ee10c33a3011311034f2cb1', 13): True,
    ('6a1d6ed2d1f659ae0b6ed638', 17): True,
    # -- ai-reliability --
    ('56896501d3d6a7000ca23da8', 7): True,   # bare True/False tied via pasted statements
    ('6a0f23984ca40187cbf977c3', 7): True,   # final msg hedges s2 but never reverses; latest decisive stance B
    ('69f6a9b7a7b418e1549df619', 9): True,   # C revised to B after "how is 1 correct?"
    ('6a0c18983b81664b14057d67', 11): True,
    ('671d39090c9e2ad9ec75a03c', 13): True,
    ('656f0ce82c0ba5e95ad58a03', 8): True,
    ('6a14ed94ddfccd8c074e9f98', 9): True,   # A revised to D once full context pasted
    ('6a0b23f183c91f11588f9713', 9): True,
    # -- pause-points --
    ('68729361bee62f6a3fb232ec', 14): True,  # one-statement-at-a-time, tied correctly
    ('6a1c834ae50cf1d3c6a7b706', 10): True,
    ('69ec7a8369d0eaa4a16a121c', 14): True,
    ('59ae8d282a78fd00010b80e7', 15): True,
    ('69f29515d1fe3f9e5661426b', 11): False,  # ERROR: full-option verdict taken from a message
    # that answered DIFFERENT statements (assistant answered the car_racing_03 statements while
    # on task 11); the stepwise dialogue on the real statements never concluded.
    ('666344916bdba2e2c980dcd0', 14): True,
    ('69f9f0668bf5734f80f13a7c', 7): True,
    ('5a86e1a4eea3d300016e7981', 8): True,
    # -- reflection-task --
    ('576fc3462984e70001a97fc3', 28): True,
    ('5d888c72662f2c0017f6339a', 22): True,  # C revised to B after timetable check
    ('6165467eb6321c819c2edb0a', 16): True,
    ('66def1304e37adb3349f648f', 20): True,
    ('6a024f725261d2958f108b09', 26): True,
    ('68a5eefd236f1c08d08ffce6', 16): True,
    ('6601b76d13817c7dc3117d2a', 18): True,
    ('6a0588c47fa42e9df12e0ea9', 10): True,
    # -- alternatives (both columns parsed and agreeing) --
    ('697a53e8b315729705307e4b', 6): True,
    ('697cbad7849402bb0a689ecc', 8): True,
    ('5f392fae9168cc472f0468f6', 14): True,
    ('6a034d39ee8639d4c7a0cdd8', 17): True,
    ('68123a73ba06c472ccd5edb8', 11): True,
    ('5dcdbf658d32d102ba69e839', 6): True,
    ('69f4a61347ac4d6e32a619d1', 6): True,   # columns initially disagreed, both converged to D
    ('69fb5b3f4a9a2b584b72f80f', 9): True,
}

NO_PARSE_REASONS = {
    # The 15 sampled unparsed trials; classification from reading the transcripts.
    ('677302ad15f7e3d0c1725fef', 6): 'stepwise dialogue never concluded '
                                     '(pause-points Steps; stances hedged/outside rules)',
    ('6a0afb57417835eaa8cf978e', 9): 'no verdict: user only asked side questions, '
                                     'never elicited a stance on the statements',
    ('6a1e0745ad50e296a4ffec34', 13): 'stepwise dialogue never concluded (pause-points Steps)',
    ('6a16ec054f5cdd315b2611c6', 16): 'alternatives: columns disagreed (A vs D; undefined by design)',
    ('67e8289e4c317bd8072e7c96', 13): 'hedged/conditional final stance '
                                      '("depends on interpretation: per day correct, total incorrect")',
    ('6a1e0745ad50e296a4ffec34', 8): 'stepwise dialogue never concluded (pause-points Step 1 only)',
    ('6a0588c47fa42e9df12e0ea9', 16): 'ambiguous meta-conversation: assistant answered '
                                      '"can these be added as rules", not statement truth',
    ('69ed80361ac67e060ad6e85e', 6): 'verdict present but too terse for rules '
                                     '(both columns converged on one-word "Neither")',
    ('6a0b2e634890878fbf46baad', 11): 'verdict present but format missed by rules '
                                      '(bullet lines "- 1: false"; one column parsed, one not)',
    ('66b90adf88e86b0a5e479b30', 6): 'alternatives: columns disagreed (D vs A; undefined by design)',
    ('6a1ca50dc52e2130653c1d5d', 11): 'stepwise dialogue never concluded (pause-points Steps)',
    ('5f4d4f3a2059689f1a2c33db', 7): 'verdict wording outside rules ("statement 1 does not hold" '
                                     'without "is"; statement 2 left implicit)',
    ('69f478835e7f45a7c46f4def', 15): 'stepwise dialogue never concluded (pause-points Step 1 only)',
    ('6a04b80e14874cdbefac323f', 12): 'alternatives: columns disagreed (B vs D; undefined by design)',
    ('63e8a4efd541d6d1d3f2bb89', 6): 'no verdict: user asked a sub-question only '
                                     '(who is available Thursday morning)',
}


def validation_samples(trials):
    rng = random.Random(VALIDATION_SEED)
    parsed = [t for t in trials if t['verdict'] is not None]
    sample = []
    for cond in COND_ORDER:
        pool = [t for t in parsed if t['condition'] == cond]
        # over-sample risky modes (combined / bare-tied contributions) where available
        risky = [t for t in pool if t['mode'] == 'combined']
        easy = [t for t in pool if t['mode'] != 'combined']
        k = 8
        kr = min(len(risky), 3)
        sample += rng.sample(risky, kr) + rng.sample(easy, k - kr)
    unparsed = [t for t in trials if t['verdict'] is None and t['n_assistant_msgs'] > 0]
    un_sample = rng.sample(unparsed, 15)
    return sample, un_sample


def dump_validation(trials):
    sample, un_sample = validation_samples(trials)
    print(f"===== {len(sample)} PARSED trials for hand-check =====")
    for t in sample:
        print("=" * 100)
        print(f"({t['pid']!r}, {t['task_id']}) cond={t['condition']} q={t['question']} "
              f"mode={t['mode']} PARSED_VERDICT={t['verdict']} "
              f"participant={t['answer']} correct={t['correct_option']}")
        for role, col, c in t['exchanges']:
            tag = f"{role}" + (f"/{col}" if col else "")
            print(f"--[{tag}]-- {c[:1500]}")
    print(f"\n===== {len(un_sample)} UNPARSED trials for classification =====")
    for t in un_sample:
        print("=" * 100)
        print(f"({t['pid']!r}, {t['task_id']}) cond={t['condition']} q={t['question']} "
              f"mode={t['mode']}")
        for role, col, c in t['exchanges']:
            tag = f"{role}" + (f"/{col}" if col else "")
            print(f"--[{tag}]-- {c[:1200]}")


# ----------------------------------------------------------------------- report
def write_report(trials):
    sample, un_sample = validation_samples(trials)
    # precision from recorded hand-check
    judged = [(t, HAND_CHECK.get((t['pid'], t['task_id']))) for t in sample]
    n_judged = sum(1 for _, j in judged if j is not None)
    n_ok = sum(1 for _, j in judged if j is True)
    precision = n_ok / n_judged if n_judged else float('nan')

    lines = []
    w = lines.append
    w("# Parsed AI verdicts and behavioral reliance measures")
    w("")
    w("Generated by `verdict_parse.py` from the raw chat logs in "
      "`data_analysis/raw_data/data/final_data/*.json`, joined with the analyzed sample "
      "(`notebook_analysis_output/participant_metrics.csv`, `exclude_primary == False`, "
      "N = 917) and per-trial answers (`task_metrics.csv`).")
    w("")
    w("## 1. Task-index mapping validation")
    w("")
    w("Before parsing, the mapping from chat-message task indices to problems was validated "
      "empirically: for **all** 925 participants x 12 problems (11,100 pairs), the answer "
      "stored in the raw JSON (`tasks[tid].responses[tid.1].answer`) was compared with "
      "`task_metrics.csv` (`participant_id`, `task_id`) rows. Result: **11,100/11,100 answers "
      "identical, 0 task-name mismatches** (standard conditions: task ids 6-17; "
      "reflection-task: even ids 6-28). Assistant messages carry the same index in "
      "`survey_index`; user messages in `task`.")
    w("")
    w("## 2. Parsing rules (summary)")
    w("")
    w("All 12 problems share the same four options (A = only statement 1, B = only "
      "statement 2, C = both, D = neither). Per assistant message the parser extracts:")
    w("")
    w("- **Full-option verdicts**: verbatim option text and paraphrases (\"only the first "
      "statement is correct\", \"both statements are false\", \"neither statement is "
      "correct\", \"the correct statement is 2\", \"my best guess is statement 1\").")
    w("- **Per-statement truth values**: \"statement 1 is false\", \"the second sentence is "
      "not\", \"Statement 2: incorrect\", line-start \"1. False -- ...\", and block headings "
      "(\"Statement 1\" / \"1.\") followed within 4 lines by a standalone \"True.\"/\"False.\".")
    w("- **Bare-polarity replies** (\"**True.**\") are tied to a statement only when the "
      "immediately preceding user message verbatim-contains exactly one of the two known "
      "statement texts (from `src/customizations/tasks/*.md`; texts verified identical "
      "across condition files).")
    w("")
    w("Messages are folded chronologically; the latest claim per statement wins, so "
      "revisions override earlier verdicts and one-statement-at-a-time conversations "
      "(common under pause-points) combine across messages. A trial is a **confident "
      "parse** only when both statements end with a known truth value, i.e. exactly one "
      "option is implied. Messages implying more than one option contribute nothing.")
    w("")
    w("**Alternatives condition**: the assistant sent two replies per prompt (columns a/b) "
      "that can disagree *by design*. Each column is folded separately; a verdict exists "
      "only when both columns parse **and agree**. Parse-but-disagree is recorded as "
      "undefined (by design) and reported separately.")
    w("")
    w("## 3. Coverage by condition")
    w("")
    w("| condition | participants | trials | confident verdicts | coverage |")
    w("|---|---|---|---|---|")
    stats = {c: condition_stats(trials, c) for c in COND_ORDER}
    for c in COND_ORDER:
        s = stats[c]
        w(f"| {c} | {s['n_participants']} | {s['n_trials']} | {s['n_parsed']} "
          f"| {100 * s['coverage']:.1f}% |")
    alt = stats['alternatives']
    w("")
    w(f"Alternatives detail: of {alt['n_trials']} trials, "
      f"{alt['modes'].get('agree', 0)} had both columns parsed and agreeing (the verdicts "
      f"used), {alt['modes'].get('disagree', 0)} had both columns parsed but disagreeing "
      f"(undefined by design), {alt['modes'].get('one-column', 0)} had only one parseable "
      f"column (treated as no verdict), {alt['modes'].get('none', 0)} had none.")
    w("")
    w("Pause-points coverage is low for a substantive reason: the intervention makes the "
      "assistant answer stepwise (\"Step 1 ... Which part should I check next?\"), and many "
      "conversations end before the assistant ever commits to a final verdict on both "
      "statements.")
    w("")
    w("## 4. Validation gate (hand-check)")
    w("")
    w(f"A seeded, condition-stratified sample of {len(sample)} confidently parsed trials "
      f"(8 per condition, over-sampling the riskier cross-message 'combined' mode) was "
      f"printed with full transcripts (`--validation-dump`) and each parse was checked by "
      f"reading the assistant's messages. Result: **{n_ok}/{n_judged} correct "
      f"({100 * precision:.1f}% precision)**.")
    w("")
    err = [t for t, j in judged if j is False]
    for t in err:
        w(f"- Error found: ({t['pid']}, task {t['task_id']}, {t['condition']}): the parser "
          f"took a full-option verdict from a message in which the assistant answered "
          f"*different* statements than the ones this problem asks about (the user had pasted "
          f"only the scenario, and the assistant answered a neighboring problem's statements); "
          f"the stepwise dialogue on the actual statements never concluded.")
    w("")
    w(f"Additionally, {len(un_sample)} unparsed trials were sampled and classified:")
    reason_counts = Counter(v.split(' (')[0].split(':')[0] for v in NO_PARSE_REASONS.values())
    for r, n in reason_counts.most_common():
        w(f"- {r}: {n}")
    w("")
    w("### Example transcripts (final assistant message, verbatim, truncated)")
    w("")
    for t in sample[:3]:
        last_assist = next((c for role, _c2, c in reversed(t['exchanges'])
                            if role == 'assistant'), '')
        w(f"**({t['condition']}, {t['question']})** parsed verdict **{t['verdict']}**, "
          f"participant answered {t['answer']} "
          f"({'followed' if t['answer'] == t['verdict'] else 'overrode'}):")
        w("")
        w("> " + last_assist[:400].replace("\n", " ").strip())
        w("")
    w("## 5. Reliance measures by condition (analyzed sample, confident parses only)")
    w("")
    w("| condition | coverage | agreement | override | follow-success | override-success "
      "| mean per-participant agreement |")
    w("|---|---|---|---|---|---|---|")
    for c in COND_ORDER:
        s = stats[c]
        def p(x):
            return f"{100 * x:.1f}%" if x is not None else "--"
        w(f"| {c} | {p(s['coverage'])} | {p(s['agree_rate'])} ({s['n_follow']}/{s['n_parsed']}) "
          f"| {p(s['override_rate'])} ({s['n_override']}/{s['n_parsed']}) "
          f"| {p(s['follow_success'])} | {p(s['override_success'])} "
          f"| {p(s['mean_pp_agreement'])} (n={s['n_pp_with_parse']}) |")
    w("")
    w("agreement = participant's submitted answer == parsed AI verdict; follow-success = "
      "P(correct | followed); override-success = P(correct | overrode).")
    w("")
    w("## 6. In-study AI advice accuracy by condition (parsed trials)")
    w("")
    w("| condition | AI verdict accuracy | follow-success (sanity check) |")
    w("|---|---|---|")
    for c in COND_ORDER:
        s = stats[c]
        acc = f"{100 * s['ai_accuracy']:.1f}%" if s['ai_accuracy'] is not None else "--"
        fs = f"{100 * s['follow_success']:.1f}%" if s['follow_success'] is not None else "--"
        w(f"| {c} | {acc} | {fs} |")
    w("")
    w("Sanity check: follow-success tracks the AI's own parsed-verdict accuracy closely in "
      "every condition, as it must when participants adopt the parsed recommendation.")
    w("")
    w("## 7. Limitations (what this parse cannot see)")
    w("")
    w("These are regex-parsed verdicts from free-text chat, not logged recommendations. "
      "(1) Coverage is selective: trials parse only when the assistant committed to an "
      "explicit stance on both statements, so unparsed trials -- especially the ~"
      f"{100 * (1 - stats['pause-points']['coverage']):.0f}% of pause-points trials where "
      "the stepwise dialogue never concluded -- are systematically different from parsed "
      "ones, and between-condition comparisons of agreement rates are conditioned on "
      "different (self-selected) subsets of trials. (2) The parse takes the assistant's "
      "latest decisive statement as its final verdict; it can be wrong when the assistant "
      "revised itself in wording the rules do not recognize, or when a decisive-sounding "
      "message actually addressed different statements than the problem asks about (the one "
      "hand-check error was of this second kind; overall hand-check error estimate: "
      f"{100 * (1 - precision):.1f}%). (3) When users pasted statements one at a time in a "
      "different order or paraphrased them, per-statement claims may occasionally be tied "
      "to the wrong statement; the verbatim-containment requirement mitigates but cannot "
      "eliminate this. (4) 'Agreement' here is behavioral co-occurrence, not causal "
      "reliance: a participant may have reached the same answer independently. (5) In the "
      "alternatives condition a single verdict is undefined by design whenever the two "
      "replies disagree; results there describe only the minority of trials where both "
      "replies agreed and are not comparable to the other conditions.")
    w("")
    out = os.path.join(HERE, 'VERDICT_PARSE.md')
    with open(out, 'w') as fh:
        fh.write("\n".join(lines))
    print(f"wrote {out}")
    # console summary
    for c in COND_ORDER:
        s = stats[c]
        print(f"{c}: coverage={100*s['coverage']:.1f}% agree={s['agree_rate'] and round(100*s['agree_rate'],1)}% "
              f"override-succ={s['override_success'] and round(100*s['override_success'],1)}% "
              f"follow-succ={s['follow_success'] and round(100*s['follow_success'],1)}% "
              f"AI-acc={s['ai_accuracy'] and round(100*s['ai_accuracy'],1)}%")
    print(f"hand-check precision: {n_ok}/{n_judged} = {100*precision:.1f}%")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--validation-dump', action='store_true',
                    help='print the seeded hand-check samples with transcripts')
    args = ap.parse_args()
    trials = run_parse()
    if args.validation_dump:
        dump_validation(trials)
    else:
        write_report(trials)


if __name__ == '__main__':
    main()
