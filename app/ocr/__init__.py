"""
PaperGraph V3 OCR Package
"""
from .config import ocr_config
from .schemas import PageOCRResult, DocumentOCRResult
from .pipeline import ocr_pipeline
from .surya_backend import surya_backend
from .pymupdf_backend import pymupdf_backend

__all__ = [
    "ocr_config",
    "PageOCRResult",
    "DocumentOCRResult",
    "ocr_pipeline",
    "surya_backend",
    "pymupdf_backend"
]
