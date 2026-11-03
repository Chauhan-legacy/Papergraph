"""
File-First Atomic Storage Manager for PaperGraph
Ensures reliable UTF-8 reads/writes with atomic replacement to prevent corruption.
"""
import os
import json
import tempfile
import re
from pathlib import Path
from typing import Any, Optional, Dict

def sanitize_id(identifier: str) -> str:
    """Sanitize any ID into a filesystem-safe identifier."""
    # Handle URLs like https://openalex.org/W123456
    clean = re.sub(r"^https?://[^/]+/", "", identifier)
    # Remove chars not allowed in Windows filenames: \ / : * ? " < > |
    clean = re.sub(r'[\\/*?:"<>|]', "_", clean)
    clean = clean.strip(" ._")
    return clean if clean else "paper_unknown"

def atomic_write_text(file_path: Path, content: str, encoding: str = "utf-8") -> None:
    """Atomically write text content to a file."""
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    dir_name = file_path.parent
    
    with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding=encoding) as tf:
        tf.write(content)
        tf.flush()
        os.fsync(tf.fileno())
        temp_name = tf.name
        
    try:
        os.replace(temp_name, file_path)
    except Exception:
        # Fallback for Windows if file exists or locked
        if os.path.exists(temp_name):
            try:
                os.remove(temp_name)
            except Exception:
                pass
        raise

def atomic_write_json(file_path: Path, data: Any, indent: int = 2) -> None:
    """Atomically write Python data as JSON."""
    content = json.dumps(data, indent=indent, ensure_ascii=False)
    atomic_write_text(file_path, content)

def safe_read_text(file_path: Path, default: str = "", encoding: str = "utf-8") -> str:
    """Safely read text file, returns default on failure or missing file."""
    p = Path(file_path)
    if not p.exists() or not p.is_file():
        return default
    try:
        with open(p, "r", encoding=encoding, errors="replace") as f:
            return f.read()
    except Exception:
        return default

def safe_read_json(file_path: Path, default: Optional[Dict[str, Any]] = None) -> Any:
    """Safely read JSON file, returns default on missing or corrupted file."""
    if default is None:
        default = {}
    p = Path(file_path)
    if not p.exists() or not p.is_file():
        return default
    try:
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            return json.load(f)
    except Exception:
        return default

