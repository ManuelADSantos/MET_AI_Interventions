# Dashboard Metrics (Pilots 1–3)

How each KPI card / chart in the participant dashboards is computed.

## Upper-bar KPI cards

| Metric | Calculation |
|--------|-------------|
| **Correct** | Count of quiz answers (tasks 6–17) matching `QUIZ_KEY`. Shown as `n / 12`. Pilot 1 uses offset detection (`T(id)` pattern). |
| **Mean confidence** | Arithmetic mean of 12 per-question confidence values (item 2 of each quiz task, 0–100%). |
| **Metacog. sensitivity** | `mean_conf_correct − mean_conf_incorrect`. Needs ≥1 of each; otherwise `–`. |
| **SUS score** | Standard SUS formula on task 23 (pilot 1: `T(24)`), items 1–7 and 9–11 (item 8 = attention check). Odd: `val − 1`; even: `5 − val`. Sum × 2.5 → 0–100. |
| **UEQ-S mean (−3…+3)** | Mean of 8 UEQ-S items (task 22 / `T(23)`), each shifted by −4. Green > 0.8, red < −0.8. |
| **TLX mean (0–20)** | Mean of 6 NASA-TLX subscales (task 20 / `T(21)`, items 1–6), each 0–20. |
| **NFC mean (1–5)** | Mean of 6 NFC items (task 24 / `T(25)`). Items 3 & 4 reverse-scored (`6 − val`). |
| **Attention checks** | Three binary checks: instruction (task 0 item 2 = `'C'`), post-task attention (task 19 item 3 = `'5'`), SUS embedded (task 23 item 8 = `5`). Shown as `pass / 3`. |
| **Msgs to AI** | Count of `role === 'user'` messages in participant's message log. |

## Charts

| Chart | What it shows |
|-------|---------------|
| **Confidence by question** | Bar chart of per-question confidence (0–100%). Correct answers colored blue, incorrect red. Sortable by name or presented order. |
| **Time per question** | Bar chart of per-question duration (seconds). Same color/sort logic as confidence. |
| **Trust (8 items)** | Radar chart of 8 trust items (task 25 / `T(25)`, items 1–8). Item 6 ("Wary") is reverse-scored. Scale 1–5. |
| **Problem-count estimates: pre vs post** | Grouped bar chart comparing pre-task and post-task estimates for 3 questions: "with AI", "without AI", "AI alone". Dashed green reference line at actual correct count (`nCorrect` from quiz). Pre-task from task 3 / `T(4)`, post-task from task 19 / `T(20)`. |

## Tables / cards

| Card | What it shows |
|------|---------------|
| **Answer table** | Per-question: name, presented order, answer text, confidence, correctness, duration. Sortable by name or presented order. |
| **Reliability intervention log** | Per-question for `ai-reliability` condition only: reliability level shown (High/Medium/Low from `reliability_card_presented` events), max similarity score and test count (from `reliability_similarity_test` events), correctness. Sortable. Hidden when participant has no interactionLog data. |

## Summary table

| Column | Calculation |
|--------|-------------|
| **PID** | Participant ID from `meta.pid`. | 1, 2, 3 |
| **Cond** | Condition from `meta.condition` (`ai` or `ai-reliability`). |
| **Correct** | `n / total` — same as upper-bar KPI. |
| **Conf** | Mean confidence (same as upper-bar). |
| **Sens** | Metacognitive sensitivity (same as upper-bar). |
| **SUS** | SUS score (same as upper-bar). |
| **UEQ** | UEQ-S mean (same as upper-bar). |
| **TLX** | TLX mean (same as upper-bar). |
| **NFC** | NFC mean (same as upper-bar). |
| **Trust** | Trust mean (mean of 8 trust items, item 6 reverse-scored). |
| **Msgs** | Messages to AI (same as upper-bar). |
| **Est w/ AI** | Pre→post estimate for "with AI" question (e.g. `4→7`). |
| **Est w/o AI** | Pre→post estimate for "without AI" question. |
| **Est AI alone** | Pre→post estimate for "AI alone" question. |
