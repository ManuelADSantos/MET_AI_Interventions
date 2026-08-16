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

## Realistic end-to-end simulation (30 & 60 simultaneous participants)

Goal: simulate real participants — mint token → real `/chat/stream` (OpenAI) → checkpoint
saves → answer all 12 questions with a realistic accuracy spread → final save — then run the
analysis pipeline on the generated replies.

**Why this ran against the LOCAL stack, not production:** the per-IP limiter keys on the
client IP, and Railway's edge **overwrites** a client-sent `X-Real-Ip` with the true edge IP
(verified: 12 requests with unique spoofed IPs all bucketed under one real IP). So a faithful
"60 distinct participants" test is impossible from a single machine against production — you
only exercise your own IP's limiter. Locally there is no edge, so `X-Real-Ip` is honored and
each virtual participant gets its own IP bucket — exactly what 60 real users look like. The
local stack runs the **identical** `app.py`/`db.py` (gunicorn 2×64 threads; local DB pool 10
vs prod 20). Production infra concurrency was validated separately (30 live OpenAI streams).

Results (local, `scratchpad/sim.py`, distinct IP per participant, real OpenAI calls):

| Scenario | Final save 201 | Concurrent chat streams | Stream errors | Wall clock | Backend score range |
|---|---|---|---|---|---|
| 30 simultaneous | 30/30 | 100 | 0 | 6.5 s | 5–11 /12 |
| 60 simultaneous | 60/60 | 200 | 0 | 7.8 s | 1–11 /12 |

(alternatives participants issue 3 concurrent column streams per prompt, so 60 participants =
up to 180 in-flight streams; all completed, avg ~5.4 s per participant end-to-end.)

**Analysis pipeline check:** exported the 60 generated records, ran
`generate_question_analysis.py` in an isolated copy (so real pilot data in `results/real_*`
was untouched). It produced a valid report — 720 question-answers, 58.3% overall accuracy,
per-condition + per-question tables, and the HTML dashboard — confirming the saved data shape
is analysis-ready. Key structural requirements the frontend must keep sending: each main task
keyed by stable source index (6–17 standard, 6/8/…/28 reflection-task) with `title` starting
`"Scenario:"` and `responses["{tid}.1"].answer` holding the multiple-choice answer.

## AutoProctor production handoff (browser walkthrough)

Walked the real participant entry (`?PROLIFIC_PID=...&condition=alternatives`) in production:

1. Consent flow renders (study info → monitoring notice → agreement); PID copy box, both
   checkboxes gate the start button correctly.
2. "Agree & Start Study" → `POST /api/launch/consent` called the real AutoProctor API and
   returned a unique URL; browser redirected to autoproctor.co showing the **correct test**
   ("Solving organising and planning tasks with AI").
3. AutoProctor's own browser gate ("Cannot Load Test on This Browser — use Chrome") stopped
   the automated browser there — expected; real participants on Chrome proceed.
4. SyncPage server seam verified directly: `GET /api/launch/session/<pid>` returns the
   registered condition (`alternatives`) for a consented pid, 404 for unknown pids.

Not automatable: AutoProctor's Chrome + screen-share device checks and the in-iframe study
run. Verify once by hand in Chrome before launch (2 min): enter through the Prolific URL,
pass the device check, confirm the study loads and the first checkpoint save appears.

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
