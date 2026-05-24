"""Geocode service — place name to lat/lng/timezone."""
from __future__ import annotations

from datetime import datetime

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

import pytz


_geolocator = Nominatim(user_agent="jyotish-chart-saas/1.0 (brook.paul@live.com)")
_tf = TimezoneFinder()


def tz_offset_for_date(iana_tz: str, date_str: str) -> dict:
    """Return the historically correct UTC offset and DST status for an IANA timezone on a given date.

    Uses noon on the given date to avoid DST transition ambiguity at midnight.

    Args:
        iana_tz:  IANA timezone string (e.g. "America/Los_Angeles").
        date_str: ISO date string (e.g. "1948-07-02").

    Returns:
        Dict with 'offset' (decimal hours) and 'dst' (bool, True if DST active).
    """
    tz = pytz.timezone(iana_tz)
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(hour=12)
    localized = tz.localize(dt)
    offset_hours = localized.utcoffset().total_seconds() / 3600
    dst_active = localized.dst().total_seconds() != 0
    return {"offset": offset_hours, "dst": dst_active}


def geocode_place(place: str) -> dict | None:
    """Geocode a place name to latitude, longitude, and timezone.

    Args:
        place: Place name string (e.g. "New Delhi, India").

    Returns:
        Dict with place, latitude, longitude, timezone, timezone_offset,
        or None if not found.
    """
    location = _geolocator.geocode(place)
    if location is None:
        return None

    lat = location.latitude
    lng = location.longitude

    tz_name = _tf.timezone_at(lat=lat, lng=lng)
    if tz_name is None:
        tz_name = "UTC"

    # Compute current UTC offset as a reference default (no birth date context here)
    tz = pytz.timezone(tz_name)
    now = datetime.now(tz)
    offset_hours = now.utcoffset().total_seconds() / 3600

    return {
        "place": location.address,
        "latitude": round(lat, 6),
        "longitude": round(lng, 6),
        "timezone": tz_name,
        "timezone_offset": offset_hours,
    }
