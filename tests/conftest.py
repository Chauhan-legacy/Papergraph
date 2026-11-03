"""
Pytest configuration and common fixtures for PaperGraph tests
"""
import pytest
import shutil
from pathlib import Path
from app.config import config
from app.core.workspace_manager import WorkspaceManager

@pytest.fixture
def temp_workspace(tmp_path: Path):
    """Fixture providing a temporary, clean PaperGraph workspace."""
    ws_dir = tmp_path / "Test_Workspace"
    mgr = WorkspaceManager(ws_dir)
    mgr.create_workspace(path=ws_dir, name="Test Research Workspace")
    old_cur = config.current_workspace_dir
    config.current_workspace_dir = str(ws_dir)
    yield mgr
    config.current_workspace_dir = old_cur
    if ws_dir.exists():
        shutil.rmtree(ws_dir, ignore_errors=True)

@pytest.fixture
def sample_raw_paper():
    """Sample paper matching OpenAlex schema with inverted index abstract."""
    return {
        "id": "W2741809807",
        "openalex_id": "https://openalex.org/W2741809807",
        "doi": "https://doi.org/10.1038/s41586-020-2649-2",
        "title": "Language Models are Few-Shot Learners",
        "authors": [
            {"name": "Tom Brown", "institution": "OpenAI", "orcid": None},
            {"name": "Benjamin Mann", "institution": "OpenAI", "orcid": None}
        ],
        "publication_year": 2020,
        "publication_date": "2020-07-22",
        "venue": "NeurIPS",
        "source_provider": "openalex",
        "source_url": "https://doi.org/10.1038/s41586-020-2649-2",
        "citation_count": 14500,
        "referenced_works": ["W2145678901", "W2987654321"],
        "abstract_inverted_index": {
            "Recent": [0],
            "work": [1],
            "has": [2],
            "demonstrated": [3],
            "substantial": [4],
            "gains": [5],
            "on": [6],
            "many": [7],
            "NLP": [8],
            "tasks": [9],
            "using": [10],
            "transformer": [11],
            "neural": [12],
            "models.": [13]
        },
        "processing_status": "Discovered"
    }

@pytest.fixture
def sample_raw_paper_2():
    """Second sample paper in Computer Science / Deep Learning."""
    return {
        "id": "W2145678901",
        "openalex_id": "https://openalex.org/W2145678901",
        "doi": "https://doi.org/10.1145/3318464.3389700",
        "title": "Attention Is All You Need",
        "authors": [
            {"name": "Ashish Vaswani", "institution": "Google Brain", "orcid": None}
        ],
        "publication_year": 2017,
        "publication_date": "2017-06-12",
        "venue": "NeurIPS",
        "source_provider": "openalex",
        "source_url": "https://arxiv.org/abs/1706.03762",
        "citation_count": 85000,
        "referenced_works": [],
        "abstract_inverted_index": {
            "The": [0],
            "dominant": [1],
            "sequence": [2],
            "transduction": [3],
            "models": [4],
            "are": [5],
            "based": [6],
            "on": [7],
            "complex": [8],
            "recurrent": [9],
            "or": [10],
            "convolutional": [11],
            "neural": [12],
            "networks.": [13]
        },
        "processing_status": "Discovered"
    }

@pytest.fixture
def sample_bio_paper():
    """Third sample paper in Biology & Medicine."""
    return {
        "id": "W3123456789",
        "openalex_id": "https://openalex.org/W3123456789",
        "doi": "https://doi.org/10.1016/j.cell.2020.08.001",
        "title": "Deep Learning for Genomic and Protein Structure Prediction",
        "authors": [
            {"name": "John Jumper", "institution": "DeepMind", "orcid": None}
        ],
        "publication_year": 2021,
        "venue": "Nature",
        "source_provider": "openalex",
        "source_url": "https://doi.org/10.1016/j.cell.2020.08.001",
        "citation_count": 9200,
        "referenced_works": ["W2741809807"],
        "abstract_inverted_index": {
            "Predicting": [0],
            "the": [1],
            "3D": [2],
            "structure": [3],
            "that": [4],
            "a": [5],
            "protein": [6],
            "adopts": [7],
            "from": [8],
            "its": [9],
            "amino": [10],
            "acid": [11],
            "sequence": [12],
            "is": [13],
            "a": [14],
            "fundamental": [15],
            "biological": [16],
            "challenge.": [17]
        },
        "processing_status": "Discovered"
    }

