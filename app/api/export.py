"""
Research Export API Routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from app.services.export_service import export_service

router = APIRouter(prefix="/api/export", tags=["Export"])

class ExportRequest(BaseModel):
    format: str = "json"  # bibtex, json, csv, markdown
    paper_ids: Optional[List[str]] = None
    collection_id: Optional[str] = None

@router.post("")
def export_research(req: ExportRequest):
    """Export selected papers or collections into standard academic formats."""
    try:
        result = export_service.export(
            format_type=req.format,
            paper_ids=req.paper_ids,
            collection_id=req.collection_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

