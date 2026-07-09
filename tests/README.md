# Tests

All stdlib-only, no installs needed. Start the stack first: `docker compose up`.

```bash
# Endpoint tests (save, auth, token minting, rate/size limits) - cleans up after itself
docker compose exec backend python /tests/test_endpoints.py

# Task parser randomization tests
docker compose exec frontend node /tests/test_taskparser.mjs

# Stress test: 100 concurrent participants (runs from host, stdlib only)
python3 tests/stress_test.py --users 100

# Stress test against Railway
python3 tests/stress_test.py --users 100 --url https://your-backend.up.railway.app

# Include LLM streaming in the stress test (costs API tokens)
python3 tests/stress_test.py --users 5 --chat
```

Stress rows are prefixed `__stress_`; clean them with:

```bash
docker compose exec db psql -U study -c "DELETE FROM participants WHERE participant_id LIKE '__stress_%'"
```
