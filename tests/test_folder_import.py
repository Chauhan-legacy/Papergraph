import pytest
import tempfile
import json
from pathlib import Path
import pypdf

from app.core.workspace_manager import WorkspaceManager
from app.services.folder_import_service import FolderImportService
from app.api.papers import scan_research_folder, import_research_folder, FolderScanRequest, FolderImportRequest

@pytest.fixture
def mock_folder_workspace(tmp_path):
    ws_dir = tmp_path / "test_ws"
    ws = WorkspaceManager()
    ws.create_workspace(ws_dir, name="Test Folder Import WS")
    return ws, ws_dir

@pytest.fixture
def sample_research_dir(tmp_path):
    src_dir = tmp_path / "user_papers"
    src_dir.mkdir(parents=True, exist_ok=True)

    # 1. Sample TXT paper
    txt_file = src_dir / "quantum_computing.txt"
    txt_file.write_text("""Quantum Algorithms for Optimization

Abstract:
This paper introduces a novel hybrid quantum-classical optimization method.
We evaluate the algorithm on standard benchmark combinatorial graphs.
The results show a significant speedup compared to classical simulated annealing.
DOI: 10.1103/PhysRevA.99.012345

Introduction:
Quantum computing offers exponential theoretical speedups for specific computational problems...
""", encoding="utf-8")

    # 2. Sample Markdown paper
    md_file = src_dir / "neural_networks.md"
    md_file.write_text("""# Neural Architecture Search for Edge Devices

By Alice Johnson and Bob Smith. Published in 2023.

## Abstract
We propose a lightweight neural architecture search framework specifically designed for edge devices with restricted thermal envelopes.
Evaluated on ImageNet and CIFAR-100 datasets, achieving 78.4% top-1 accuracy.
DOI: 10.1145/3318464.3389700

## Methodology
Our approach formulates neural architecture search as a constrained multi-objective problem...
""", encoding="utf-8")

    # 3. Sample JSON paper
    json_file = src_dir / "reinforcement_learning.json"
    json_file.write_text(json.dumps({
        "title": "Sample Efficient Reinforcement Learning via World Models",
        "authors": ["Elena Rostova", "Marcus Vance"],
        "publication_year": 2024,
        "doi": "10.48550/arXiv.2401.99999",
        "abstract": "Model-based reinforcement learning provides substantial sample efficiency benefits.",
        "full_text": "Model-based reinforcement learning provides substantial sample efficiency benefits by training a predictive world model."
    }), encoding="utf-8")

    # 4. Sample PDF paper created using pypdf
    pdf_file = src_dir / "attention_mechanisms.pdf"
    writer = pypdf.PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    # Add metadata
    writer.add_metadata({
        "/Title": "Sparse Attention Mechanisms for Long Context Sequences",
        "/Author": "Dr. Sarah Connor",
        "/Subject": "Computer Science - Machine Learning"
    })
    with open(pdf_file, "wb") as f:
        writer.write(f)

    # 5. Unsupported file format
    unsupported = src_dir / "presentation.pptx"
    unsupported.write_bytes(b"dummy pptx binary")

    return src_dir

def test_scan_directory_discovery(mock_folder_workspace, sample_research_dir):
    ws, _ = mock_folder_workspace
    service = FolderImportService(ws_manager=ws)

    scan_res = service.scan_directory(str(sample_research_dir))

    assert scan_res["supported_count"] == 4
    assert scan_res["unsupported_count"] == 1
    assert scan_res["ready_to_import_count"] == 4
    assert scan_res["already_imported_count"] == 0

    titles = [p["title"] for p in scan_res["discovered_papers"]]
    assert any("Quantum Algorithms" in t for t in titles)
    assert any("Neural Architecture" in t for t in titles)
    assert any("Reinforcement Learning" in t for t in titles)
    assert any("Sparse Attention" in t for t in titles)

def test_import_selected_files_and_preservation(mock_folder_workspace, sample_research_dir):
    ws, ws_dir = mock_folder_workspace
    service = FolderImportService(ws_manager=ws)

    # Original files check
    txt_path = sample_research_dir / "quantum_computing.txt"
    original_mtime = txt_path.stat().st_mtime

    res = service.import_selected_files(
        folder_path_str=str(sample_research_dir),
        selected_filenames=["quantum_computing.txt", "neural_networks.md"]
    )

    assert res["imported_count"] == 2
    assert len(res["errors"]) == 0

    # Verify original file untouched
    assert txt_path.stat().st_mtime == original_mtime

    # Verify library files created in workspace
    papers = ws.list_all_papers()
    assert len(papers) == 2

    for p in papers:
        p_dir = ws.get_paper_dir(p["id"])
        assert (p_dir / "paper.json").exists()
        assert (p_dir / "full_text.txt").exists()
        assert p["source_provider"] == "local_folder"

    # Test duplicate detection on re-scan
    re_scan = service.scan_directory(str(sample_research_dir))
    assert re_scan["already_imported_count"] == 2
    assert re_scan["ready_to_import_count"] == 2

def test_folder_import_api_endpoints(mock_folder_workspace, sample_research_dir):
    ws, _ = mock_folder_workspace
    from app.services.folder_import_service import folder_import_service
    folder_import_service.ws = ws

    # Test scan endpoint
    scan_req = FolderScanRequest(folder_path=str(sample_research_dir))
    scan_resp = scan_research_folder(scan_req)
    assert scan_resp["supported_count"] == 4

    # Test import endpoint
    import_req = FolderImportRequest(
        folder_path=str(sample_research_dir),
        selected_filenames=["quantum_computing.txt"]
    )
    import_resp = import_research_folder(import_req)
    assert import_resp["imported_count"] == 1
