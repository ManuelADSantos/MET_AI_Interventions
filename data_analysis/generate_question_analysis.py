#!/usr/bin/env python3
"""Regenerate question_analysis.md and question_analysis.html from response JSONs.
Usage: python3 generate_question_analysis.py
"""
import json, collections, glob, os

DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(DIR, 'results')

QUIZ_QUESTIONS = [
    ('ypc_02','Neither of the two statements is correct.'),
    ('ypc_03','Only statement 2 is correct.'),
    ('ypc_05','Only statement 1 is correct.'),
    ('ypc_06','Only statement 1 is correct.'),
    ('car_racing_01','Neither of the two statements is correct.'),
    ('car_racing_02','Both statements are correct.'),
    ('car_racing_03','Only statement 2 is correct.'),
    ('car_racing_05','Only statement 1 is correct.'),
    ('graduation_party_01','Only statement 2 is correct.'),
    ('graduation_party_05','Only statement 1 is correct.'),
    ('graduation_party_06','Neither of the two statements is correct.'),
    ('graduation_party_07','Only statement 2 is correct.'),
]
# ponytail: task IDs differ per condition; reflection-task interleaves justify tasks
QUIZ_IDS_STANDARD = list(range(6, 18))
QUIZ_IDS_REFLECTION = list(range(6, 29, 2))
def quiz_ids_for(condition):
    return QUIZ_IDS_REFLECTION if condition == 'reflection-task' else QUIZ_IDS_STANDARD

OPTIONS = ['Both statements are correct.','Neither of the two statements is correct.','Only statement 1 is correct.','Only statement 2 is correct.']
OPT_LETTER = {o: chr(65+i) for i,o in enumerate(OPTIONS)}

# Load all participants
files = sorted(glob.glob(os.path.join(RESULTS, 'real_*', '*.json')))
participants = []
for fname in files:
    with open(fname) as f:
        data = json.load(f)
    for p in data.get('participants', [data] if 'tasks' in data else []):
        # ponytail: exports now include mid-study checkpoints (completed=false) from
        # crashed/abandoned sessions; only finished participants belong in the analysis.
        # Records without the flag predate checkpointing = completed.
        if p.get('completed', True):
            participants.append(p)

n_files = len(files)
n_participants = len(participants)
print(f"{n_files} files, {n_participants} participants")

# Discover all conditions
all_conds = sorted(set(p.get('condition','?') for p in participants if p.get('condition','?') != '?'))

# Build per-question data
chart_data = []
for qi, (name, correct_ans) in enumerate(QUIZ_QUESTIONS):
    data_all = []
    for p in participants:
        cond = p.get('condition','?')
        tids = quiz_ids_for(cond)
        if qi >= len(tids): continue
        tid = tids[qi]
        tasks = p.get('tasks',{})
        t = tasks.get(str(tid)) or tasks.get(tid)
        if not t: continue
        for k,v in (t.get('responses') or {}).items():
            if k.endswith('.1'):
                ans = v.get('answer') if isinstance(v,dict) else v
                data_all.append((cond, ans))
                break
    n = len(data_all)
    overall = collections.Counter(a for _,a in data_all)
    n_correct = sum(1 for _,a in data_all if a == correct_ans)
    # Per-condition stats
    by_cond = {}
    for c in all_conds:
        c_ans = [a for cc,a in data_all if cc==c]
        by_cond[c] = {
            'n': len(c_ans),
            'pct': round(100*sum(1 for a in c_ans if a==correct_ans)/len(c_ans),1) if c_ans else 0,
            'dist': {o: sum(1 for a in c_ans if a==o) for o in OPTIONS},
        }
    chart_data.append({
        'name': name, 'correct_ans': correct_ans, 'n': n, 'n_correct': n_correct,
        'dist': {o: overall.get(o,0) for o in OPTIONS},
        'by_cond': by_cond,
        # Keep ai/rel shortcuts for the HTML chart
        'ai_pct': by_cond.get('ai',{}).get('pct',0), 'rel_pct': by_cond.get('ai-reliability',{}).get('pct',0),
        'ai_n': by_cond.get('ai',{}).get('n',0), 'rel_n': by_cond.get('ai-reliability',{}).get('n',0),
        'ai_dist': by_cond.get('ai',{}).get('dist',{o:0 for o in OPTIONS}),
        'rel_dist': by_cond.get('ai-reliability',{}).get('dist',{o:0 for o in OPTIONS}),
    })

