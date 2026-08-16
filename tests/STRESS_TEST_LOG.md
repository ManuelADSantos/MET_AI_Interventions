# Production stress test log — 2026-08-16

Target: `backend-production-b624.up.railway.app` (backend) + `aalto-engpsy-metai.up.railway.app` (frontend), Railway Pro, OpenAI Tier 3, gpt-5.4-mini.

Everything below ran against the **live production deployment**. All test rows used prefixes
`STRESS_TEST_` / `STRESS_V2_` / `STRESS_V3_` / `STRESSPID_` / `claudetestingclaude` and were
deleted afterwards (both `participants` and `sessions` tables verified at 0 rows).

## What was tested and results

### 1. Save path (`/save`)
- 10 concurrent saves: all 201 at ~150 ms.
- Malformed `tasks` payload (`{"1": "not_a_dict"}`): 201 — the `evaluate_answers` try/catch
  degrades to `correctAnswers: 0` instead of a 500. (Before the fix deploy: 500.)
- 20–30 concurrent saves from ONE IP: ~10 pass, rest 429 — see "rate limiter" below.

### 2. Checkpoint feature (mid-study saves, `completed` flag)
- Checkpoint save (`completed: false`) → `/check_participation` still `false` (no lockout on reload).
- Final save (no flag = completed) → `/check_participation` `true`.
- Late-arriving checkpoint after final save → 201 but **does not clobber** the final record
  (verified via `/export`: `completed: True`, final messages intact). Guard lives in
  `db.py save_participant` (conditional UPSERT `WHERE`).

### 3. Study entry URLs (all 3 conditions)
`?PROLIFIC_PID=...&condition=reflection_task|alternatives|pause_points`
- Auto-start works (no manual ID entry when PROLIFIC_PID present).
- `condition` URL param binds correctly, underscores → hyphens (`reflection-task`, `pause-points`).

### 4. Streaming load (`/chat/stream`, real OpenAI calls)
Per virtual participant: mint token (`/token`) → stream one chat response → checkpoint save.
- reflection-task, 10 concurrent participants × 1 stream: 10/10, TTFB ~2.2 s, 0 errors.
- pause-points, 10 concurrent × 1 stream: 10/10. Intervention visibly reshapes output
  ("**Step 1** … Which part should I look at next?") — conditions verified end-to-end.
- alternatives worst case, 10 participants × 3 columns = **30 concurrent streams**:
  30/30, TTFB 0.6–2.2 s, all complete ≤ 2.5 s, 0 errors.
  NOTE: mint ONE token per participant (the app shares it across columns). A first attempt
  minting per-column (30 concurrent `/token`) tripped the rate limiter — that load pattern
  does not exist in the real app.

## The "rate limiter" (read this before diagnosing 429s)

All 429s came from **our own backend**, `app.py _rate_limit()` — NOT Railway:
per **IP**, per endpoint prefix, sliding **5-minute** window:
`/chat` 30 · `/token` 10 · `/save` 10.

Consequences:
- Load tests from one machine hit these limits long before any real bottleneck.
  A "lockout" is just the window draining (up to 5 min). Don't diagnose launch problems by
  rapidly opening many study tabs from one machine.
- Real participants (distinct IPs) sit far under every limit: ~2 token mints,
  ~3 saves/window, a handful of chat calls per session.
- Known squeeze: two `alternatives` participants behind the same NAT share the `/chat` bucket
  (3 hits per prompt each). `/chat` was raised 30 → 90 after this test run to cover that case.

## Capacity conclusion

30 simultaneous participants is comfortable in every condition; ~50 is fine. The expensive
path (30 concurrent OpenAI streams) returns in ~2 s. Real ceilings, in order: gunicorn threads
(128; alternatives streams cost 3/participant), then DB pool. Bump `WEB_THREADS` env var
before code changes if 100+ simultaneous is ever needed.

## Reproducing

Single save:

```bash
curl -s -w "\n%{http_code}\n" -X POST https://backend-production-b624.up.railway.app/save \
  -H 'Content-Type: application/json' \
  -d '{"participantId":"STRESS_TEST_X","condition":"stress_test","tasks":{},"completed":false}'
```

Streaming as a participant (token, then stream; add `"column":"a|b|c"` for alternatives):

```bash
TOKEN=$(curl -s -X POST https://backend-production-b624.up.railway.app/token \
  -H 'Content-Type: application/json' \
  -d '{"id":"STRESS_TEST_X","condition":"alternatives"}' | python3 -c 'import json,sys;print(json.load(sys.stdin)["token"])')
curl -s -N -X POST https://backend-production-b624.up.railway.app/chat/stream \
  -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" \
  -d '{"messages":[{"role":"user","content":"one short sentence: 2+2?"}],"hasTaskQuestion":true,"column":"a"}'
```

Concurrency = wrap in `for i in $(seq 1 N); do ( ... ) & done; wait`. Keep N ≤ the per-IP
limits above or you are testing the limiter, not the system.

Cleanup (DB has no public endpoint by default — use Railway dashboard query tab, or
temporarily add a TCP proxy and remove it after):

```sql
DELETE FROM participants WHERE participant_id LIKE 'STRESS%' OR participant_id LIKE 'claudetesting%';
DELETE FROM sessions     WHERE participant_id LIKE 'STRESS%' OR participant_id LIKE 'claudetesting%';
```
