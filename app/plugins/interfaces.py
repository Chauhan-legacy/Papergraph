"""
PaperGraph V3 - Plugin Interfaces (Phase 5)
Defines formal extension points for OCR, Embeddings, LLMs, and Report Renderers.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class PluginManifest(BaseModel):
    plugin_id: str
    version: str = "1.0.0"
    capabilities: List[str] = Field(default_factory=list)  # ocr_backend, embedding_model, llm_provider, report_renderer
    entry_point: str
    papergraph_min_version: str = "3.0.0"
    license: str = "MIT"
    enabled: bool = False

class BasePlugin(ABC):
    def __init__(self, manifest: PluginManifest):
        self.manifest = manifest
        self.plugin_id = manifest.plugin_id
        self.failed = False
        self.last_error: Optional[str] = None

class OCRBackendPlugin(BasePlugin):
    @abstractmethod
    def extract(self, pdf_path: str, page_number: int) -> Dict[str, Any]:
        """
        Must return dict with at least:
        {"text": str, "extraction_source": str, "confidence": float}
        """
        pass

class EmbeddingModelPlugin(BasePlugin):
    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        pass

class LLMProviderPlugin(BasePlugin):
    @abstractmethod
    def complete(self, prompt: str, **kwargs) -> str:
        pass

class ReportRendererPlugin(BasePlugin):
    @abstractmethod
    def render(self, analysis_data: Dict[str, Any], output_path: str) -> bool:
        pass

