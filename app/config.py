"""
PaperGraph V3 - Unified Configuration
Supports all V1/V2 baseline services while extending with V3 OCR & Plugin parameters.
"""
import os
from pathlib import Path
from pydantic import BaseModel
from typing import Optional

class AppConfigV3(BaseModel):
    app_name: str = "PaperGraph"
    version: str = "3.4.0-final"
    default_workspace_dir: str = str(Path.home() / "Documents" / "PaperGraph_Workspace")
    current_workspace_dir: Optional[str] = None
    embedding_model_name: str = "all-MiniLM-L6-v2"
    device: str = "cpu"
    max_graph_nodes: int = 300
    semantic_similarity_threshold: float = 0.35
    cache_ttl_seconds: int = 86400

    # V3 OCR & Model Parameters
    root_dir: str = str(Path(__file__).resolve().parent.parent)
    surya_backend: str = os.getenv("SURYA_OCR_BACKEND", "surya2")
    surya_device: str = os.getenv("SURYA_DEVICE", "cpu")
    models_dir: str = str(Path(__file__).resolve().parent.parent / "models")
    cache_dir: str = str(Path(__file__).resolve().parent.parent / "cache")
    redis_enabled: bool = bool(os.getenv("REDIS_URL"))

    def get_active_workspace(self) -> Path:
        if self.current_workspace_dir:
            return Path(self.current_workspace_dir)
        default_path = Path(self.default_workspace_dir)
        try:
            default_path.mkdir(parents=True, exist_ok=True)
            return default_path
        except Exception:
            fallback = (Path(self.root_dir) / "workspace").resolve()
            fallback.mkdir(parents=True, exist_ok=True)
            return fallback

config = AppConfigV3()
config_v3 = config
