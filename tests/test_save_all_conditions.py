"""End-of-study save works for every condition and nothing is dropped.

Builds a realistic payload per condition (dual-column messages for alternatives,
.prediction responses for prediction, reflection answers, empty chat for no-ai),
saves it, retries the save, and round-trips the record from Postgres to prove the
stored data equals what was sent. Run inside the backend container:

    docker compose exec backend python /tests/test_save_all_conditions.py
"""

import json
import sys
import urllib.request
import urllib.error
import uuid

sys.path.insert(0, '/app')
import db                                   # noqa: E402
from correct_answers import right_choices   # noqa: E402

BACKEND_URL = "http://localhost:5001"

CONDITIONS = ['ai', 'ai-reliability', 'alternatives', 'pause-points', 'reflection-task']

passed = failed = 0


def test(name, ok, detail=""):
    global passed, failed
    passed, failed = passed + ok, failed + (not ok)
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f" ({detail})"))


def build_payload(pid, condition):
    # 12 scored tasks (sourceIndex 5-16), all answered correctly, plus a trial page that must not score
    tasks = {"4": {"ts": 1700000000000, "displayIndex": 4, "title": "Trial: Future Days", "responses": {
        "4.1": {"question": "Please indicate your answer.", "answer": "Only statement 1 is correct."}}}}
    for i, right in enumerate(right_choices):
        tid = str(5 + i)
        responses = {
            f"{tid}.1": {"question": "Please indicate your answer.", "answer": right},
            f"{tid}.2": {"question": "How confident are you that your answer is correct?", "answer": 80},
        }
        if condition == 'reflection-task':
            responses[f"{tid}.3"] = {"question": "Explain the AI's reasoning in your own words.",
                                     "answer": "It checked each constraint against the schedule."}
        tasks[tid] = {"ts": 1700000000000 + i, "displayIndex": int(tid),
                      "title": f"Scenario: Test {i}", "responses": responses}

    prompt = {"role": "user", "content": "Here is the task...", "ts": 1700000001000, "task": 5,
              "hasTaskQuestion": True}
    if condition == 'alternatives':
        messages = [prompt,
                    {"role": "assistant", "column": "a", "choices": [], "survey_index": 5},
                    {"role": "assistant", "column": "b", "choices": [], "survey_index": 5}]
    else:
        messages = [prompt, {"role": "assistant", "choices": [], "survey_index": 5}]

    log = [
        {"type": "intervention_gate_test", "taskId": 5, "timestamp": 1700000001000,
         "coverage": 0.9, "threshold": 0.6, "matched": True},
        {"type": "chat_reset", "taskId": 5, "timestamp": 1700000002000},
    ]

    return {"participantId": pid, "condition": condition, "messages": messages,
            "interactionLog": log, "tasks": tasks, "studyId": "study-x", "sessionId": "session-y"}


def post_save(payload):
    # Distinct X-Real-Ip per participant: the /save rate limit (10 per IP per 5 min) keys on it,
    # and this test alone makes 16 saves — real participants save once or twice each.
    fake_ip = f"10.0.0.{CONDITIONS.index(payload['condition']) + 1}"
    req = urllib.request.Request(f"{BACKEND_URL}/save", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json", "X-Real-Ip": fake_ip})
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or '{}')


pids = []
for condition in CONDITIONS:
    pid = f"__savetest_{uuid.uuid4().hex[:8]}_{condition}__"
    pids.append(pid)
    payload = build_payload(pid, condition)

    print(f"\n{condition}:")
    status, body = post_save(payload)
    test("save returns 201", status == 201, f"got {status} {body}")
    test("all 12 answers scored correct",
         body.get("correctAnswers") == len(right_choices) and body.get("totalQuestions") == len(right_choices),
         f"got {body.get('correctAnswers')}/{body.get('totalQuestions')}")

    status, _ = post_save(payload)
    test("retry save returns 201 (upsert)", status == 201, f"got {status}")

    rows = db._run("SELECT data FROM participants WHERE participant_id = %s", (pid,), fetch=True)
    record = rows[0][0] if rows else {}
    test("messages round-trip intact", record.get("messages") == payload["messages"])
    test("interactionLog round-trips intact", record.get("interactionLog") == payload["interactionLog"])
    test("tasks round-trip intact", record.get("tasks") == payload["tasks"])
    test("condition stored", record.get("condition") == condition, f"got {record.get('condition')}")

for pid in pids:
    db._run("DELETE FROM participants WHERE participant_id = %s", (pid,))

total = passed + failed
print(f"\n{'=' * 40}\nResults: {passed}/{total} passed" + (f", {failed} FAILED" if failed else " - all good!"))
sys.exit(1 if failed else 0)
