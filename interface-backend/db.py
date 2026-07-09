import os
import secrets
import threading
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import Json

# Railway provides DATABASE_URL; default matches docker-compose
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://study:study@db:5432/study')

_POOL_MAX = int(os.environ.get('DB_POOL_MAX', '10'))
_pool = ThreadedConnectionPool(1, _POOL_MAX, DATABASE_URL)
# The pool raises when exhausted; the semaphore makes excess requests queue instead
_pool_gate = threading.BoundedSemaphore(_POOL_MAX)


def _run(query, params=(), fetch=False):
    with _pool_gate:
        conn = _pool.getconn()
        try:
            with conn, conn.cursor() as cur:
                cur.execute(query, params)
                return cur.fetchall() if fetch else None
        finally:
            _pool.putconn(conn)


def init():
    # ponytail: parallel gunicorn workers can race on Postgres type creation during first boot
    _run('''SELECT pg_advisory_xact_lock(2026070501);
            CREATE TABLE IF NOT EXISTS participants (
                participant_id TEXT PRIMARY KEY,
                condition TEXT,
                data JSONB NOT NULL,
                saved_at TIMESTAMPTZ NOT NULL DEFAULT now());
            CREATE TABLE IF NOT EXISTS sessions (
                participant_id TEXT PRIMARY KEY,
                condition TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now());
            ALTER TABLE sessions ADD COLUMN IF NOT EXISTS token TEXT;
            ALTER TABLE sessions ADD COLUMN IF NOT EXISTS chat_count INT NOT NULL DEFAULT 0''')


def save_participant(pid, condition, record):
    # ponytail: upsert so a retry after a network hiccup never loses a participant's data
    _run('''INSERT INTO participants (participant_id, condition, data)
            VALUES (%s, %s, %s)
            ON CONFLICT (participant_id)
            DO UPDATE SET data = EXCLUDED.data, condition = EXCLUDED.condition, saved_at = now()''',
         (pid, condition, Json(record)))


def has_participated(pid):
    return bool(_run('SELECT 1 FROM participants WHERE participant_id = %s', (pid,), fetch=True))


def create_session(pid, condition):
    _run('''INSERT INTO sessions (participant_id, condition)
            VALUES (%s, %s)
            ON CONFLICT (participant_id)
            DO UPDATE SET condition = EXCLUDED.condition''',
         (pid, condition))


# Hard per-participant ceiling on chat calls: bounds OpenAI spend even if a token leaks
CHAT_CAP = int(os.environ.get('CHAT_MESSAGE_CAP', '300'))


def issue_token(pid, condition):
    token = secrets.token_urlsafe(32)
    _run('''INSERT INTO sessions (participant_id, condition, token)
            VALUES (%s, %s, %s)
            ON CONFLICT (participant_id)
            DO UPDATE SET condition = EXCLUDED.condition, token = EXCLUDED.token''',
         (pid, condition, token))
    return token


def consume_chat(token):
    # ponytail: one atomic UPDATE is both the auth check and the spend counter
    return bool(_run('''UPDATE sessions SET chat_count = chat_count + 1
                        WHERE token = %s AND chat_count < %s RETURNING 1''',
                     (token, CHAT_CAP), fetch=True))


def get_session_condition(pid):
    rows = _run('SELECT condition FROM sessions WHERE participant_id = %s', (pid,), fetch=True)
    return rows[0][0] if rows else None


def fetch_all():
    rows = _run('SELECT data, saved_at FROM participants ORDER BY saved_at', fetch=True)
    return [{**row[0], 'savedAt': row[1].isoformat()} for row in rows]
