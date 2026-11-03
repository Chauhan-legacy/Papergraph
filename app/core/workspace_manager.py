"""
Workspace Manager for PaperGraph
Manages local research workspace creation, validation, paper scanning, and directory operations.
Authoritative storage is entirely file-based (JSON, Markdown, TXT, CSV).
"""
import os
import json
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from app.config import config
from app.core.file_store import (
    atomic_write_json,
    atomic_write_text,
    safe_read_json,
    safe_read_text,
    sanitize_id
)
from app.core.validation import validate_workspace_path, normalize_title
from app.models.schemas import WorkspaceInfo, PaperMetadata, Collection

class WorkspaceManager:
    def __init__(self, workspace_path: Optional[Path] = None):
        if workspace_path:
            self.workspace_path = Path(workspace_path).resolve()
        else:
            self.workspace_path = config.get_active_workspace().resolve()

    def exists(self) -> bool:
        """Check if active workspace exists and is valid."""
        valid, _ = validate_workspace_path(self.workspace_path)
        return valid

    def create_workspace(self, path: Optional[Path] = None, name: str = "My Research Workspace") -> Dict[str, Any]:
        """Create and initialize a new PaperGraph workspace."""
        target_path = Path(path).resolve() if path else self.workspace_path
        target_path.mkdir(parents=True, exist_ok=True)
        
        subdirs = ["library", "collections", "graphs", "exports", "cache", "logs", "backups"]
        for d in subdirs:
            (target_path / d).mkdir(parents=True, exist_ok=True)
            
        now_str = datetime.datetime.now().isoformat()
        ws_info = {
            "workspace_name": name,
            "version": config.version,
            "created_at": now_str,
            "updated_at": now_str,
            "active_model": config.embedding_model_name,
            "settings": {
                "auto_backup": True,
                "max_graph_nodes": config.max_graph_nodes,
                "similarity_threshold": config.semantic_similarity_threshold,
                "theme": "jade"
            }
        }
        atomic_write_json(target_path / "workspace.json", ws_info)
        
        # Create a default "Uncategorized" or "Starred" collection
        default_col_id = "general"
        default_collection = {
            "id": default_col_id,
            "name": "General Reading",
            "description": "Default research collection for imported literature.",
            "paper_ids": [],
            "created_at": now_str,
            "updated_at": now_str
        }
        atomic_write_json(target_path / "collections" / f"{default_col_id}.json", default_collection)
        
        self.workspace_path = target_path
        config.current_workspace_dir = str(target_path)
        return self.get_info()

    def open_workspace(self, path: Path) -> Dict[str, Any]:
        """Open an existing workspace after validation."""
        target_path = Path(path).resolve()
        valid, msg = validate_workspace_path(target_path)
        if not valid:
            raise ValueError(f"Invalid workspace at {target_path}: {msg}")
            
        self.workspace_path = target_path
        config.current_workspace_dir = str(target_path)
        return self.get_info()

    def get_info(self) -> Dict[str, Any]:
        """Return workspace statistics directly calculated from files."""
        ws_file = self.workspace_path / "workspace.json"
        metadata = safe_read_json(ws_file, {})
        
        papers = self.list_all_papers()
        completed = sum(1 for p in papers if p.get("processing_status") in ["Analysis Completed", "Graph Processed"])
        pending = len(papers) - completed
        
        collections = self.list_collections()
        
        return {
            "workspace_path": str(self.workspace_path),
            "workspace_name": metadata.get("workspace_name", "PaperGraph Workspace"),
            "version": metadata.get("version", config.version),
            "paper_count": len(papers),
            "completed_analyses": completed,
            "pending_analyses": pending,
            "collections_count": len(collections),
            "created_at": metadata.get("created_at", ""),
            "updated_at": metadata.get("updated_at", ""),
            "settings": metadata.get("settings", {})
        }

    def rebuild_workspace_index(self) -> Dict[str, Any]:
        """Rescan library files and refresh workspace info."""
        return self.get_info()

    def list_all_papers(self) -> List[Dict[str, Any]]:
        """Scan library/ folder and return metadata for all papers."""
        lib_dir = self.workspace_path / "library"
        if not lib_dir.exists():
            return []
            
        papers = []
        for paper_dir in sorted(lib_dir.iterdir()):
            if not paper_dir.is_dir():
                continue
            paper_json_path = paper_dir / "paper.json"
            if paper_json_path.exists():
                data = safe_read_json(paper_json_path)
                if data and "id" in data:
                    # check if summary, analysis, notes exist
                    data["has_summary"] = (paper_dir / "summary.md").exists()
                    data["has_analysis"] = (paper_dir / "analysis.json").exists()
                    data["has_notes"] = (paper_dir / "notes.md").exists()
                    papers.append(data)
        return papers

    def get_paper_dir(self, paper_id: str) -> Path:
        """Get directory path for a specific paper."""
        safe_id = sanitize_id(paper_id)
        return self.workspace_path / "library" / safe_id

    def get_paper_detail(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve full details of a paper including files."""
        p_dir = self.get_paper_dir(paper_id)
        if not p_dir.exists():
            return None
            
        meta = safe_read_json(p_dir / "paper.json")
        if not meta:
            return None
            
        abstract = safe_read_text(p_dir / "abstract.txt")
        summary = safe_read_text(p_dir / "summary.md")
        analysis = safe_read_json(p_dir / "analysis.json", {})
        notes = safe_read_text(p_dir / "notes.md")
        
        return {
            "metadata": meta,
            "abstract": abstract,
            "summary": summary,
            "analysis": analysis,
            "notes": notes
        }

    def save_paper_metadata(self, paper_id: str, metadata: Dict[str, Any]) -> None:
        """Save paper metadata."""
        p_dir = self.get_paper_dir(paper_id)
        p_dir.mkdir(parents=True, exist_ok=True)
        atomic_write_json(p_dir / "paper.json", metadata)

    def save_paper_notes(self, paper_id: str, notes: str) -> None:
        """Save user notes without touching other files."""
        p_dir = self.get_paper_dir(paper_id)
        p_dir.mkdir(parents=True, exist_ok=True)
        atomic_write_text(p_dir / "notes.md", notes)

    def list_collections(self) -> List[Dict[str, Any]]:
        """List all user collections."""
        col_dir = self.workspace_path / "collections"
        if not col_dir.exists():
            return []
            
        collections = []
        for col_file in sorted(col_dir.glob("*.json")):
            data = safe_read_json(col_file)
            if data and "id" in data:
                collections.append(data)
        return collections

    def save_collection(self, collection_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save or update a collection."""
        col_dir = self.workspace_path / "collections"
        col_dir.mkdir(parents=True, exist_ok=True)
        cid = sanitize_id(collection_data.get("id", "col_default"))
        collection_data["id"] = cid
        collection_data["updated_at"] = datetime.datetime.now().isoformat()
        if "created_at" not in collection_data or not collection_data["created_at"]:
            collection_data["created_at"] = collection_data["updated_at"]
        atomic_write_json(col_dir / f"{cid}.json", collection_data)
        return collection_data

    def delete_collection(self, collection_id: str) -> bool:
        """Delete a collection file."""
        col_path = self.workspace_path / "collections" / f"{sanitize_id(collection_id)}.json"
        if col_path.exists():
            try:
                col_path.unlink()
                return True
            except Exception:
                return False
        return False

# Global instance initialized with config
workspace_manager = WorkspaceManager()

