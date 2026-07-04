import os
import threading
import psycopg2
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
    _run('''CREATE TABLE IF NOT EXISTS participants (
                participant_id TEXT PRIMARY KEY,
                condition TEXT,
                data JSONB NOT NULL,
                saved_at TIMESTAMPTZ NOT NULL DEFAULT now())''')


def save_participant(pid, condition, record):
    # ponytail: upsert so a retry after a network hiccup never loses a participant's data
    _run('''INSERT INTO participants (participant_id, condition, data)
            VALUES (%s, %s, %s)
            ON CONFLICT (participant_id)
            DO UPDATE SET data = EXCLUDED.data, condition = EXCLUDED.condition, saved_at = now()''',
         (pid, condition, Json(record)))


def has_participated(pid):
    return bool(_run('SELECT 1 FROM participants WHERE participant_id = %s', (pid,), fetch=True))


def fetch_all():
    rows = _run('SELECT data, saved_at FROM participants ORDER BY saved_at', fetch=True)
    return [{**row[0], 'savedAt': row[1].isoformat()} for row in rows]
