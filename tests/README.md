# Tests

Free (no API calls), stdlib only. Start the stack first: `docker compose up`.

```bash
# The 12 scenario pages (the stimulus) are byte-identical across all 5 conditions' task files
docker compose exec frontend node /tests/test_condition_files.mjs

# The alternatives / pause-points intervention engages only when a prompt carries the task question
docker compose exec frontend node /tests/test_intervention_gate.mjs

# Task-order randomization keeps every page's sourceIndex, which answers and scoring are keyed by
docker compose exec frontend node /tests/test_taskparser.mjs

# Save, scoring against the answer key, duplicate-participation guard and Postgres round trip,
# for all 5 conditions — cleans up after itself
docker compose exec backend python /tests/test_save_all_conditions.py
```