# Compute summary stats
q_stats = []
for cd in chart_data:
    most = max(cd['dist'].items(), key=lambda x: x[1])
    q_stats.append((cd['name'], cd['n'], cd['n_correct'], 100*cd['n_correct']/cd['n'],
        {c: cd['by_cond'].get(c,{}).get('pct',0) for c in all_conds},
        most[0], 100*most[1]/cd['n'], most[0]==cd['correct_ans']))

overall_n = sum(s[1] for s in q_stats)
overall_c = sum(s[2] for s in q_stats)

# Per-condition totals
cond_totals = {}
for c in all_conds:
    cn = sum(cd['by_cond'].get(c,{}).get('n',0) for cd in chart_data)
    cc = sum(cd['by_cond'].get(c,{}).get('pct',0)*cd['by_cond'].get(c,{}).get('n',0)/100 for cd in chart_data)
    cond_totals[c] = (cn, cc)

easy = sorted([s for s in q_stats if s[3] >= 50], key=lambda x:-x[3])
hard = sorted([s for s in q_stats if s[3] < 25], key=lambda x:x[3])
wrong_dominant = [s for s in q_stats if not s[7]]
topics = [('ypc', [s for s in q_stats if s[0].startswith('ypc')]),
          ('car_racing', [s for s in q_stats if s[0].startswith('car')]),
          ('graduation_party', [s for s in q_stats if s[0].startswith('grad')])]
topic_pcts = {t: 100*sum(s[2] for s in qs)/sum(s[1] for s in qs) for t,qs in topics}

cond_summary = ', '.join(f'**{c}: {100*cond_totals[c][1]/cond_totals[c][0]:.0f}%** (n={cond_totals[c][0]//12})'
    for c in all_conds if cond_totals[c][0] > 0)
observations = [
    f'**Overall accuracy: {100*overall_c/overall_n:.1f}%** across {overall_n} question-answers from {n_participants} participants.',
    f'By condition: {cond_summary}.',
    f'**{len(easy)} questions above 50%**: {", ".join(s[0] for s in easy)}.' if easy else 'No questions above 50%.',
    f'**{len(hard)} questions below 25%** (at or below chance): {", ".join(s[0] for s in hard)}.' if hard else 'No questions below 25%.',
    f'**{len(wrong_dominant)} questions where the most popular answer is wrong**: {", ".join(s[0] for s in wrong_dominant)}.',
    'Random-chance baseline (4 options): 25%.',
    f'**graduation_party** is the easiest topic ({topic_pcts["graduation_party"]:.1f}%), **ypc** the hardest ({topic_pcts["ypc"]:.1f}%).',
]

# ── Write Markdown ──
lines = ['# Question-level answer analysis', '',
    f'Data: {n_files} response files, {n_participants} participants total.', '',
    '**Answer options** (same for all questions):', '',
    '| Key | Answer |', '|-----|--------|']
for o in OPTIONS:
    lines.append(f'| **{OPT_LETTER[o]}** | {o} |')
lines += ['', '---', '']

for cd in chart_data:
    name, correct_ans, n, n_correct = cd['name'], cd['correct_ans'], cd['n'], cd['n_correct']
    lines += [f'## {name}', '', f'Correct answer: **{OPT_LETTER[correct_ans]}) {correct_ans}**  ',
        f'Overall accuracy: **{n_correct}/{n} ({100*n_correct/n:.1f}%)**', '', f'### Overall (n={n})', '',
        '| Answer | Count | % |', '|--------|------:|---:|']
    for o in OPTIONS:
        c = cd['dist'].get(o, 0)
        mark = ' **correct**' if o == correct_ans else ''
        lines.append(f'| {OPT_LETTER[o]}) {o} | {c} | {100*c/n:.1f}%{mark} |')
    lines += ['', '### By condition', '']
    hdr = '| Answer |' + '|'.join(f' {c} (n={cd["by_cond"].get(c,{}).get("n",0)}) ' for c in all_conds) + '|'
    sep = '|--------|' + '|'.join('---:' for _ in all_conds) + '|'
    lines += [hdr, sep]
    for o in OPTIONS:
        cells = []
        for c in all_conds:
            bc = cd['by_cond'].get(c, {})
            tot = bc.get('n', 0)
            cnt = bc.get('dist', {}).get(o, 0)
            cells.append(f' {cnt} ({100*cnt/tot:.0f}%) ' if tot else ' – ')
        mark = ' **correct**' if o == correct_ans else ''
        lines.append(f'| {OPT_LETTER[o]}) {o}{mark} |{"|".join(cells)}|')
    lines += ['', '---', '']

