"""
Tests for Atomic File-First Storage
"""
import pytest
from pathlib import Path
from app.core.file_store import (
    atomic_write_text,
    atomic_write_json,
    safe_read_text,
    safe_read_json,
    sanitize_id
)

def test_sanitize_id():
    assert sanitize_id("https://openalex.org/W2741809807") == "W2741809807"
    assert sanitize_id("10.1038/s41586-020-2649-2") == "10.1038_s41586-020-2649-2"
    assert sanitize_id("paper?name*<test>") == "paper_name__test"
    assert sanitize_id("") == "paper_unknown"

def test_atomic_write_and_read_text(tmp_path: Path):
    target_file = tmp_path / "sub" / "test.txt"
    content = "Hello PaperGraph UTF-8: äöü, αβγ, 中文, 🔬"
    
    atomic_write_text(target_file, content)
    assert target_file.exists()
    
    read_back = safe_read_text(target_file)
    assert read_back == content

def test_atomic_write_and_read_json(tmp_path: Path):
    target_file = tmp_path / "data.json"
    data = {
        "title": "Quantum Computation",
        "scores": [0.95, 0.88],
        "nested": {"valid": True, "count": 42}
    }
    
    atomic_write_json(target_file, data)
    assert target_file.exists()
    
    loaded = safe_read_json(target_file)
    assert loaded == data

def test_safe_read_missing_files(tmp_path: Path):
    non_existent = tmp_path / "non_existent.txt"
    assert safe_read_text(non_existent, default="fallback") == "fallback"
    assert safe_read_json(tmp_path / "missing.json", default={"k": "v"}) == {"k": "v"}
