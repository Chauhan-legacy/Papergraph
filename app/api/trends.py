"""
Research Trend Analytics API Routes
"""
from fastapi import APIRouter, HTTPException
from app.services.trend_service import trend_service

router = APIRouter(prefix="/api/trends", tags=["Trends"])

@router.get("")
def get_trends():
    """Retrieve publication temporal distributions, topic and keyword trends."""
    try:
        return trend_service.compute_trends()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