cond_hdrs = ' | '.join(c for c in all_conds)
cond_seps = ' | '.join('---:' for _ in all_conds)
lines += ['## Summary analysis', '', '### Accuracy ranking', '',
    f'| Rank | Question | Correct | % | {cond_hdrs} | Dominant answer is correct? |',
    f'|-----:|----------|--------:|---:| {cond_seps} |---|']
for rank, s in enumerate(sorted(q_stats, key=lambda x: -x[3]), 1):
    nm, n, nc, pct, cpcts, _, _, cim = s
    cond_vals = ' | '.join(f'{cpcts.get(c,0):.0f}%' for c in all_conds)
    lines.append(f'| {rank} | {nm} | {nc}/{n} | {pct:.1f}% | {cond_vals} | {"Yes" if cim else "No"} |')
overall_cond_vals = ' | '.join(f'**{100*cond_totals[c][1]/cond_totals[c][0]:.0f}%**' if cond_totals[c][0] else '–' for c in all_conds)
lines.append(f'| | **Overall** | **{overall_c}/{overall_n}** | **{100*overall_c/overall_n:.1f}%** | {overall_cond_vals} | |')
lines += ['', '### Accuracy by topic', '', '| Topic | Questions | Mean accuracy |', '|-------|----------:|---------:|']
for tname, qs in topics:
    tc = sum(s[2] for s in qs); tn = sum(s[1] for s in qs)
    lines.append(f'| {tname} | {len(qs)} | {100*tc/tn:.1f}% |')
lines += ['', '### Key observations', ''] + [f'- {o}' for o in observations] + ['']

DASHBOARDS = os.path.join(DIR, 'exploration_dashboards')
with open(os.path.join(DASHBOARDS, 'question_analysis.md'), 'w') as f:
    f.write('\n'.join(lines))
print(f"Wrote question_analysis.md ({len(lines)} lines)")

# ── Write HTML ──
import re
def bold_to_strong(s):
    return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
