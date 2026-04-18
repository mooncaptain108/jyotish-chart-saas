"""Geocode API router — /api/v1/geocode and /api/v1/tz-offset endpoints."""

from fastapi import APIRouter, HTTPException, Query

from services.geocode_service import geocode_place, tz_offset_for_date

router = APIRouter(prefix="/api/v1", tags=["geocode"])


@router.get("/geocode")
def geocode(place: str = Query(..., description="Place name to geocode")):
    """Geocode a place name to latitude, longitude, and timezone."""
    result = geocode_place(place)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Place not found: {place}")
    return result


@router.get("/tz-offset")
def tz_offset(
    iana_tz: str = Query(..., description="IANA timezone name (e.g. America/Los_Angeles)"),
    date:    str = Query(..., description="ISO date string (e.g. 1948-07-02)"),
):
    """Return the historically correct UTC offset and DST status for an IANA timezone on a given date."""
    try:
        result = tz_offset_for_date(iana_tz, date)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"timezone": iana_tz, "date": date, **result}
