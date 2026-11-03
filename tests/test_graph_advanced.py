import pytest
from app.core.workspace_manager import WorkspaceManager
from app.services.graph_service import GraphService
from app.services.paper_service import PaperService
from app.api.graph import get_knowledge_graph

@pytest.fixture
def mock_graph_ws(tmp_path):
    ws_dir = tmp_path / "test_graph_ws"
    ws = WorkspaceManager()
    ws.create_workspace(ws_dir, name="Test Graph WS")
    return ws, ws_dir

def test_empty_graph_state(mock_graph_ws):
    ws, _ = mock_graph_ws
    service = GraphService(ws_manager=ws)
    data = service.build_graph()

    assert data["graph_state"] == "empty_library"
    assert "No research papers found" in data["state_message"]
    assert len(data["elements"]["nodes"]) == 0
    assert len(data["elements"]["edges"]) == 0

def test_graph_nodes_and_relationships(mock_graph_ws):
    ws, _ = mock_graph_ws
    paper_srv = PaperService(ws_manager=ws)
    service = GraphService(ws_manager=ws)

    # Import paper A
    paper_a = {
        "id": "W1001",
        "title": "Deep Residual Learning for Image Recognition",
        "authors": ["Kaiming He", "Xiangyu Zhang"],
        "publication_year": 2016,
        "venue": "CVPR",
        "citation_count": 1000,
        "referenced_works": [],
        "topics": ["Computer Vision", "Deep Learning"]
    }
    paper_srv.import_paper(paper_a)

    # Import paper B citing paper A
    paper_b = {
        "id": "W1002",
        "title": "Identity Mappings in Deep Residual Networks",
        "authors": ["Kaiming He", "Jian Sun"],
        "publication_year": 2016,
        "venue": "ECCV",
        "citation_count": 500,
        "referenced_works": ["https://openalex.org/W1001"],
        "topics": ["Deep Learning", "Optimization"]
    }
    paper_srv.import_paper(paper_b)

    # Build basic paper graph
    data = service.build_graph(include_citations=True, include_semantics=False)
    assert data["stats"]["paper_nodes"] == 2
    assert data["stats"]["citation_edges"] == 1
    assert data["graph_state"] in ["small_corpus", "ready"]

    # Verify citation edge properties
    edge = data["elements"]["edges"][0]
    assert edge["data"]["source"] == "W1002"
    assert edge["data"]["target"] == "W1001"
    assert edge["data"]["type"] == "citation"

    # Test with Author and Topic nodes enabled
    data_with_aux = service.build_graph(
        include_citations=True,
        include_authors=True,
        include_topics=True
    )

    node_types = {n["data"]["type"] for n in data_with_aux["elements"]["nodes"]}
    assert "paper" in node_types
    assert "author" in node_types
    assert "topic" in node_types

    edge_types = {e["data"]["type"] for e in data_with_aux["elements"]["edges"]}
    assert "citation" in edge_types
    assert "authorship" in edge_types
    assert "concept" in edge_types

def test_api_graph_route(mock_graph_ws):
    ws, _ = mock_graph_ws
    from app.services.graph_service import graph_service
    graph_service.ws = ws

    paper_srv = PaperService(ws_manager=ws)
    paper_srv.import_paper({
        "id": "W2001",
        "title": "Attention Is All You Need",
        "authors": ["Ashish Vaswani", "Noam Shazeer"],
        "publication_year": 2017,
        "venue": "NeurIPS"
    })

    res = get_knowledge_graph(citations=True, semantics=True, authors=True, topics=True)
    assert res["stats"]["paper_nodes"] == 1
    assert res["graph_state"] in ["no_edges", "small_corpus"]

