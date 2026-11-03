"""
Abstract Extraction and Processing Service
"""
from pathlib import Path
from typing import Optional, Dict, Any

from app.core.file_store import atomic_write_text, safe_read_text
from app.providers.openalex import reconstruct_abstract

class AbstractService:
    @staticmethod
    def process_and_save_abstract(paper_dir: Path, raw_paper_data: Dict[str, Any]) -> str:
        """Process abstract from raw paper metadata or existing inverted index and persist it."""
        abstract_file = paper_dir / "abstract.txt"
        
        # Check if already present on disk
        if abstract_file.exists():
            existing = safe_read_text(abstract_file).strip()
            if existing:
                return existing

        abstract_text = ""
        # 1. Plain string abstract if provided
        if raw_paper_data.get("abstract") and isinstance(raw_paper_data["abstract"], str):
            abstract_text = raw_paper_data["abstract"].strip()
            
        # 2. Inverted index reconstruction
        if not abstract_text and "abstract_inverted_index" in raw_paper_data:
            abstract_text = reconstruct_abstract(raw_paper_data["abstract_inverted_index"])

        if not abstract_text:
            abstract_text = "Abstract unavailable for this publication."

        atomic_write_text(abstract_file, abstract_text)
        return abstract_text

