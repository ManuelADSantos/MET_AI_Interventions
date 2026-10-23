"""End-of-study save works for every condition and nothing is dropped.

For each of the 5 conditions: an unknown participant is not flagged as having participated, the save
returns 201 with the completion code, scoring matches the answer key (one deliberate wrong answer),
the participant is then flagged (duplicate-participation guard), a retry upserts, and the record read
back from Postgres equals what was sent. Run inside the backend container:

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
    # 12 scored tasks (sourceIndex 5-16) plus a trial page that must not score. Task 5 is answered
    # wrong and its confidence item avoids the word "confident", so only the title-based detection of
    # scored pages in evaluate_answers gives 11/12 — the legacy fallback would misalign the key.
    tasks = {"4": {"ts": 1700000000000, "displayIndex": 4, "title": "Trial: Future Days", "responses": {
        "4.1": {"question": "Please indicate your answer.", "answer": "Only statement 1 is correct."}}}}
    for i, right in enumerate(right_choices):
        tid = str(5 + i)
        wrong = i == 0
        tasks[tid] = {"ts": 1700000000000 + i, "displayIndex": int(tid), "title": f"Scenario: Test {i}", "responses": {
            f"{tid}.1": {"question": "Please indicate your answer.", "answer": "This is a wrong answer" if wrong else right},
            f"{tid}.2": {"question": "Confidence?" if wrong else "How confident are you that your answer is correct?",
                         "answer": 80}}}

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


def post(path, payload, condition):
    # One X-Real-Ip per condition: /save is rate-limited per IP (30 per 5 min) and a run makes 10 saves,
    # so without this a few back-to-back runs would start failing with 429
    ip = f"10.0.0.{CONDITIONS.index(condition) + 1}"
    req = urllib.request.Request(f"{BACKEND_URL}{path}", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json", "X-Real-Ip": ip})
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return resp.status, json.loads(resp.read().decode() or '{}')
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or '{}')


pids = []
for condition in CONDITIONS:
    pid = f"__savetest_{uuid.uuid4().hex[:8]}_{condition}__"
    pids.append(pid)
    payload = build_payload(pid, condition)
    print(f"\n{condition}:")

    status, body = post("/check_participation", {"id": pid}, condition)
    test("unknown participant not flagged", status == 200 and body.get("participated") is False, f"got {status} {body}")

    status, body = post("/save", payload, condition)
    test("save returns 201 with completion code", status == 201 and body.get("message") == "OK" and "prolificCode" in body,
         f"got {status} {body}")
    test("scored 11/12 against the answer key",
         body.get("correctAnswers") == len(right_choices) - 1 and body.get("totalQuestions") == len(right_choices),
         f"got {body.get('correctAnswers')}/{body.get('totalQuestions')}")

    status, body = post("/check_participation", {"id": pid}, condition)
    test("saved participant flagged", status == 200 and body.get("participated") is True, f"got {status} {body}")

    status, _ = post("/save", payload, condition)
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
