"""
Stress test: N concurrent simulated participants hitting the backend.
Stdlib only - runs from the host or inside the backend container.

    python3 tests/stress_test.py --users 100
    python3 tests/stress_test.py --users 50 --url https://your-backend.up.railway.app
    python3 tests/stress_test.py --users 5 --chat        # also hits /chat/stream (costs API tokens!)

Each virtual participant: check_participation -> save -> check_participation.
Test rows are left in the DB (prefixed __stress_); clean with:
    docker compose exec db psql -U study -c "DELETE FROM participants WHERE participant_id LIKE '__stress_%'"
"""

import argparse
import json
import statistics
import sys
import time
import urllib.request
import urllib.error
import uuid
from concurrent.futures import ThreadPoolExecutor

parser = argparse.ArgumentParser()
parser.add_argument("--users", type=int, default=100, help="number of concurrent participants")
parser.add_argument("--url", default="http://localhost:5001", help="backend base URL")
parser.add_argument("--chat", action="store_true", help="also stream one chat completion per user (costs API tokens)")
args = parser.parse_args()

TASKS = {
    "4": {"ts": 1700000010000, "displayIndex": 4, "responses": {
        "4.1": {"question": "q", "answer": "Federal pay is out of line."},
        "4.2": {"question": "q", "answer": 75}}}
}

results = []  # (endpoint, seconds, ok, error)


def post(path, data, stream=False):
    req = urllib.request.Request(
        f"{args.url}{path}",
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"})
    start = time.perf_counter()
    ok, error = True, None
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        if stream:
            while resp.read(8192):
                pass
        else:
            resp.read()
    except urllib.error.HTTPError as e:
        ok = 200 <= e.code < 400
        error = None if ok else f"HTTP {e.code}: {e.read()[:120].decode(errors='replace')}"
    except Exception as e:
        ok, error = False, repr(e)[:140]
    results.append((path, time.perf_counter() - start, ok, error))


def participant(i):
    pid = f"__stress_{uuid.uuid4().hex[:10]}__"
    post("/check_participation", {"id": pid})
    if args.chat:
        post("/chat/stream", {"messages": [{"role": "user", "content": "Say hi in one word."}]}, stream=True)
    post("/save", {"participantId": pid, "condition": "ai", "messages": [], "tasks": TASKS})
    post("/check_participation", {"id": pid})


print(f"Running {args.users} concurrent participants against {args.url} (chat={'on' if args.chat else 'off'})\n")
wall_start = time.perf_counter()
with ThreadPoolExecutor(max_workers=args.users) as pool:
    list(pool.map(participant, range(args.users)))
wall = time.perf_counter() - wall_start

failures = [r for r in results if not r[2]]
print(f"{'endpoint':<24}{'count':>6}{'p50 ms':>10}{'p95 ms':>10}{'max ms':>10}")
for endpoint in sorted({r[0] for r in results}):
    times = sorted(r[1] * 1000 for r in results if r[0] == endpoint)
    p95 = times[max(0, int(len(times) * 0.95) - 1)]
    print(f"{endpoint:<24}{len(times):>6}{statistics.median(times):>10.0f}{p95:>10.0f}{times[-1]:>10.0f}")

print(f"\nTotal: {len(results)} requests in {wall:.1f}s ({len(results)/wall:.1f} req/s), {len(failures)} failed")
for error in sorted({f"{r[0]} -> {r[3]}" for r in failures}):
    print(f"  {error}")
sys.exit(1 if failures else 0)
