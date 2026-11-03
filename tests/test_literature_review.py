"""
Tests for Literature Review Studio Service
"""
import pytest
from pathlib import Path
from app.core.workspace_manager import WorkspaceManager
from app.services.literature_review_service import LiteratureReviewService
from app.services.paper_service import PaperService

def test_generate_literature_review(tmp_path: Path):
    ws_dir = tmp_path / "rev_ws"
    ws = WorkspaceManager(ws_dir)
    ws.create_workspace(ws_dir, "Review Test Lab")

    ps = PaperService(ws)
    ps.import_paper({
        "id": "R001",
        "title": "Attention Is All You Need for Sequence Modeling",
        "authors": ["Ashish Vaswani", "Noam Shazeer"],
        "publication_year": 2017,
        "venue": "NeurIPS",
        "doi": "https://doi.org/10.1145/transformer",
        "collections": ["general"]
    })
    ps.import_paper({
        "id": "R002",
        "title": "BERT: Pre-training of Deep Bidirectional Transformers",
        "authors": ["Jacob Devlin", "Ming-Wei Chang"],
        "publication_year": 2019,
        "venue": "NAACL",
        "doi": "https://doi.org/10.1145/bert",
        "collections": ["general"]
    })

    service = LiteratureReviewService(ws)
    review = service.generate_review(topic="Transformers", paper_ids=["R001", "R002"])

    assert review.topic == "Transformers"
    assert len(review.paper_ids) == 2
    assert len(review.thematic_groups) > 0
    assert len(review.outline) == 5

    # Check academic Markdown draft and in-text citation formatting
    assert "# Scientific Literature Review" in review.markdown_draft
    assert "[Vaswani, 2017]" in review.markdown_draft or "[Devlin, 2019]" in review.markdown_draft

    # Check BibTeX entries
    assert "@article{" in review.bibtex_entries
    assert "Vaswani2017" in review.bibtex_entries or "Devlin2019" in review.bibtex_entries

