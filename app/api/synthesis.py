"""
Cross-Paper Scientific Synthesis & Evidence Matrix API Routes
"""
from fastapi import APIRouter, HTTPException, Query, Response
from typing import List, Optional
from pydantic import BaseModel

from app.services.synthesis_service import synthesis_service

router = APIRouter(prefix="/api/synthesis", tags=["Synthesis"])

class CompareRequest(BaseModel):
    paper_ids: List[str]

class ExportMatrixRequest(BaseModel):
    format_type: str = "csv"  # csv or markdown
    collection_id: Optional[str] = None

@router.post("/compare")
def compare_papers_endpoint(req: CompareRequest):
    """Compare 2 to 10 papers systematically across structured dimensions."""
    try:
        return synthesis_service.compare_papers(req.paper_ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/matrix")
def get_evidence_matrix_endpoint(
    collection_id: Optional[str] = None,
    topic: Optional[str] = None
):
    """Get dynamic evidence matrix across literature collection."""
    try:
        return synthesis_service.build_evidence_matrix(collection_id=collection_id, topic=topic)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/patterns")
def get_corpus_patterns_endpoint():
    """Detect corpus-wide recurring methods, datasets, limitations, and citations."""
    try:
        return synthesis_service.detect_corpus_patterns()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/matrix/export")
def export_evidence_matrix_endpoint(
    format_type: str = Query("csv", pattern="^(csv|markdown)$"),
    collection_id: Optional[str] = None
):
    """Export evidence matrix as CSV file or Markdown text."""
    try:
        content = synthesis_service.export_matrix(format_type=format_type, collection_id=collection_id)
        if format_type == "csv":
            return Response(
                content=content,
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=evidence_matrix.csv"}
            )
        else:
            return Response(
                content=content,
                media_type="text/markdown",
                headers={"Content-Disposition": "attachment; filename=evidence_matrix.md"}
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
