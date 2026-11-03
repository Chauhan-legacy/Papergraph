"""
PaperGraph Configuration
"""
from pathlib import Path
from pydantic import BaseModel
from typing import Optional
import os

class AppConfig(BaseModel):
    app_name: str = "PaperGraph"
    version: str = "4.0.0"
    default_workspace_dir: str = str(Path.home() / "Documents" / "PaperGraph_Workspace")
    current_workspace_dir: Optional[str] = None
    embedding_model_name: str = "all-MiniLM-L6-v2"
    device: str = "cpu"
    max_graph_nodes: int = 300
    semantic_similarity_threshold: float = 0.35
    cache_ttl_seconds: int = 86400  # 24 hours

    def get_active_workspace(self) -> Path:
        if self.current_workspace_dir:
            return Path(self.current_workspace_dir)
        # Default or fallback to local directory if Documents is inaccessible
        default_path = Path(self.default_workspace_dir)
        try:
            default_path.mkdir(parents=True, exist_ok=True)
            return default_path
        except Exception:
            fallback = Path("./workspace").resolve()
            fallback.mkdir(parents=True, exist_ok=True)
            return fallback

config = AppConfig()

