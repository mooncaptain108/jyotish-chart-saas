"""Activity logging middleware — records access time, source IP, endpoint, and location to SQLite."""

import ipaddress
import json
import sqlite3
import threading
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

DB_PATH = Path(__file__).parent / "data" / "activity.db"

LOGGED_PREFIXES = (
    "/api/v1/chart",
)

_db_lock    = threading.Lock()
_cache_lock = threading.Lock()

# ip -> (expire_monotonic, location_string)
_ip_cache: dict[str, tuple[float, str]] = {}
_IP_CACHE_TTL = 86400   # 24 hours
_IP_CACHE_MAX = 500


def _init_db():
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS activity (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                ts        TEXT    NOT NULL,
                ip        TEXT    NOT NULL,
                method    TEXT    NOT NULL,
                path      TEXT    NOT NULL,
                location  TEXT
            )
        """)
        for col, typedef in [("location", "TEXT"), ("duration_s", "REAL")]:
            try:
                con.execute(f"ALTER TABLE activity ADD COLUMN {col} {typedef}")
            except sqlite3.OperationalError:
                pass  # column already exists
        con.commit()


_init_db()


def _get_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _is_private(ip: str) -> bool:
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        return False


def _lookup_location(ip: str) -> str:
    if _is_private(ip) or ip in ("unknown", ""):
        return "local"

    now = time.monotonic()
    with _cache_lock:
        entry = _ip_cache.get(ip)
        if entry and now < entry[0]:
            return entry[1]

    try:
        url = f"http://ip-api.com/json/{ip}?fields=status,city,regionName,country"
        with urllib.request.urlopen(url, timeout=3) as resp:
            data = json.loads(resp.read())
        if data.get("status") == "success":
            parts = [data.get("city"), data.get("regionName"), data.get("country")]
            location = ", ".join(p for p in parts if p)
        else:
            location = ip
    except Exception:
        location = ip

    with _cache_lock:
        if len(_ip_cache) >= _IP_CACHE_MAX:
            oldest = min(_ip_cache, key=lambda k: _ip_cache[k][0])
            del _ip_cache[oldest]
        _ip_cache[ip] = (now + _IP_CACHE_TTL, location)

    return location


def _log(ip: str, ts: str, method: str, path: str, duration_s: float):
    location = _lookup_location(ip)
    with _db_lock:
        with sqlite3.connect(DB_PATH) as con:
            con.execute(
                "INSERT INTO activity (ts, ip, method, path, location, duration_s) VALUES (?, ?, ?, ?, ?, ?)",
                (ts, ip, method, path, location, round(duration_s, 2)),
            )
            con.commit()


def log_request(request: Request, method: str, path: str, duration_s: float) -> None:
    ip = _get_ip(request)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    threading.Thread(target=_log, args=(ip, ts, method, path, duration_s), daemon=True).start()


class ActivityLogger(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        t0 = time.monotonic()
        response = await call_next(request)
        elapsed = time.monotonic() - t0
        path = request.url.path
        if request.method != "GET" and any(path.startswith(p) for p in LOGGED_PREFIXES):
            ip = _get_ip(request)
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            threading.Thread(target=_log, args=(ip, ts, request.method, path, elapsed), daemon=True).start()
        return response
