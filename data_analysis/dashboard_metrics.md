# Dashboard Upper-Bar Metrics (Pilot 2)

How each KPI card in `dashboard.html` is computed.

| Metric | Calculation |
|--------|-------------|
| **Correct** | Count of quiz answers (tasks 6–17) matching the correct answer in `QUIZ_KEY`. Shown as `n / 12`. |
| **Mean confidence** | Arithmetic mean of the 12 per-question confidence values (item 2 of each quiz task, 0–100%). |
| **Metacog. sensitivity** | `mean_confidence_on_correct − mean_confidence_on_incorrect`. Positive = participant was more confident when right. Needs ≥1 correct and ≥1 incorrect answer; otherwise `–`. |
| **SUS score** | Standard System Usability Scale formula on task 23, items 1–7 and 9–11 (item 8 is an attention check). Odd items: `value − 1`; even items: `5 − value`. Sum × 2.5 → 0–100. |
| **UEQ-S mean (−3…+3)** | Arithmetic mean of all 8 UEQ-S items (task 22, items 1–8). Each raw response is shifted by −4 to center on 0. Green if > 0.8, red if < −0.8 (standard UEQ benchmarks). |
| **TLX mean (0–20)** | Arithmetic mean of the 6 NASA-TLX subscales (task 20 items 1–6: Mental, Physical, Temporal, Performance, Effort, Frustration), each 0–20. |
| **NFC mean (1–5)** | Arithmetic mean of 6 Need-for-Cognition items (task 24). Items 3 & 4 are reverse-scored (`6 − value`); the rest taken as-is. Scale 1–5. |
| **Attention checks** | Three binary checks: (1) instruction check — task 0 item 2 equals `'C'`; (2) post-task attention — task 19 item 3 equals `'5'`; (3) SUS embedded check — task 23 item 8 equals `5`. Shown as `pass / 3`. |
| **Msgs to AI** | Count of messages with `role === 'user'` in the participant's message log. |
