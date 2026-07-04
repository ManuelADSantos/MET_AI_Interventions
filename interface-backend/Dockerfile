# Build context is the repo root (see docker-compose.yml / Railway service settings)
FROM python:3.11-slim

WORKDIR /app

COPY interface-backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY interface-backend/ .
COPY customizations/correct_answers.py ./correct_answers.py

EXPOSE 5001

# Railway sets PORT; docker-compose overrides this with flask --debug for hot-reload
CMD gunicorn --workers ${WEB_CONCURRENCY:-2} --threads 8 --timeout 120 --bind 0.0.0.0:${PORT:-5001} app:app
