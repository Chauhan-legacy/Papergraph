"""
Paper Analyzer Execution and Control API Routes
"""
import threading
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List

from app.core.progress_manager import progress_manager
from app.services.analyzer_pipeline import analyzer_pipeline

router = APIRouter(prefix="/api/analyzer", tags=["Analyzer"])

class StartAnalysisRequest(BaseModel):
    paper_ids: Optional[List[str]] = None
    force_reanalyze: bool = False

@router.get("/progress")
def get_progress():
    """Retrieve active analyzer progress and current status."""
    return progress_manager.get_status()

@router.post("/paper/{paper_id}")
def analyze_single_paper_endpoint(paper_id: str, force: bool = True):
    """Analyze a single paper immediately on demand."""
    try:
        res = analyzer_pipeline.process_single_paper(paper_id, force=force)
        return {"status": "success", "paper": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start")
def start_analysis(req: StartAnalysisRequest, background_tasks: BackgroundTasks):
    """Start autonomous analyzer pipeline in background."""
    status = progress_manager.get_status()
    if status.active:
        return {"status": "already_running", "message": "Analyzer is currently running."}

    background_tasks.add_task(
        analyzer_pipeline.run_all,
        paper_ids=req.paper_ids,
        force_reanalyze=req.force_reanalyze
    )
    return {"status": "started", "message": "Analyzer pipeline triggered."}

@router.post("/pause")
def pause_analysis():
    """Pause analyzer execution."""
    progress_manager.pause()
    return {"status": "paused", "message": "Analyzer paused."}

@router.post("/resume")
def resume_analysis():
    """Resume paused analyzer execution."""
    progress_manager.resume()
    return {"status": "resumed", "message": "Analyzer resumed."}

@router.post("/cancel")
def cancel_analysis():
    """Cancel analyzer execution safely without corrupting completed work."""
    progress_manager.cancel()
    return {"status": "cancelled", "message": "Analyzer cancelled."}

@router.post("/retry")
def retry_failed(background_tasks: BackgroundTasks):
    """Retry processing for failed papers."""
    status = progress_manager.get_status()
    if status.active:
        return {"status": "already_running", "message": "Analyzer is currently running."}

    # Find failed papers
    all_papers = analyzer_pipeline.ws.list_all_papers()
    failed_ids = [p["id"] for p in all_papers if p.get("processing_status") in ["Failed", "Awaiting Retry"]]
    
    if not failed_ids:
        return {"status": "none", "message": "No failed papers found to retry."}

    background_tasks.add_task(
        analyzer_pipeline.run_all,
        paper_ids=failed_ids,
        force_reanalyze=True
    )
    return {"status": "retrying", "retrying_count": len(failed_ids)}

