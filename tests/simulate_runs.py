"""
Simulate N participant runs, populating Postgres and Redis with mock data.
Stdlib only — runs from host or inside the backend container.

    docker compose exec backend python /tests/simulate_runs.py
    docker compose exec backend python /tests/simulate_runs.py --runs 20 --condition no-ai

Clean up:
    docker compose exec db psql -U study -c "DELETE FROM participants WHERE participant_id LIKE '__sim_%'"
"""

import argparse
import json
import random
import sys
import urllib.request
import urllib.error

parser = argparse.ArgumentParser()
parser.add_argument("--runs", type=int, default=10)
parser.add_argument("--url", default="http://localhost:5001")
parser.add_argument("--condition", default="both", choices=["ai", "no-ai", "both"])
args = parser.parse_args()

AI_OPTIONS = [
    "Only statement 1 is correct.",
    "Only statement 2 is correct.",
    "Both statements are correct.",
    "Neither of the two statements is correct.",
]

# ponytail: no-ai answers from correct_answers.py, plus some wrong ones for realism
NO_AI_CORRECT = [
    "Soon after the advent of color television, white shirts became less popular as dressy attire for men, and pastel-colored shirts began to sell well.",
    "Federal pay is out of line.",
    "No high jumper entered the meet.",
    "Therefore, if the overweight men between 25 and 50 were to lose weight, their risk of heart disease would be reduced.",
    "Some brilliant mathematicians require calculators for simple multiplication facts.",
    "Women tend to conform to social expectations.",
    "the powerful can often avoid serious criminal sentences",
    "When the dog has fleas, he always scratches. But the dog doesn't have fleas, so he won't be scratching.",
    "sign ordinances are rarely, if ever effective",
    "happenstance will be more beneficial to those who are prepared",
    "not doing anything is not an act",
    "Jumbo shrimp may not actually be very big.",
    "the lie detector is sometimes worthless",
    "citing the number of cases in which the lie detector mistook falsehood for truth",
    "The very threat of a lie-detector test has led to a significant number of criminals to confess.",
    "Danish automobiles also leak oil.",
    "disapproving",
    "water conservation",
    "Ten years ago, most letters reached their destination within twenty-four hours.",
    "may or may not pass the course",
]
NO_AI_WRONG = ["Wrong answer A", "Wrong answer B", "Wrong answer C"]

CHAT_PAIRS = [
    ("Can you help me with this scheduling problem?", "Of course! Let me analyze the constraints."),
    ("What should I consider here?", "Look at the availability and preferences of each person."),
    ("Is statement 1 correct?", "Let me check the constraints — it depends on whether all capacity is used."),
    ("Which answer makes more sense?", "Based on the context, I'd suggest examining each option carefully."),
    ("I'm not sure about this one.", "Let's break it down step by step."),
]


def build_tasks(condition):
    tasks = {}
    base_ts = 1700000000000
    for i in range(4, 29):  # sourceIndex 4–28 covers 25 task pages
        answers = AI_OPTIONS if condition == "ai" else (NO_AI_CORRECT + NO_AI_WRONG)
        answer = random.choice(answers)
        confidence = random.randint(10, 100)
        tasks[str(i)] = {
            "ts": base_ts + i * 15000,
            "displayIndex": i,
            "responses": {
                f"{i}.1": {"question": f"Question {i}", "answer": answer},
                f"{i}.2": {"question": "How confident are you that your answer is correct?", "answer": confidence},
            },
        }
    return tasks


def build_messages(condition):
    if condition == "no-ai":
        return []
    n = random.randint(2, len(CHAT_PAIRS))
    pairs = random.sample(CHAT_PAIRS, n)
    msgs = []
    for user_msg, ai_msg in pairs:
        msgs.append({"role": "user", "content": user_msg})
        msgs.append({"role": "assistant", "content": ai_msg})
    return msgs


def post(url, data):
    req = urllib.request.Request(
        url, data=json.dumps(data).encode(), headers={"Content-Type": "application/json"}
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())
    except Exception as e:
        return 0, {"error": str(e)}


conditions = ["ai", "no-ai"] if args.condition == "both" else [args.condition]
ok = fail = 0

print(f"Simulating {args.runs} participants against {args.url}\n")

for i in range(args.runs):
    cond = conditions[i % len(conditions)]
    pid = f"__sim_{i:03d}_{cond}__"
    payload = {
        "participantId": pid,
        "condition": cond,
        "messages": build_messages(cond),
        "tasks": build_tasks(cond),
    }
    status, body = post(f"{args.url}/save", payload)
    if status == 201:
        ok += 1
        score = body.get("correctAnswers", "?")
        total = body.get("totalQuestions", "?")
        print(f"  {pid}  {cond:<5}  {score}/{total} correct")
    else:
        fail += 1
        print(f"  {pid}  FAILED ({status}): {body.get('error', body)}")

print(f"\nDone: {ok} saved, {fail} failed.")
if ok:
    print("View in Postgres:  docker compose exec db psql -U study -c \"SELECT participant_id, condition, data->'correctAnswers' AS score FROM participants WHERE participant_id LIKE '__sim_%'\"")
    print("View in Redis:     open http://localhost:8001 (RedisInsight)")
    print("Clean up:          docker compose exec db psql -U study -c \"DELETE FROM participants WHERE participant_id LIKE '__sim_%'\"")
sys.exit(1 if fail else 0)
