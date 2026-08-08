# Build context is the repo root (see docker-compose.yml / Railway service settings)
FROM python:3.11-slim

WORKDIR /app

COPY interface-backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY interface-backend/ .
COPY customizations/questions/correct_answers.py ./correct_answers.py

EXPOSE 5001

# Railway sets PORT; docker-compose overrides this with gunicorn --reload for hot-reload
CMD gunicorn --workers ${WEB_CONCURRENCY:-2} --threads ${WEB_THREADS:-64} --timeout ${WEB_TIMEOUT:-180} --bind 0.0.0.0:${PORT:-5001} app:app
