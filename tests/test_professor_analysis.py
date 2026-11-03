"""
Tests for Professor-Level Analysis & Claim Tracking Service
"""
import pytest
from pathlib import Path
from app.services.professor_analysis_service import ProfessorAnalysisService

def test_professor_analysis_from_abstract(tmp_path: Path, sample_raw_paper):
    paper_dir = tmp_path / "paper_test"
    paper_dir.mkdir(parents=True)
    abstract = (
        "Despite recent advances, language models suffer from catastrophic forgetting during fine-tuning. "
        "We propose an orthogonal projection methodology to constrain weight updates. "
        "Evaluations on benchmark GLUE show 94% retention with minimal throughput penalty. "
        "However, our method is bounded by quadratic memory requirements."
    )
    keywords = ["language models", "orthogonal projection", "catastrophic forgetting"]

    prof = ProfessorAnalysisService.analyze_paper(sample_raw_paper, abstract, keywords)

    assert prof.paper_id == "W2741809807"
    assert prof.scope == "Abstract-only Analysis"

    # Research problem breakdown
    assert "catastrophic forgetting" in prof.research_problem["exact_problem"].lower()
    assert prof.research_problem["why_it_matters"]
    assert prof.research_problem["foundational_assumptions"]

    # Methodology breakdown
    assert prof.methodology["intuitive_explanation"]
    assert prof.methodology["appropriateness_rationale"]
    assert prof.methodology["experimental_design"]

    # Results breakdown
    assert "94%" in prof.results["actual_observations"] or "retention" in prof.results["actual_observations"]
    assert prof.results["results_vs_interpretations"]

    # Critical evaluation
    assert prof.critical_evaluation["limitations"]
    assert prof.critical_evaluation["reproducibility_threats"]

    # Pedagogical explanation
    assert prof.professor_explanation["core_concept"]
    assert prof.professor_explanation["pedagogical_intuition"]
    assert prof.professor_explanation["mathematical_formalism"]

    # Discrete scientific claims with epistemic status
    assert len(prof.claims) >= 4
    statuses = [c.epistemic_status for c in prof.claims]
    assert "REPORTED" in statuses

    # Save and reload test
    ProfessorAnalysisService.save_analysis(paper_dir, prof, sample_raw_paper)
    assert (paper_dir / "professor_analysis.json").exists()
    assert (paper_dir / "professor_analysis.md").exists()

    loaded = ProfessorAnalysisService.load_analysis(paper_dir)
    assert loaded is not None
    assert loaded.paper_id == prof.paper_id
    assert loaded.title == prof.title

def test_professor_analysis_from_full_text(tmp_path: Path, sample_raw_paper):
    full_text = """
    # 1. Introduction
    Deep neural networks deployed in clinical decision support face severe trust hurdles.
    
    # 2. Methodology
    We formulate a Bayesian uncertainty estimation layer based on Monte Carlo dropout.
    Our training dataset comprises 45,000 anonymized radiology scans evaluated across three hospital sites.
    
    # 3. Empirical Results
    The model observed a diagnostic sensitivity of 91.2% with a 0.05 false positive rate.
    
    # 4. Critical Limitations
    A critical limitation is the susceptibility to distribution shifts across different MRI scanner manufacturers.
    """
    keywords = ["clinical ai", "bayesian uncertainty", "radiology"]

    prof = ProfessorAnalysisService.analyze_paper(sample_raw_paper, abstract="", keywords=keywords, full_text=full_text)

    assert "Full Paper Text Analysis" in prof.scope
    assert len(prof.claims) > 0
    assert "radiology" in prof.methodology["datasets_and_variables"].lower() or "clinical" in prof.research_problem["exact_problem"].lower()

