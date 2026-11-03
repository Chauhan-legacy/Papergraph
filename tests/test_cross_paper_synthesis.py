"""
Tests for Cross-Paper Scientific Synthesis & Evidence Matrix Service
"""
import pytest
from pathlib import Path
from app.core.workspace_manager import WorkspaceManager
from app.services.synthesis_service import SynthesisService
from app.services.paper_service import PaperService

@pytest.fixture
def mock_ws_with_papers(tmp_path: Path):
    ws_dir = tmp_path / "test_ws"
    ws = WorkspaceManager(ws_dir)
    ws.create_workspace(ws_dir, "Test Synthesis Lab")

    ps = PaperService(ws)
    p1 = {
        "id": "P001",
        "title": "Scalable Graph Transformers for Molecular Representation",
        "authors": ["Alice Smith", "Bob Jones"],
        "publication_year": 2022,
        "venue": "NeurIPS",
        "doi": "https://doi.org/10.1145/123",
        "referenced_works": ["P002"],
        "collections": ["general"]
    }
    p2 = {
        "id": "P002",
        "title": "Equivariant Message Passing in 3D Point Clouds",
        "authors": ["Carol White"],
        "publication_year": 2023,
        "venue": "ICLR",
        "doi": "https://doi.org/10.1145/456",
        "referenced_works": [],
        "collections": ["general"]
    }
    ps.import_paper(p1)
    ps.import_paper(p2)
    return ws

def test_cross_paper_comparison(mock_ws_with_papers):
    service = SynthesisService(mock_ws_with_papers)
    cmp_res = service.compare_papers(["P001", "P002"])

    assert cmp_res.comparison_id.startswith("cmp_2_")
    assert "P001" in cmp_res.paper_ids
    assert "P002" in cmp_res.paper_ids
    assert len(cmp_res.consensus_points) > 0
    assert len(cmp_res.disagreement_points) > 0
    assert "P001" in cmp_res.dimensions
    assert "methodology" in cmp_res.dimensions["P001"]

def test_evidence_matrix_generation_and_export(mock_ws_with_papers):
    service = SynthesisService(mock_ws_with_papers)
    matrix = service.build_evidence_matrix()

    assert matrix.total_papers == 2
    assert len(matrix.rows) == 2
    row = matrix.rows[0]
    assert row.title
    assert row.method
    assert row.epistemic_grade in ["High", "Moderate"]

    csv_data = service.export_matrix(format_type="csv")
    assert "Paper ID,Title,Year" in csv_data
    assert "P001" in csv_data
    assert "P002" in csv_data

    md_data = service.export_matrix(format_type="markdown")
    assert "# Scientific Evidence Matrix" in md_data
    assert "| Paper | Year |" in md_data

def test_corpus_patterns_detection(mock_ws_with_papers):
    service = SynthesisService(mock_ws_with_papers)
    patterns = service.detect_corpus_patterns()

    assert patterns.total_analyzed_papers == 2
    assert isinstance(patterns.repeated_methods, list)
    assert isinstance(patterns.recurring_datasets, list)
    assert isinstance(patterns.common_limitations, list)

