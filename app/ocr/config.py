"""
PaperGraph V3 - OCR Pipeline Configuration
Enforces Surya OCR 2 FIRST with PyMuPDF Fallback
"""
import os
from pydantic import BaseModel

class OCRConfig(BaseModel):
    backend: str = os.getenv("SURYA_OCR_BACKEND", "surya2")
    inference_backend: str = os.getenv("SURYA_INFERENCE_BACKEND", "llamacpp")
    device: str = os.getenv("SURYA_DEVICE", "cpu")
    parallel_workers: int = int(os.getenv("SURYA_INFERENCE_PARALLEL", "4"))
    confidence_threshold: float = float(os.getenv("OCR_CONFIDENCE_THRESHOLD", "0.40"))
    timeout_seconds_per_page: int = int(os.getenv("SURYA_TIMEOUT_SECONDS", "60"))
    llama_server_path: str = os.getenv("LLAMA_SERVER_PATH", "llama-server")

ocr_config = OCRConfig()
