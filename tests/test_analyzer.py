"""
Tests for Multi-Stage Paper Analyzer Pipeline
"""
import pytest
from app.services.paper_service import PaperService
from app.services.analyzer_pipeline import AnalyzerPipeline
from app.core.progress_manager import progress_manager

def test_full_pipeline_execution(temp_workspace, sample_raw_paper, sample_raw_paper_2):
    paper_srv = PaperService(temp_workspace)
    p1 = paper_srv.import_paper(sample_raw_paper)
    p2 = paper_srv.import_paper(sample_raw_paper_2)

    pipeline = AnalyzerPipeline(temp_workspace)
    pipeline.run_all(paper_ids=[p1["id"], p2["id"]], force_reanalyze=True)

    # Check paper 1
    p1_dir = temp_workspace.get_paper_dir(p1["id"])
    assert (p1_dir / "abstract.txt").exists()
    assert (p1_dir / "summary.md").exists()
    assert (p1_dir / "analysis.json").exists()

    detail = temp_workspace.get_paper_detail(p1["id"])
    assert detail["metadata"]["processing_status"] == "Analysis Completed"
    assert len(detail["analysis"]["keywords"]) > 0
    assert len(detail["analysis"]["embedding"]) > 0

    # Verify progress manager status
    status = progress_manager.get_status()
    assert status.processed_papers == 2
    assert status.failed_papers == 0
    assert status.percent_complete == 100.0

def test_progress_manager_controls():
    progress_manager.start(5)
    assert progress_manager.active is True
    assert progress_manager.paused is False
    assert progress_manager.total_papers == 5

    progress_manager.pause()
    assert progress_manager.is_paused() is True

    progress_manager.resume()
    assert progress_manager.is_paused() is False

    progress_manager.cancel()
    assert progress_manager.is_interrupted() is True
    assert progress_manager.active is False

