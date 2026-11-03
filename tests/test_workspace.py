"""
Tests for Workspace Manager and File-First Organization
"""
import pytest
from pathlib import Path
from app.core.workspace_manager import WorkspaceManager
from app.core.validation import validate_workspace_path

def test_workspace_creation_and_structure(tmp_path: Path):
    ws_dir = tmp_path / "My_Test_Workspace"
    mgr = WorkspaceManager(ws_dir)
    info = mgr.create_workspace(path=ws_dir, name="Biology Lab")

    assert info["workspace_name"] == "Biology Lab"
    assert (ws_dir / "workspace.json").exists()
    
    # Required subdirectories
    for req in ["library", "collections", "graphs", "exports", "cache", "logs", "backups"]:
        assert (ws_dir / req).is_dir()

    valid, msg = validate_workspace_path(ws_dir)
    assert valid is True

def test_workspace_open_and_info(temp_workspace: WorkspaceManager):
    info = temp_workspace.get_info()
    assert info["paper_count"] == 0
    assert info["completed_analyses"] == 0
    assert info["collections_count"] >= 1  # Default collection created

def test_collections_management(temp_workspace: WorkspaceManager):
    col_data = {
        "id": "quantum_reading",
        "name": "Quantum Reading",
        "description": "Foundational quantum computing papers."
    }
    saved = temp_workspace.save_collection(col_data)
    assert saved["id"] == "quantum_reading"

    cols = temp_workspace.list_collections()
    col_ids = [c["id"] for c in cols]
    assert "quantum_reading" in col_ids

    deleted = temp_workspace.delete_collection("quantum_reading")
    assert deleted is True
    assert "quantum_reading" not in [c["id"] for c in temp_workspace.list_collections()]

