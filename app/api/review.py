"""
Literature Review Studio API Routes
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from app.services.literature_review_service import literature_review_service

router = APIRouter(prefix="/api/review", tags=["Review"])

class ReviewRequest(BaseModel):
    topic: str = ""
    paper_ids: Optional[List[str]] = None

@router.post("/generate")
def generate_literature_review_endpoint(req: ReviewRequest):
    """Synthesize structured literature review outline and draft with citations."""
    try:
        return literature_review_service.generate_review(topic=req.topic, paper_ids=req.paper_ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/outline")
def get_review_outline_endpoint(req: ReviewRequest):
    """Synthesize structured literature review outline."""
    try:
        review = literature_review_service.generate_review(topic=req.topic, paper_ids=req.paper_ids)
        return {"outline": review.outline, "thematic_groups": review.thematic_groups}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/draft")
def get_review_draft_endpoint(req: ReviewRequest):
    """Synthesize full literature review draft with markdown and bibtex."""
    try:
        return literature_review_service.generate_review(topic=req.topic, paper_ids=req.paper_ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

