import hashlib
import sqlite3
import threading
from pathlib import Path


CACHE_DB = Path(__file__).resolve().parent.parent / "ai_cache.db"

_local_locks = {}
_local_locks_guard = threading.Lock()


def _get_lock(key: str):
    with _local_locks_guard:
        if key not in _local_locks:
            _local_locks[key] = threading.Lock()
        return _local_locks[key]


def make_cache_key(task, prompt, system_instruction, model_strategy):
    raw = "\n".join([
        str(task.value if hasattr(task, "value") else task),
        str(model_strategy or ""),
        str(system_instruction or ""),
        prompt,
    ])

    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _connect():
    connection = sqlite3.connect(
        CACHE_DB,
        timeout=30,
    )

    connection.execute("""
        CREATE TABLE IF NOT EXISTS ai_cache (
            cache_key TEXT PRIMARY KEY,
            task TEXT NOT NULL,
            model_strategy TEXT,
            response TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    return connection


def get_cached(cache_key):
    try:
        connection = _connect()

        row = connection.execute(
            """
            SELECT response
            FROM ai_cache
            WHERE cache_key = ?
            """,
            (cache_key,),
        ).fetchone()

        connection.close()

        return row[0] if row else None

    except Exception:
        return None


def set_cached(cache_key, task, model_strategy, response):
    if not response:
        return

    try:
        connection = _connect()

        connection.execute(
            """
            INSERT OR REPLACE INTO ai_cache
            (
                cache_key,
                task,
                model_strategy,
                response
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                cache_key,
                task.value if hasattr(task, "value") else str(task),
                model_strategy,
                response,
            ),
        )

        connection.commit()
        connection.close()

    except Exception:
        # Cache failure must NEVER break AI generation.
        pass


def get_key_lock(cache_key):
    return _get_lock(cache_key)