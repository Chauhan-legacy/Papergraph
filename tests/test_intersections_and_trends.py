"""
Tests for Candidate Intersections and Trend Analytics
"""
import pytest
from app.services.paper_service import PaperService
from app.services.analyzer_pipeline import AnalyzerPipeline
from app.services.intersection_service import IntersectionService
from app.services.trend_service import TrendService

def test_intersections_and_trends(temp_workspace, sample_raw_paper, sample_bio_paper):
    paper_srv = PaperService(temp_workspace)
    p1 = paper_srv.import_paper(sample_raw_paper)
    p2 = paper_srv.import_paper(sample_bio_paper)

    pipeline = AnalyzerPipeline(temp_workspace)
    pipeline.run_all(paper_ids=[p1["id"], p2["id"]], force_reanalyze=True)

    # 1. Test Intersections
    inter_service = IntersectionService(temp_workspace)
    intersections = inter_service.find_intersections()
    assert isinstance(intersections, list)
    if intersections:
        cand = intersections[0]
        assert "Candidate Research Intersection" in cand["title"]
        assert cand["limitations"]
        assert cand["reason_suggested"]

    # 2. Test Trends
    trend_srv = TrendService(temp_workspace)
    trends = trend_srv.compute_trends()

    assert trends["total_analyzed"] == 2
    assert "2020" in trends["publications_by_year"] or "2021" in trends["publications_by_year"]
    # Small corpus warning
    assert len(trends["warnings"]) > 0
    assert "Corpus size is limited" in trends["warnings"][0]

