"""
Endpoint test for /save, /check_participation and /export.
Run inside the backend container (cleans up after itself there):
    docker compose exec backend python /tests/test_endpoints.py
Or against any deployment (leaves one test row behind):
    python3 tests/test_endpoints.py https://your-backend.up.railway.app
"""

import sys
import json
import uuid
import urllib.request
import urllib.error

BACKEND_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5001"
PID = f"__test_{uuid.uuid4().hex[:12]}__"

PAYLOAD = {
    "participantId": PID,
    "condition": "ai",
    "messages": [
        {"role": "user", "content": "What is logical reasoning?"},
        {"role": "assistant", "content": "Logical reasoning is rational analysis of arguments."}
    ],
    "tasks": {
        "4": {"ts": 1700000010000, "displayIndex": 4, "responses": {
            "4.1": {"question": "Life imitates art...", "answer": "Soon after the advent of color television, white shirts became less popular as dressy attire for men, and pastel-colored shirts began to sell well."},
            "4.2": {"question": "Confidence?", "answer": 75}}},
        "5": {"ts": 1700000020000, "displayIndex": 5, "responses": {
            "5.1": {"question": "Federal workers...", "answer": "Federal pay is out of line."},
            "5.2": {"question": "Confidence?", "answer": 60}}},
        "6": {"ts": 1700000030000, "displayIndex": 6, "responses": {
            "6.1": {"question": "No high jumper...", "answer": "This is a wrong answer"},
            "6.2": {"question": "Confidence?", "answer": 30}}}
    }
}

passed = failed = 0


def post_json(path, data):
    req = urllib.request.Request(
        f"{BACKEND_URL}{path}",
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req)
        body = resp.read().decode()
        return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return e.code, json.loads(body) if body else {}
    except urllib.error.URLError as e:
        print(f"FATAL: cannot connect to {BACKEND_URL} - {e.reason}")
        sys.exit(1)


def test(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name}" + (f" ({detail})" if detail else ""))


print(f"Testing against: {BACKEND_URL}\n")

print("1. Unknown ID is not a participant...")
status, body = post_json("/check_participation", {"id": PID})
test("check_participation returns 200 + participated=false",
     status == 200 and body.get("participated") is False, f"got {status} {body}")

print("\n2. POST /save ...")
status, body = post_json("/save", PAYLOAD)
test("returns 201", status == 201, f"got {status}")
test("message is OK", body.get("message") == "OK", f"got {body.get('message')}")
test("has prolificCode", "prolificCode" in body)
test("correct answers == 2", body.get("correctAnswers") == 2, f"got {body.get('correctAnswers')}")
test("total questions == 20", body.get("totalQuestions") == 20, f"got {body.get('totalQuestions')}")

print("\n3. Saved ID is now a participant...")
status, body = post_json("/check_participation", {"id": PID})
test("check_participation returns 200 + participated=true",
     status == 200 and body.get("participated") is True, f"got {status} {body}")

print("\n4. Re-save is a safe upsert (retry scenario)...")
status, _ = post_json("/save", PAYLOAD)
test("second save returns 201", status == 201, f"got {status}")

print("\n5. Cleanup...")
try:
    sys.path.insert(0, "/app")
    import db
    db._run("DELETE FROM participants WHERE participant_id = %s", (PID,))
    print("  removed test row from Postgres")
except Exception:
    print(f"  skipped (not inside backend container) - stray row: {PID}")

total = passed + failed
print(f"\n{'='*40}\nResults: {passed}/{total} passed" + (f", {failed} FAILED" if failed else " - all good!"))
sys.exit(1 if failed else 0)
