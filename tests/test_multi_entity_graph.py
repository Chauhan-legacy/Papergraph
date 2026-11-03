"""
Tests for Multi-Entity Knowledge Graph and Edge Explanations
"""
import pytest
from pathlib import Path
from app.core.workspace_manager import WorkspaceManager
from app.services.graph_service import GraphService
from app.services.paper_service import PaperService

def test_multi_entity_graph_methods_and_datasets(tmp_path: Path):
    ws_dir = tmp_path / "graph_ws"
    ws = WorkspaceManager(ws_dir)
    ws.create_workspace(ws_dir, "Graph Multi Entity Lab")

    ps = PaperService(ws)
    ps.import_paper({
        "id": "G001",
        "title": "Deep Residual Learning for Image Recognition",
        "authors": ["Kaiming He", "Xiangyu Zhang"],
        "publication_year": 2016,
        "venue": "CVPR",
        "referenced_works": ["G002"],
        "collections": ["general"]
    })
    ps.import_paper({
        "id": "G002",
        "title": "Very Deep Convolutional Networks for Large-Scale Image Recognition",
        "authors": ["Karen Simonyan", "Andrew Zisserman"],
        "publication_year": 2015,
        "venue": "ICLR",
        "referenced_works": [],
        "collections": ["general"]
    })

    service = GraphService(ws)
    graph = service.build_graph(
        include_citations=True,
        include_semantics=True,
        include_authors=True,
        include_topics=True,
        include_methods=True,
        include_datasets=True
    )

    stats = graph["stats"]
    assert stats["paper_nodes"] == 2
    assert stats["citation_edges"] == 1
    assert stats["author_nodes"] >= 2

    # Check edge explanations
    citation_edge = [e for e in graph["elements"]["edges"] if e["data"]["type"] == "citation"][0]
    assert "explanation" in citation_edge["data"]
    assert "explicitly references" in citation_edge["data"]["explanation"]

