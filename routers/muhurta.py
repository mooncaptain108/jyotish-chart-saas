"""Muhurta search API endpoints."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.muhurta_jobs import start_search, get_status, get_results, cancel_job

router = APIRouter(prefix="/api/v1/muhurta", tags=["muhurta"])


class MuhurtaSearchRequest(BaseModel):
    lat:         float
    lon:         float
    tz:          float
    tzName:      Optional[str] = None
    locName:     Optional[str] = None
    date:        str
    time:        str = "00:00"
    days:        int
    targetSigns: Optional[List[int]] = None
    targetSign:  Optional[int] = None   # backward compat — single sign
    cfg:         dict


@router.post("/search")
def muhurta_start(req: MuhurtaSearchRequest):
    """Start a background muhurta search. Returns job_id."""
    params = req.model_dump()
    # Normalize to targetSigns list
    if not params.get('targetSigns'):
        ts = params.get('targetSign')
        params['targetSigns'] = [int(ts)] if ts is not None else [3]
    params.pop('targetSign', None)
    job_id = start_search(params)
    return {"job_id": job_id}


@router.get("/status/{job_id}")
def muhurta_status(job_id: str):
    """Get search progress (no results payload)."""
    status = get_status(job_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return status


@router.get("/results/{job_id}")
def muhurta_get_results(job_id: str):
    """Get accumulated results list."""
    results = get_results(job_id)
    if results is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"results": results}


@router.delete("/search/{job_id}")
def muhurta_cancel(job_id: str):
    """Cancel a running search."""
    ok = cancel_job(job_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"cancelled": True}
