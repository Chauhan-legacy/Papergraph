"""
Research Intersections API Routes
"""
from fastapi import APIRouter, HTTPException
from app.services.intersection_service import intersection_service

router = APIRouter(prefix="/api/intersections", tags=["Intersections"])

@router.get("")
def get_candidate_intersections():
    """Retrieve evidence-backed candidate research intersections."""
    try:
        intersections = intersection_service.find_intersections()
        return {"total": len(intersections), "intersections": intersections}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

