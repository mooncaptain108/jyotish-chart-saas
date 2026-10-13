"""FastAPI application entry point for the Vedic Jyotish Chart API."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from routers import chart, geocode, muhurta
from activity import ActivityLogger

app = FastAPI(
    title="Vedic Jyotish Chart API",
    description="Vedic astrology (Jyotish) birth chart calculation engine using Swiss Ephemeris.",
    version="1.0.0",
)

app.add_middleware(ActivityLogger)

# Include routers
app.include_router(chart.router)
app.include_router(geocode.router)
app.include_router(muhurta.router)

# Serve static frontend files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", include_in_schema=False)
def root():
    # no-cache = "revalidate every load" (not "never store"): without it,
    # browsers may heuristically reuse a stale index.html after a deploy and
    # run old code against new data. Revalidation is cheap -- the ETag turns
    # an unchanged page into a 304.
    return FileResponse("static/index.html", headers={"Cache-Control": "no-cache"})

@app.get("/health", tags=["system"])
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
