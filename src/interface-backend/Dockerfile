# Build context is the repo root (see docker-compose.yml / Railway service settings)
FROM python:3.11-slim

WORKDIR /app

COPY src/interface-backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/interface-backend/ .
COPY src/customizations/questions/correct_answers.py ./correct_answers.py

EXPOSE 5001

# Railway sets PORT; docker-compose overrides this with gunicorn --reload for hot-reload
# ponytail: --max-requests recycles workers to reclaim fragmented CPython memory (RSS climbs
# monotonically because pymalloc doesn't return partial arenas to the OS). Jitter staggers restarts.
CMD gunicorn --workers ${WEB_CONCURRENCY:-2} --threads ${WEB_THREADS:-64} --timeout ${WEB_TIMEOUT:-180} --max-requests 1000 --max-requests-jitter 200 --bind 0.0.0.0:${PORT:-5001} app:app
