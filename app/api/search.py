"""
Literature Search API Routes
"""
from fastapi import APIRouter, HTTPException
from app.models.schemas import SearchQuery
from app.services.literature_service import literature_service

router = APIRouter(prefix="/api/search", tags=["Search"])

@router.post("")
def search_literature(query: SearchQuery):
    """Search OpenAlex literature with filters and pagination."""
    try:
        results = literature_service.search_literature(query)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

