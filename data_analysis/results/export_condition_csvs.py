#!/usr/bin/env python3
"""Flatten final_data/*.json into one CSV per condition (one row per participant)."""
import csv, glob, json, os

FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'final_data')

QUIZ = [('ypc_02', 'Only statement 1 is correct.'), ('ypc_03', 'Only statement 2 is correct.'),
        ('ypc_05', 'Both statements are correct.'), ('ypc_06', 'Only statement 2 is correct.'),
        ('car_racing_01', 'Only statement 1 is correct.'), ('car_racing_02', 'Only statement 2 is correct.'),
        ('car_racing_03', 'Both statements are correct.'), ('car_racing_05', 'Only statement 1 is correct.'),
        ('graduation_party_01', 'Neither of the two statements is correct.'),
        ('graduation_party_05', 'Only statement 1 is correct.'),
        ('graduation_party_06', 'Both statements are correct.'), ('graduation_party_07', 'Only statement 2 is correct.')]
OPTIONS = ['Both statements are correct.', 'Neither of the two statements is correct.',
           'Only statement 1 is correct.', 'Only statement 2 is correct.']
OPT_LETTER = {o: chr(65 + i) for i, o in enumerate(OPTIONS)}

# Task IDs per layout (see dashboard.html TASK_MAP)
STD = {'quiz': list(range(6, 18)), 'post': 19, 'tlx': 20, 'ueq': 22, 'sus': 23, 'nfc': 24, 'trust': 25}
REFL = {'quiz': list(range(6, 29, 2)), 'post': 31, 'tlx': 32, 'ueq': 34, 'sus': 35, 'nfc': 36, 'trust': 37}

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
    for (name, correct_ans), tid in zip(QUIZ, L['quiz']):
        ans, conf = get(tid, 1), num(tid, 2)
        ok = ans == correct_ans
        n_correct += ok
        (confs_correct if ok else confs_wrong).append(conf) if conf is not None else None
        r[f'{name}_answer'] = OPT_LETTER.get(ans, '')
        r[f'{name}_correct'] = int(ok)
        r[f'{name}_confidence'] = conf if conf is not None else ''

    r['n_correct'] = n_correct
    all_confs = confs_correct + confs_wrong
    r['mean_confidence'] = mean(all_confs)
    r['metacog_sensitivity'] = (round(sum(confs_correct)/len(confs_correct) - sum(confs_wrong)/len(confs_wrong), 2)
                                if confs_correct and confs_wrong else '')

    # SUS: items 1-7,9-11 (8 = attention check); alternate v-1 / 5-v by position, sum * 2.5
    sus_vals = [num(L['sus'], i) for i in [1, 2, 3, 4, 5, 6, 7, 9, 10, 11]]
    r['sus'] = ('' if any(v is None for v in sus_vals)
                else round(sum(v - 1 if i % 2 == 0 else 5 - v for i, v in enumerate(sus_vals)) * 2.5, 1))
    r['ueq_mean'] = mean([v - 4 for i in range(1, 9) if (v := num(L['ueq'], i)) is not None])
    r['tlx_mean'] = mean([v for i in range(1, 7) if (v := num(L['tlx'], i)) is not None])
    r['nfc_mean'] = mean([(6 - v if i in (3, 4) else v) for i in range(1, 7) if (v := num(L['nfc'], i)) is not None])
    r['trust_mean'] = mean([(6 - v if i == 6 else v) for i in range(1, 9) if (v := num(L['trust'], i)) is not None])

    r['attn_instruction'] = int(get(0, 2) == 'C')
    r['attn_post'] = int(str(get(L['post'], 3)) == '5')
    r['attn_sus'] = int(num(L['sus'], 8) == 5)
    r['msgs_to_ai'] = sum(1 for m in p['messages'] if m and m.get('role') == 'user')

    for k, t, i in [('pre_with_ai', 4, 1), ('pre_without_ai', 4, 2), ('pre_ai_alone', 4, 3),
                    ('post_with_ai', L['post'], 1), ('post_without_ai', L['post'], 2), ('post_ai_alone', L['post'], 4)]:
        v = get(t, i)
        r[k] = v if v is not None else ''
    return r

for f in sorted(glob.glob(f'{FD}/*.json')):
    stem = os.path.basename(f)[:-5]
    if stem == 'all_data':
        continue
    with open(f) as fh:
        parts = json.load(fh)['participants']
    rows = [row(p) for p in parts]
    out = f'{FD}/{stem}.csv'
    with open(out, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    assert len(rows) == len(parts), stem  # every participant exported
    print(f'{stem}.csv: {len(rows)} rows')
