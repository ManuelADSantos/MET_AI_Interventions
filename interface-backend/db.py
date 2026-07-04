import os
import threading
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import Json
import redis as redis_lib

# Railway provides DATABASE_URL / REDIS_URL; defaults match docker-compose services
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://study:study@db:5432/study')
REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')

_POOL_MAX = int(os.environ.get('DB_POOL_MAX', '10'))
_pool = ThreadedConnectionPool(1, _POOL_MAX, DATABASE_URL)
# The pool raises when exhausted; the semaphore makes excess requests queue instead
_pool_gate = threading.BoundedSemaphore(_POOL_MAX)
_redis = redis_lib.Redis.from_url(REDIS_URL, socket_timeout=1, socket_connect_timeout=1)


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
    _cache_set(pid)


def has_participated(pid):
    if _cache_hit(pid):
        return True
    exists = bool(_run('SELECT 1 FROM participants WHERE participant_id = %s', (pid,), fetch=True))
    if exists:
        _cache_set(pid)
    return exists


def fetch_all():
    rows = _run('SELECT data, saved_at FROM participants ORDER BY saved_at', fetch=True)
    return [{**row[0], 'savedAt': row[1].isoformat()} for row in rows]


# ponytail: Redis is a read cache only — if it's down, everything falls through to Postgres
def _cache_set(pid):
    try:
        _redis.set(f'participated:{pid}', '1')
    except redis_lib.RedisError:
        pass


def _cache_hit(pid):
    try:
        return _redis.exists(f'participated:{pid}') == 1
    except redis_lib.RedisError:
        return False
