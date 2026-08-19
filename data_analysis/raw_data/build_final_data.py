#!/usr/bin/env python3
"""Merge real_interventions + real_paul into final_data/ (all_data, per-condition, repeated.csv)."""
import csv, glob, json, os

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = sorted(glob.glob(f'{BASE}/data/real_interventions/*.json') + glob.glob(f'{BASE}/data/real_paul/*.json'))
OUT = f'{BASE}/data/final_data'
os.makedirs(OUT, exist_ok=True)

# Key order of the most recent format (batch2_mix3 = batch1 + 'completed')
KEY_ORDER = ['answerResults', 'completed', 'condition', 'correctAnswers', 'interactionLog',
             'messages', 'participantId', 'savedAt', 'sessionId', 'studyId', 'tasks', 'totalQuestions']

all_parts, seen = [], {}  # seen: pid -> [conditions]
for f in SRC:
    with open(f) as fh:
        for p in json.load(fh)['participants']:
            p.setdefault('completed', True)  # ponytail: per user, pre-'completed' files are all finished runs
            p = {k: p[k] for k in KEY_ORDER if k in p}  # normalize key order to newest format
            all_parts.append(p)
            seen.setdefault(p['participantId'], []).append(p['condition'])

with open(f'{OUT}/all_data.json', 'w') as fh:
    json.dump({'participants': all_parts}, fh, ensure_ascii=False)

conds = sorted({p['condition'] for p in all_parts})
for c in conds:
    fname = c.replace('-', '_').lower()
    with open(f'{OUT}/{fname}.json', 'w') as fh:
        json.dump({'participants': [p for p in all_parts if p['condition'] == c]}, fh, ensure_ascii=False)

repeated = {pid: cs for pid, cs in seen.items() if len(cs) > 1}
with open(f'{OUT}/repeated.csv', 'w', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['participant'] + conds)
    for pid in sorted(repeated):
        w.writerow([pid] + ['X' if c in repeated[pid] else '' for c in conds])

print(f'{len(SRC)} source files, {len(all_parts)} participants, {len(conds)} conditions: {conds}')
print(f'{len(repeated)} repeated participants')

# --- verification: written data must be byte-identical in content to sources ---
def canon(p):  # key-order-independent form
    return json.dumps(p, sort_keys=True, ensure_ascii=False)

src_parts = []
for f in SRC:
    with open(f) as fh:
        for p in json.load(fh)['participants']:
            p.setdefault('completed', True)
            src_parts.append(canon(p))

with open(f'{OUT}/all_data.json') as fh:
    out_parts = [canon(p) for p in json.load(fh)['participants']]
assert sorted(src_parts) == sorted(out_parts), 'all_data.json does not match sources'

cond_total = 0
for c in conds:
    with open(f"{OUT}/{c.replace('-', '_').lower()}.json") as fh:
        ps = json.load(fh)['participants']
    assert all(p['condition'] == c and 'completed' in p for p in ps), f'{c}: bad condition/completed'
    cond_total += len(ps)
assert cond_total == len(all_parts), 'per-condition files do not sum to total'
print('verification OK: all data intact')
