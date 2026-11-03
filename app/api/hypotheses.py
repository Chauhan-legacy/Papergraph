"""
Research Question & Scientific Hypothesis Explorer API Routes
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from app.services.hypothesis_service import hypothesis_service

router = APIRouter(prefix="/api/hypotheses", tags=["Hypotheses"])

@router.get("")
def get_candidate_research_questions(limit: int = Query(10, ge=1, le=50)):
    """Synthesize candidate research questions and hypotheses across corpus."""
    try:
        return hypothesis_service.discover_candidate_questions(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
