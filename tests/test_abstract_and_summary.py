"""
Tests for Abstract and Structured Summary Services
"""
import pytest
from pathlib import Path
from app.services.abstract_service import AbstractService
from app.services.summary_service import SummaryService
from app.core.file_store import safe_read_text

def test_abstract_service(tmp_path: Path, sample_raw_paper):
    paper_dir = tmp_path / "paper_test"
    paper_dir.mkdir(parents=True)
    
    abstract = AbstractService.process_and_save_abstract(paper_dir, sample_raw_paper)
    assert "Recent work has demonstrated substantial gains" in abstract
    assert (paper_dir / "abstract.txt").exists()
    assert safe_read_text(paper_dir / "abstract.txt") == abstract

def test_summary_service_8_sections(tmp_path: Path, sample_raw_paper):
    paper_dir = tmp_path / "paper_test"
    paper_dir.mkdir(parents=True)
    abstract = "Recent work has demonstrated substantial gains on NLP tasks using transformer neural models. We train GPT-3. Results show high few-shot performance."
    keywords = ["transformers", "language models", "few-shot learning"]

    summary = SummaryService.generate_structured_summary(sample_raw_paper, abstract, keywords)
    
    assert summary.paper_id == "W2741809807"
    assert summary.scope == "Abstract-only Analysis"
    assert summary.research_objective
    assert summary.research_problem
    assert summary.methodology
    assert summary.dataset_or_materials
    assert summary.main_findings
    assert summary.limitations
    assert len(summary.important_keywords) > 0
    assert len(summary.potential_connections) > 0

    md_content = SummaryService.save_summary(paper_dir, summary, sample_raw_paper)
    assert (paper_dir / "summary.md").exists()
    assert "# Structured Research Summary" in md_content
    assert "### 1. Research Objective" in md_content
    assert "### 8. Future Research Directions" in md_content
    assert "### Potential Research Connections" in md_content

