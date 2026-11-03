"""
Tests for Paper Library Management and Deduplication
"""
import pytest
from app.services.paper_service import PaperService

def test_paper_import_and_deduplication(temp_workspace, sample_raw_paper):
    service = PaperService(temp_workspace)

    # 1. First import
    imported = service.import_paper(sample_raw_paper, target_collection="general")
    assert imported["id"] == "W2741809807"
    assert "general" in imported["collections"]

    # Verify files created in workspace
    paper_dir = temp_workspace.get_paper_dir("W2741809807")
    assert (paper_dir / "paper.json").exists()

    # 2. Duplicate detection by DOI
    dup_by_doi = dict(sample_raw_paper)
    dup_by_doi["id"] = "DIFFERENT_ID"
    dup = service.find_duplicate(dup_by_doi)
    assert dup is not None
    assert dup["id"] == "W2741809807"

    # 3. Duplicate detection by Title
    dup_by_title = {
        "id": "ANOTHER_ID",
        "title": "Language Models are Few-Shot Learners!"
    }
    dup_title = service.find_duplicate(dup_by_title)
    assert dup_title is not None
    assert dup_title["id"] == "W2741809807"

def test_library_filtering_and_sorting(temp_workspace, sample_raw_paper, sample_raw_paper_2):
    service = PaperService(temp_workspace)
    service.import_paper(sample_raw_paper)
    service.import_paper(sample_raw_paper_2)

    # List all
    all_papers = service.list_papers()
    assert len(all_papers) == 2

    # Filter by query
    query_res = service.list_papers(query="Attention")
    assert len(query_res) == 1
    assert query_res[0]["id"] == "W2145678901"

    # Filter by year
    year_res = service.list_papers(year=2020)
    assert len(year_res) == 1
    assert year_res[0]["id"] == "W2741809807"

def test_user_notes_preservation(temp_workspace, sample_raw_paper):
    service = PaperService(temp_workspace)
    service.import_paper(sample_raw_paper)

    temp_workspace.save_paper_notes(sample_raw_paper["id"], "My custom critical notes on GPT-3.")
    detail = temp_workspace.get_paper_detail(sample_raw_paper["id"])
    assert detail["notes"] == "My custom critical notes on GPT-3."

