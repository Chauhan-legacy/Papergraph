"""
PaperGraph V3 - API Routes
Exposes endpoints for OCR execution, 4-Pass Analysis, Corpus Search, Plugins, and Hypotheses.
"""
from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from typing import List, Optional, Dict, Any

from app.ocr.pipeline import ocr_pipeline
from app.analysis.pipeline import analysis_pipeline
from app.search.corpus_search import corpus_search
from app.plugins.registry import plugin_registry
from app.lab.hypothesis_lab import hypothesis_lab, report_studio
from app.core.redis_backend import redis_backend
from app.core.job_manager import job_manager

api_router = APIRouter(prefix="/api/v3", tags=["V3 Core"])

@api_router.get("/status")
def get_v3_status():
    return {
        "status": "healthy",
        "engine": "PaperGraph V3",
        "version": "3.4.0-final",
        "architecture": {
            "ocr_primary": "Surya OCR 2 (CPU/llamacpp)",
            "ocr_fallback": "PyMuPDF",
            "analysis_pass1": "Pattern Recognition (Deterministic/Zero-Model)",
            "analysis_pass2": "Qwen2.5-0.5B GGUF INT4 (Optional Small Model)",
            "plugins": plugin_registry.list_plugins(),
            "redis_connected": redis_backend.is_connected
        }
    }

@api_router.post("/ocr/process")
def process_ocr(pdf_path: str, page_number: int = 0):
    try:
        res = ocr_pipeline.process_page(pdf_path, page_number)
        job_manager.record_page_complete(job_id=pdf_path, page_number=page_number)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/analysis/analyze")
def analyze_text(paper_id: str, text: str, page_number: int = 0, extraction_source: str = "pymupdf"):
    try:
        pages = [{"page_number": page_number, "text": text, "extraction_source": extraction_source}]
        report = analysis_pipeline.analyze_document(paper_id, pages)
        corpus_search.index_document(paper_id, paper_id, report.claims)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/search")
def search_corpus(query: str, top_k: int = 10):
    return corpus_search.search(query, top_k)

@api_router.get("/graph")
def get_graph():
    return corpus_search.build_knowledge_graph()

@api_router.post("/hypothesis/synthesize")
def synthesize_hypothesis(topic: str):
    return hypothesis_lab.synthesize_hypothesis(topic, [])

@api_router.get("/plugins")
def list_plugins():
    return plugin_registry.list_plugins()

@api_router.post("/plugins/register")
def register_plugin(manifest: Dict[str, Any]):
    ok = plugin_registry.register_manifest(manifest)
    if not ok:
        raise HTTPException(status_code=400, detail="Invalid plugin manifest")
    return {"status": "registered", "manifest": manifest}

