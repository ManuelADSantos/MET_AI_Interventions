#!/usr/bin/env python3
"""Flatten final_data/*.json into one CSV per condition (one row per participant)."""
import csv, glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FD = os.path.join(HERE, 'data', 'final_data')
sys.path.insert(0, os.path.join(HERE, '..', '..', 'src', 'customizations', 'questions'))
from correct_answers import CORRECT_ANSWERS, ANSWER_OPTIONS, TEXT_TO_LETTER  # noqa: E402

QUIZ = list(CORRECT_ANSWERS.keys())
OPTIONS = ANSWER_OPTIONS
OPT_LETTER = TEXT_TO_LETTER

# Task IDs per layout (see dashboard.html TASK_MAP)
STD = {'quiz': list(range(6, 18)), 'post': 19, 'tlx': 20, 'postq': 21, 'ueq': 22, 'sus': 23, 'nfc': 24, 'trust': 25}
REFL = {'quiz': list(range(6, 29, 2)), 'post': 31, 'tlx': 32, 'postq': 33, 'ueq': 34, 'sus': 35, 'nfc': 36, 'trust': 37}

def row(p):
    L = REFL if p['condition'] == 'reflection-task' else STD
    tasks = p['tasks']
    get = lambda t, i: tasks.get(str(t), {}).get('responses', {}).get(f'{t}.{i}', {}).get('answer')
    num = lambda t, i: (lambda v: float(v) if v is not None and str(v).strip() != '' else None)(get(t, i))
    mean = lambda vals: round(sum(vals) / len(vals), 2) if vals else ''

    r = {'participantId': p['participantId'], 'condition': p['condition'],
         'savedAt': p['savedAt'], 'completed': p['completed'],
         'age': get(1, 1), 'gender': get(1, 2), 'profession': get(1, 3),
         'fluency': get(1, 4), 'education': get(1, 5), 'ai_use': get(1, 6)}

    confs_correct, confs_wrong = [], []
    n_correct = 0
    for name, tid in zip(QUIZ, L['quiz']):
        ans, conf = get(tid, 1), num(tid, 2)
        ok = bool(p['answerResults'][f'{tid}.1'])
        n_correct += ok
        (confs_correct if ok else confs_wrong).append(conf) if conf is not None else None
        r[f'{name}_answer'] = OPT_LETTER.get(ans, '')
        r[f'{name}_correct'] = int(ok)
        r[f'{name}_confidence'] = conf if conf is not None else ''

    assert n_correct == p['correctAnswers'], p['participantId']  # app's own tally must agree
    r['n_correct'] = n_correct
    all_confs = confs_correct + confs_wrong
    r['mean_confidence'] = mean(all_confs)
    r['metacog_sensitivity'] = (round(sum(confs_correct)/len(confs_correct) - sum(confs_wrong)/len(confs_wrong), 2)
                                if confs_correct and confs_wrong else '')

    # Each scale: raw items (unreversed, as answered) followed by its aggregate
    def items(scale, n):
        vals = []
        for i in range(1, n + 1):
            v = num(L[scale], i)
            r[f'{scale}_{i}'] = v if v is not None else ''
            vals.append(v)
        return vals

    # SUS: items 1-7,9-11 (8 = attention check); alternate v-1 / 5-v by position, sum * 2.5
    sus = [v for i, v in enumerate(items('sus', 11), 1) if i != 8]
    r['sus_aggregate'] = ('' if any(v is None for v in sus)
                          else round(sum(v - 1 if i % 2 == 0 else 5 - v for i, v in enumerate(sus)) * 2.5, 1))
    ueq = items('ueq', 8)
    r['ueq_aggregate'] = mean([v - 4 for v in ueq if v is not None])
    tlx = items('tlx', 6)
    r['tlx_aggregate'] = mean([v for v in tlx if v is not None])
    nfc = items('nfc', 6)
    r['nfc_aggregate'] = mean([(6 - v if i in (3, 4) else v) for i, v in enumerate(nfc, 1) if v is not None])
    trust = items('trust', 8)
    r['trust_aggregate'] = mean([(6 - v if i == 6 else v) for i, v in enumerate(trust, 1) if v is not None])

    r['attn_instruction'] = int(get(0, 2) == 'C')
    r['attn_post'] = int(str(get(L['post'], 3)) == '5')
    r['attn_sus'] = int(num(L['sus'], 8) == 5)
    r['msgs_to_ai'] = sum(1 for m in p['messages'] if m and m.get('role') == 'user')

    for k, t, i in [('pre_with_ai', 4, 1), ('pre_without_ai', 4, 2), ('pre_ai_alone', 4, 3),
                    ('post_with_ai', L['post'], 1), ('post_without_ai', L['post'], 2), ('post_ai_alone', L['post'], 4)]:
        v = get(t, i)
        r[k] = v if v is not None else ''

    # Post-questionnaire block (open text + Likert; items differ per condition).
    # Column header = the full question text itself.
    postq = tasks.get(str(L['postq']), {}).get('responses', {})
    for key in sorted(postq, key=lambda k: int(k.split('.')[1])):
        i = key.split('.')[1]
        q = (postq[key].get('question') or '').strip() or f'postq_{i}'
        col = q if q not in r else f'{q} ({i})'  # guard against duplicate question text
        r[col] = postq[key].get('answer', '')
    return r

for f in sorted(glob.glob(f'{FD}/*.json')):
    stem = os.path.basename(f)[:-5]
    if stem == 'all_data':
        continue
    with open(f) as fh:
        parts = json.load(fh)['participants']
    rows = [row(p) for p in parts]
    fields = list(dict.fromkeys(k for r in rows for k in r))  # union, first-seen order
    out = f'{FD}/{stem}.csv'
    with open(out, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=fields, restval='')
        w.writeheader()
        w.writerows(rows)
    assert len(rows) == len(parts), stem  # every participant exported
    print(f'{stem}.csv: {len(rows)} rows, {len(fields)} columns')
