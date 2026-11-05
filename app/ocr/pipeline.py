"""
PaperGraph V3 - Unified OCR Pipeline Orchestrator
Strict execution order: Surya OCR 2 -> PyMuPDF fallback -> Plugin -> Unavailable
"""
import os
import hashlib
import logging
from typing import List
from .config import ocr_config
from .schemas import DocumentOCRResult, PageOCRResult
from .surya_backend import surya_backend
from .pymupdf_backend import pymupdf_backend

logger = logging.getLogger("papergraph.v3.ocr.pipeline")

class OCRPipeline:
    def __init__(self, config=ocr_config):
        self.config = config

    def process_document(self, pdf_path: str, total_pages: int = 1) -> DocumentOCRResult:
        pages: List[PageOCRResult] = []
        
        h = hashlib.sha256()
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                while c := f.read(65536): h.update(c)
        pdf_hash = h.hexdigest()

        for p_idx in range(total_pages):
            res = self.process_page(pdf_path, p_idx)
            pages.append(res)

        full_text = "\n\n".join([p.text for p in pages if p.text])
        primary = pages[0].extraction_source if pages else "ocr_unavailable"

        return DocumentOCRResult(
            document_id=os.path.basename(pdf_path),
            file_path=pdf_path,
            total_pages=total_pages,
            pages=pages,
            full_text=full_text,
            primary_source=primary,
            sha256_hash=pdf_hash
        )

    def process_page(self, pdf_path: str, page_number: int) -> PageOCRResult:
        if surya_backend.is_available():
            try:
                res = surya_backend.extract_page(pdf_path, page_number)
                if res and (res.ocr_confidence or 0.0) >= self.config.confidence_threshold:
                    return res
                fallback_reason = "Surya confidence below threshold"
            except Exception as e:
                fallback_reason = f"Surya exception: {e}"
        else:
            fallback_reason = "Surya model files or llama-server not present"

        try:
            return pymupdf_backend.extract_page(pdf_path, page_number, reason=fallback_reason)
        except Exception as e:
            return PageOCRResult(
                page_number=page_number,
                text="",
                extraction_source="ocr_unavailable",
                fallback_reason=f"PyMuPDF failed: {e}"
            )

ocr_pipeline = OCRPipeline()
