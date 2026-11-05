"""
PaperGraph V3 - OCR Output & Provenance Schemas
"""
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field

ExtractionSource = Literal["surya_ocr_2", "pymupdf", "ocr_unavailable"]

class PageOCRResult(BaseModel):
    page_number: int
    text: str = ""
    extraction_source: str = "ocr_unavailable"
    ocr_backend_version: Optional[str] = None
    ocr_confidence: Optional[float] = None
    fallback_reason: Optional[str] = None
    layout_blocks: List[Dict[str, Any]] = Field(default_factory=list)
    processing_time_ms: float = 0.0

class DocumentOCRResult(BaseModel):
    document_id: str
    file_path: str
    total_pages: int
    pages: List[PageOCRResult] = Field(default_factory=list)
    full_text: str = ""
    primary_source: str = "surya_ocr_2"
    sha256_hash: str = ""
