"""
PaperGraph V3 - PyMuPDF Text Extractor (Fallback)
Lightweight, deterministic fallback without ML dependencies
"""
import logging
import time
from typing import Optional
from .schemas import PageOCRResult

logger = logging.getLogger("papergraph.v3.ocr.pymupdf")

class PyMuPDFBackend:
    def __init__(self):
        self.version = "1.24.0"

    def extract_page(self, pdf_path: str, page_number: int, reason: str = "Surya unavailable") -> PageOCRResult:
        t0 = time.time()
        extracted_text = ""
        try:
            import fitz
            doc = fitz.open(pdf_path)
            if 0 <= page_number < len(doc):
                extracted_text = doc[page_number].get_text()
            doc.close()
        except ImportError:
            try:
                from pypdf import PdfReader
                reader = PdfReader(pdf_path)
                if 0 <= page_number < len(reader.pages):
                    extracted_text = reader.pages[page_number].extract_text() or ""
            except Exception as e:
                logger.warning(f"Fallback extraction failed: {e}")
        except Exception as e:
            logger.warning(f"PyMuPDF extraction failed: {e}")

        dt = (time.time() - t0) * 1000
        return PageOCRResult(
            page_number=page_number,
            text=extracted_text,
            extraction_source="pymupdf",
            ocr_backend_version=self.version,
            ocr_confidence=0.85 if extracted_text else 0.0,
            fallback_reason=reason,
            processing_time_ms=dt
        )

pymupdf_backend = PyMuPDFBackend()
