"""Activity logging middleware — records access time, source IP, and endpoint to SQLite."""

import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

DB_PATH = Path(__file__).parent / "data" / "activity.db"
_lock = threading.Lock()

LOGGED_PREFIXES = (
    "/api/v1/chart",
    "/api/v1/muhurta",
)


def _init_db():
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS activity (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                ts        TEXT    NOT NULL,
                ip        TEXT    NOT NULL,
                method    TEXT    NOT NULL,
                path      TEXT    NOT NULL
            )
        """)
        con.commit()


_init_db()


def _get_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


class ActivityLogger(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        if any(path.startswith(p) for p in LOGGED_PREFIXES):
            ip = _get_ip(request)
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            with _lock:
                with sqlite3.connect(DB_PATH) as con:
                    con.execute(
                        "INSERT INTO activity (ts, ip, method, path) VALUES (?, ?, ?, ?)",
                        (ts, ip, request.method, path),
                    )
                    con.commit()
        return response
