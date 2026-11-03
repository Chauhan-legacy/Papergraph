"""
Validation and Normalization utilities for PaperGraph
"""
import re
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

def normalize_title(title: str) -> str:
    """Normalize a paper title for deduplication."""
    if not title:
        return ""
    # Lowercase, strip punctuation and excessive whitespace
    cleaned = re.sub(r"[^\w\s]", "", title.lower())
    return " ".join(cleaned.split())

def validate_workspace_path(path: Path) -> Tuple[bool, str]:
    """Check if a directory is a valid PaperGraph workspace."""
    p = Path(path)
    if not p.exists():
        return False, "Directory does not exist."
    if not p.is_dir():
        return False, "Path is not a directory."
    
    ws_file = p / "workspace.json"
    if not ws_file.exists():
        return False, "Missing workspace.json metadata file."
        
    required_dirs = ["library", "collections", "graphs", "exports", "cache"]
    for req in required_dirs:
        req_path = p / req
        if not req_path.exists():
            return False, f"Missing required workspace directory: {req}"
            
    return True, "Workspace is valid."

def validate_paper_metadata(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate paper metadata before persistence."""
    if not isinstance(data, dict):
        return False, "Paper data must be a dictionary."
    if not data.get("title") or not str(data["title"]).strip():
        return False, "Paper title cannot be empty."
    if not data.get("id"):
        return False, "Paper identifier cannot be empty."
    return True, None

