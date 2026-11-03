"""
Tests for Cytoscape Knowledge Graph Service
"""
import pytest
from app.services.paper_service import PaperService
from app.services.analyzer_pipeline import AnalyzerPipeline
from app.services.graph_service import GraphService

def test_empty_graph(temp_workspace):
    service = GraphService(temp_workspace)
    data = service.build_graph()
    assert data["stats"]["total_nodes"] == 0
    assert len(data["elements"]["nodes"]) == 0
    assert len(data["elements"]["edges"]) == 0

def test_graph_with_citations_and_semantics(temp_workspace, sample_raw_paper, sample_raw_paper_2):
    paper_srv = PaperService(temp_workspace)
    p1 = paper_srv.import_paper(sample_raw_paper)
    p2 = paper_srv.import_paper(sample_raw_paper_2)

    pipeline = AnalyzerPipeline(temp_workspace)
    pipeline.run_all(paper_ids=[p1["id"], p2["id"]], force_reanalyze=True)

    service = GraphService(temp_workspace)
    graph = service.build_graph(include_citations=True, include_semantics=True, min_similarity=0.20)

    assert graph["stats"]["total_nodes"] == 2
    nodes = graph["elements"]["nodes"]
    assert len(nodes) == 2

    # Check citation edge exists (W2741809807 -> W2145678901)
    citation_edges = [e for e in graph["elements"]["edges"] if e["data"]["type"] == "citation"]
    assert len(citation_edges) >= 1
    edge = citation_edges[0]
    assert edge["data"]["source"] == "W2741809807"
    assert edge["data"]["target"] == "W2145678901"

    # Check clusters assigned
    assert len(graph["clusters"]) > 0

    # Check ego graph
    ego = service.get_ego_graph(p1["id"])
    assert ego["stats"]["center_paper_id"] == p1["id"]
    assert ego["stats"]["total_nodes"] >= 1

