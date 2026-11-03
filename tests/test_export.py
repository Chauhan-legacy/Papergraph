"""
Tests for Academic Literature Export Service
"""
import pytest
from app.services.paper_service import PaperService
from app.services.export_service import ExportService

def test_export_formats(temp_workspace, sample_raw_paper):
    paper_srv = PaperService(temp_workspace)
    paper_srv.import_paper(sample_raw_paper)

    export_srv = ExportService(temp_workspace)

    # 1. BibTeX
    bib_res = export_srv.export("bibtex")
    assert bib_res["paper_count"] == 1
    assert "@article" in bib_res["content"]
    assert "Language Models are Few-Shot Learners" in bib_res["content"]

    # 2. JSON
    json_res = export_srv.export("json")
    assert json_res["paper_count"] == 1
    assert "W2741809807" in json_res["content"]

    # 3. CSV
    csv_res = export_srv.export("csv")
    assert csv_res["paper_count"] == 1
    assert "title,authors,year" in csv_res["content"].lower()

    # 4. Markdown
    md_res = export_srv.export("markdown")
    assert md_res["paper_count"] == 1
    assert "# Research Literature Export" in md_res["content"]