obs_html = '\n'.join(f'    <li>{bold_to_strong(o)}</li>' for o in observations)
cond_counts = {c: cond_totals[c][0]//12 for c in all_conds if cond_totals[c][0] > 0}
subtitle_parts = ' · '.join(f'{c} (n={n})' for c,n in cond_counts.items())
cond_options_html = '\n'.join(f'      <option value="{c}">{c} only</option>' for c in all_conds)

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Question-level Answer Analysis</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.5.0/dist/chart.umd.js"></script>
<style>
* {{ box-sizing: border-box; margin: 0; }}
body {{ font-family: -apple-system, "Segoe UI", Roboto, sans-serif; background:#f6f7f9; color:#1a202c; padding:20px; font-size:14px; max-width:1200px; margin:0 auto; }}
h1 {{ font-size:20px; margin-bottom:4px; }} h2 {{ font-size:15px; margin-bottom:10px; color:#2d3748; }}
.sub {{ color:#718096; font-size:12px; margin-bottom:16px; }}
.card {{ background:#fff; border:1px solid #e2e8f0; border-radius:10px; padding:16px; margin-bottom:14px; }}
.grid {{ display:grid; gap:14px; grid-template-columns:1fr 1fr; }}
@media (max-width:900px) {{ .grid {{ grid-template-columns:1fr; }} }}
.chartbox {{ position:relative; height:320px; }}
.tall {{ height:700px; }}
select {{ font-size:13px; padding:4px 8px; border-radius:6px; border:1px solid #cbd5e0; margin-bottom:12px; }}
</style>
</head>
<body>

<h1>Question-level Answer Analysis</h1>
<div class="sub">{n_files} response files · {n_participants} participants · 12 questions · {subtitle_parts}</div>

<div class="card">
  <h2>Accuracy by question (% correct, sorted)</h2>
  <div class="chartbox tall"><canvas id="c_accuracy"></canvas></div>
</div>

<div class="grid">
  <div class="card">
    <h2>Accuracy by condition</h2>
    <div class="chartbox tall"><canvas id="c_condition"></canvas></div>
  </div>
  <div class="card">
    <h2>Accuracy by topic</h2>
    <div class="chartbox"><canvas id="c_topic"></canvas></div>
  </div>
</div>

<div class="card">
  <h2>Answer distribution per question</h2>
  <div>
    <select id="qPicker" onchange="renderDist()"></select>
    <select id="condPicker" onchange="renderDist()">
      <option value="all">All participants</option>
{cond_options_html}
    </select>
  </div>
  <div class="chartbox"><canvas id="c_dist"></canvas></div>
</div>

<div class="card">
  <h2>Key observations</h2>
  <ul style="margin:0;padding-left:20px;line-height:1.8;color:#2d3748">
{obs_html}
  </ul>
</div>

<script>
const D = {json.dumps(chart_data)};

const OPTIONS = ['Both statements are correct.','Neither of the two statements is correct.','Only statement 1 is correct.','Only statement 2 is correct.'];
const OPT_SHORT = ['Both correct','Neither correct','Only stmt 1','Only stmt 2'];
const OPT_COLORS = ['#ed8936','#4c8bf5','#48bb78','#9f7aea'];
const grid = '#eef1f5', noAR = {{ responsive:true, maintainAspectRatio:false }};
const padH = {{ layout:{{ padding:{{ right:36 }} }} }};

Chart.defaults.font.size = 11; Chart.defaults.color = '#4a5568';
const barLabels = {{ id:'barLabels', afterDatasetsDraw(chart) {{
  const ctx = chart.ctx; ctx.save(); ctx.font = '10px sans-serif'; ctx.fillStyle = '#4a5568';
  chart.data.datasets.forEach((ds, di) => {{
    chart.getDatasetMeta(di).data.forEach((bar, i) => {{
      const v = ds.data[i]; if (v == null) return;
      if (chart.options.indexAxis === 'y') {{
        ctx.textBaseline = 'middle'; ctx.textAlign = v < 0 ? 'right' : 'left';
        ctx.fillText(v + '%', bar.x + (v < 0 ? -4 : 4), bar.y);
      }} else {{ ctx.textAlign = 'center'; ctx.textBaseline = 'bottom'; ctx.fillText(v + '%', bar.x, bar.y - 4); }}
    }});
  }}); ctx.restore();
}}}};

const sorted = [...D].sort((a,b) => b.n_correct/b.n - a.n_correct/a.n);
const chanceLine = {{ id:'chanceLine', afterDraw(ch) {{
  const x = ch.scales.x.getPixelForValue(25);
  const ctx = ch.ctx; ctx.save(); ctx.setLineDash([5,3]); ctx.strokeStyle='#e53e3e'; ctx.lineWidth=1;
  ctx.beginPath(); ctx.moveTo(x, ch.chartArea.top); ctx.lineTo(x, ch.chartArea.bottom); ctx.stroke();
  ctx.fillStyle='#e53e3e'; ctx.font='9px sans-serif'; ctx.textAlign='left';
  ctx.fillText('chance (25%)', x+3, ch.chartArea.top-4); ctx.restore();
}}}};
new Chart(document.getElementById('c_accuracy'), {{ type:'bar', plugins:[barLabels, chanceLine],
  data:{{ labels:sorted.map(q=>q.name), datasets:[{{ data:sorted.map(q=>+(100*q.n_correct/q.n).toFixed(1)),
    backgroundColor:sorted.map(q=>100*q.n_correct/q.n >= 50 ? '#48bb78' : 100*q.n_correct/q.n < 25 ? '#fc8181' : '#ecc94b'),
    borderRadius:4 }}]}},
  options:{{ ...noAR, ...padH, indexAxis:'y', plugins:{{ legend:{{display:false}} }},
    scales:{{ x:{{ min:0, max:100, grid:{{color:grid}}, title:{{display:true,text:'% correct'}} }}, y:{{ grid:{{display:false}} }} }}}}}});

const CONDS = {json.dumps(all_conds)};
const COND_COLORS = ['#4c8bf5','#ed8936','#48bb78','#9f7aea','#fc8181','#38b2ac'];
const byName = [...D].sort((a,b) => b.n_correct/b.n - a.n_correct/a.n);
new Chart(document.getElementById('c_condition'), {{ type:'bar', plugins:[barLabels],
  data:{{ labels:byName.map(q=>q.name), datasets:CONDS.map((c,ci) => ({{
    label:c, data:byName.map(q=>(q.by_cond[c]||{{}}).pct||0),
    backgroundColor:COND_COLORS[ci % COND_COLORS.length], borderRadius:4
  }})) }},
  options:{{ ...noAR, indexAxis:'y', plugins:{{ legend:{{position:'bottom'}} }},
    scales:{{ x:{{ min:0, max:100, grid:{{color:grid}} }}, y:{{ grid:{{display:false}} }} }}}}}});

const topicData = [
  {{name:'ypc', qs:D.filter(q=>q.name.startsWith('ypc'))}},
  {{name:'car_racing', qs:D.filter(q=>q.name.startsWith('car'))}},
  {{name:'graduation_party', qs:D.filter(q=>q.name.startsWith('grad'))}}];
new Chart(document.getElementById('c_topic'), {{ type:'bar', plugins:[barLabels],
  data:{{ labels:topicData.map(t=>t.name), datasets:[{{ data:topicData.map(t => {{
    const c = t.qs.reduce((s,q)=>s+q.n_correct,0), n = t.qs.reduce((s,q)=>s+q.n,0);
    return +(100*c/n).toFixed(1);
  }}), backgroundColor:['#4c8bf5','#ed8936','#48bb78'], borderRadius:4 }}]}},
  options:{{ ...noAR, layout:{{padding:{{top:14}}}}, plugins:{{ legend:{{display:false}} }},
    scales:{{ y:{{ min:0, max:100, grid:{{color:grid}}, title:{{display:true,text:'% correct'}} }}, x:{{ grid:{{display:false}} }} }}}}}});

const picker = document.getElementById('qPicker');
picker.innerHTML = D.map((q,i) => `<option value="${{i}}">${{q.name}}</option>`).join('');
let distChart = null;
function renderDist() {{
  if (distChart) distChart.destroy();
  const q = D[+picker.value];
  const cond = document.getElementById('condPicker').value;
  const dist = cond === 'all' ? q.dist : (q.by_cond[cond]||{{}}).dist || {{}};
  const total = Object.values(dist).reduce((a,b)=>a+b,0);
  const colors = OPTIONS.map(o => o === q.correct_ans ? '#48bb78' : '#fc8181');
  distChart = new Chart(document.getElementById('c_dist'), {{ type:'bar',
    data:{{ labels:OPT_SHORT, datasets:[{{ data:OPTIONS.map(o => +(100*(dist[o]||0)/total).toFixed(1)),
      backgroundColor:colors, borderRadius:4 }}]}},
    options:{{ ...noAR, layout:{{padding:{{top:14}}}}, plugins:{{ legend:{{display:false}},
      tooltip:{{ callbacks:{{ afterLabel:c => OPTIONS[c.dataIndex] === q.correct_ans ? '← correct answer' : '',
        label:c => `${{c.raw}}% (${{dist[OPTIONS[c.dataIndex]]||0}} participants)` }}}}}},
      scales:{{ y:{{ min:0, max:100, grid:{{color:grid}}, title:{{display:true,text:'% of participants'}} }}, x:{{ grid:{{display:false}} }} }}}}}});
}}
renderDist();
</script>
</body>
</html>'''

with open(os.path.join(DASHBOARDS, 'question_analysis.html'), 'w') as f:
    f.write(html)
print("Wrote question_analysis.html")
