"""
Advanced Research Engineering Tools API
Provides:
- Literature Copilot / Q&A (/api/tools/copilot)
- Benchmark Matrix (/api/tools/benchmarks)
- Contradiction & Gap Radar (/api/tools/gaps)
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from app.services.copilot_service import copilot_service
from app.services.benchmark_service import benchmark_service
from app.services.gap_service import gap_service

router = APIRouter(prefix="/api/tools", tags=["Research Tools"])

class CopilotQueryRequest(BaseModel):
    query: str
    top_k: int = 5

@router.post("/copilot")
def ask_literature_endpoint(req: CopilotQueryRequest):
    """Ask natural language research question across literature corpus."""
    try:
        return copilot_service.ask_literature(query=req.query, top_k=req.top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/benchmarks")
def get_benchmarks_endpoint():
    """Retrieve structured benchmark datasets and performance comparisons."""
    try:
        return benchmark_service.extract_benchmarks()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/gaps")
def get_gaps_endpoint():
    """Retrieve literature contradictions, limitations, and open frontiers."""
    try:
        return gap_service.detect_gaps_and_contradictions()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

