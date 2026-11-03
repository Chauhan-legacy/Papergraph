"""
AI Engine Configuration API Routes
"""
from fastapi import APIRouter, HTTPException
from app.models.schemas import AIProviderConfig
from app.providers.ai_provider import ai_provider_manager
from app.core.workspace_manager import workspace_manager
from app.core.file_store import safe_read_json, atomic_write_json

router = APIRouter(prefix="/api/ai", tags=["AI Engine"])

@router.get("/config")
def get_ai_config():
    """Retrieve current AI engine settings."""
    try:
        ws_info = workspace_manager.get_info()
        settings = ws_info.get("settings", {}).get("ai_config") if isinstance(ws_info, dict) else getattr(ws_info, "settings", {}).get("ai_config")
        if settings:
            return settings
    except Exception:
        pass
    return ai_provider_manager.config.model_dump()

@router.post("/config")
def set_ai_config(config: AIProviderConfig):
    """Update AI engine configuration."""
    try:
        ai_provider_manager.set_config(config)
        # Persist to workspace.json settings
        ws_file = workspace_manager.workspace_path / "workspace.json"
        if ws_file.exists():
            metadata = safe_read_json(ws_file, {})
            metadata.setdefault("settings", {})["ai_config"] = config.model_dump()
            atomic_write_json(ws_file, metadata)
        return {"success": True, "active_provider": ai_provider_manager.get_active_provider_name(), "config": config.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-connection")
def test_ai_connection():
    """Test connectivity to configured AI engine."""
    try:
        return ai_provider_manager.test_connection()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
