"""Does the pause-points system prompt change model accuracy when the participant only says NEXT?

Runs each task twice: once with the production pause-points prompt (participant pastes the
task, then answers every step question with "NEXT" until the model concludes) and once with
the plain assistant as baseline. Uses the real prompt + streaming path imported from /app.

    docker compose exec -T backend python /tests/pause_points_next_test.py \
        < src/customizations/tasks/pause_points_tasks.md

Full transcripts land in /tmp/pause_next_results.json inside the container:
    docker compose cp backend:/tmp/pause_next_results.json .
"""

import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, '/app')
from app import INTERVENTION_PROMPTS          # noqa: E402 — also pulls config + db, fine in-container
from chat_helpers import stream_completion    # noqa: E402
from correct_answers import right_choices     # noqa: E402

N_TASKS = 10       # "10 runs" — first 10 of the 12 main tasks, one run per condition each
MAX_TURNS = 12     # pause prompt allows up to 10 steps; small buffer
BASELINE_TURNS = 3

OPTIONS = [
    "Only statement 1 is correct.",
    "Only statement 2 is correct.",
    "Both statements are correct.",
    "Neither of the two statements is correct.",
]
OPTION_PATTERNS = [
    (re.compile(r"only statement 1 is correct", re.I), OPTIONS[0]),
    (re.compile(r"only statement 2 is correct", re.I), OPTIONS[1]),
    (re.compile(r"both statements are correct", re.I), OPTIONS[2]),
    (re.compile(r"neither (of the two )?statements? is correct", re.I), OPTIONS[3]),
]


def parse_tasks(md):
    """Yield (title, chat_message) per '# Scenario:' section, mimicking the task-to-chat draft."""
    tasks = []
    sections = re.split(r"^# ", md, flags=re.M)[1:]
    for sec in sections:
        title = sec.splitlines()[0].strip()
        if not title.startswith("Scenario:"):
            continue
        copies = re.findall(r"^:::copy\n(.*?)\n:::\s*$", sec, flags=re.S | re.M)
        if len(copies) < 2:
            continue
        exercise, scenario = copies[0].strip(), copies[1].strip()
        answer_block = "Please indicate your answer.\n" + "\n".join(
            f"{chr(65 + i)}. {o}" for i, o in enumerate(OPTIONS))
        tasks.append((title, f"{title}\n\nScenario:\n{scenario}\n\n"
                             f"Question and answer options:\n{exercise}\n\n{answer_block}"))
    return tasks


def complete(messages):
    """One full (non-streamed to us) completion; returns assistant text."""
    for attempt in (1, 2):
        try:
            content = ''
            for event in stream_completion(messages):
                if event['type'] == 'done':
                    content = event['response']['choices'][0]['message']['content']
            return content
        except Exception as e:
            if attempt == 2:
                raise
            print(f"  retrying after error: {e}", file=sys.stderr)


def extract_answer(text):
    last = None
    for pat, opt in OPTION_PATTERNS:
        for m in pat.finditer(text or ''):
            if last is None or m.start() > last[0]:
                last = (m.start(), opt)
    return last[1] if last else None


CONCLUSION = re.compile(r"\b(final answer|the answer is|correct (answer|option) is)\b", re.I)


def run_conversation(task_text, intervention, max_turns):
    """Paste the task, then say NEXT until the model commits to an option (or cap)."""
    history = [{'role': 'user', 'content': task_text}]
    replies = []
    for _ in range(max_turns):
        messages = history + ([{'role': 'system', 'content': intervention}] if intervention else [])
        reply = complete(messages)
        replies.append(reply)
        history += [{'role': 'assistant', 'content': reply}]
        if extract_answer(reply) and (CONCLUSION.search(reply) or any(o.lower() in reply.lower() for o in OPTIONS)):
            break
        history += [{'role': 'user', 'content': 'NEXT'}]
    # answer = last option mentioned, scanning back from the final reply
    answer = None
    for reply in reversed(replies):
        answer = extract_answer(reply)
        if answer:
            break
    return answer, len(replies), history


def run_one(i, title, task_text, expected):
    pause_prompt = INTERVENTION_PROMPTS['pause-points']
    p_answer, p_turns, p_hist = run_conversation(task_text, pause_prompt, MAX_TURNS)
    b_answer, b_turns, b_hist = run_conversation(task_text, None, BASELINE_TURNS)
    print(f"[{i + 1:2}] {title[:40]:<42} pause: {('?' if not p_answer else p_answer[:20]):<22}"
          f" ({p_turns:2} turns) {'OK ' if p_answer == expected else 'MISS'} |"
          f" base: {('?' if not b_answer else b_answer[:20]):<22} ({b_turns} turns)"
          f" {'OK' if b_answer == expected else 'MISS'}", flush=True)
    return {
        'task': title, 'expected': expected,
        'pause': {'answer': p_answer, 'turns': p_turns, 'correct': p_answer == expected,
                  'transcript': p_hist},
        'baseline': {'answer': b_answer, 'turns': b_turns, 'correct': b_answer == expected,
                     'transcript': b_hist},
    }


def main():
    tasks = parse_tasks(sys.stdin.read())
    assert len(tasks) == len(right_choices), f"parsed {len(tasks)} tasks, expected {len(right_choices)}"
    if os.environ.get('DRY'):
        print(f"parsed {len(tasks)} tasks; first message:\n\n{tasks[0][1]}")
        return
    runs = list(zip(range(N_TASKS), tasks[:N_TASKS], right_choices[:N_TASKS]))

    print(f"Running {len(runs)} tasks x 2 conditions (pause-points vs baseline), model from study.config.yml\n", flush=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda r: run_one(r[0], r[1][0], r[1][1], r[2]), runs))

    p_ok = sum(r['pause']['correct'] for r in results)
    b_ok = sum(r['baseline']['correct'] for r in results)
    p_turns = sum(r['pause']['turns'] for r in results) / len(results)
    print(f"\npause-points: {p_ok}/{len(results)} correct (avg {p_turns:.1f} steps)")
    print(f"baseline:     {b_ok}/{len(results)} correct")

    with open('/tmp/pause_next_results.json', 'w') as f:
        json.dump(results, f, indent=1)
    print("transcripts: /tmp/pause_next_results.json (docker compose cp backend:/tmp/pause_next_results.json .)")


if __name__ == '__main__':
    main()
