"""
Tests for Research Question & Hypothesis Explorer Service
"""
import pytest
from pathlib import Path
from app.core.workspace_manager import WorkspaceManager
from app.services.hypothesis_service import HypothesisService
from app.services.paper_service import PaperService

def test_discover_candidate_questions(tmp_path: Path):
    ws_dir = tmp_path / "hypo_ws"
    ws = WorkspaceManager(ws_dir)
    ws.create_workspace(ws_dir, "Hypothesis Test Lab")

    ps = PaperService(ws)
    ps.import_paper({
        "id": "H001",
        "title": "Quantum Annealing for Combinatorial Portfolio Optimization",
        "authors": ["Dr. Quantum"],
        "publication_year": 2021,
        "venue": "IEEE Quantum",
        "collections": ["general"]
    })
    ps.import_paper({
        "id": "H002",
        "title": "Graph Convolutional Networks for Power Grid Failure Cascades",
        "authors": ["Dr. Network"],
        "publication_year": 2023,
        "venue": "ACM Cyber-Physical",
        "collections": ["general"]
    })

    service = HypothesisService(ws)
    questions = service.discover_candidate_questions()

    assert len(questions) > 0
    q = questions[0]
    assert q.id.startswith("crq_")
    assert q.title
    assert q.suggested_hypothesis
    assert q.why_suggested
    assert len(q.supporting_papers) > 0
    assert len(q.supporting_evidence) > 0
    assert len(q.contradictory_or_limiting_evidence) > 0
    assert len(q.possible_methodological_approaches) > 0
    assert q.confidence_and_uncertainty
    # Crucial scientific boundary rule
    assert "Candidate Research Question / Potential Opportunity" in q.epistemic_boundary
