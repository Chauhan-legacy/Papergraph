"""
Workspace Management API Routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from pathlib import Path

from app.core.workspace_manager import workspace_manager
from app.core.backups import BackupManager

router = APIRouter(prefix="/api/workspace", tags=["Workspace"])

class CreateWorkspaceRequest(BaseModel):
    path: Optional[str] = None
    name: str = "My Research Workspace"

class OpenWorkspaceRequest(BaseModel):
    path: str

class RestoreRequest(BaseModel):
    filename: str

@router.get("/status")
def get_workspace_status():
    """Return active workspace status and statistics."""
    try:
        return workspace_manager.get_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create")
def create_workspace(req: CreateWorkspaceRequest):
    """Create a new workspace at target path."""
    try:
        path = Path(req.path) if req.path else None
        info = workspace_manager.create_workspace(path=path, name=req.name)
        return info
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/open")
def open_workspace(req: OpenWorkspaceRequest):
    """Open and validate an existing workspace directory."""
    try:
        path = Path(req.path)
        info = workspace_manager.open_workspace(path)
        return info
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/backup")
def trigger_backup():
    """Create a timestamped zip backup of the current workspace."""
    try:
        bm = BackupManager(workspace_manager.workspace_path)
        backup_info = bm.create_backup(label="manual")
        return {"status": "success", "backup": backup_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/backups")
def list_backups():
    """List available backups."""
    try:
        bm = BackupManager(workspace_manager.workspace_path)
        return {"backups": bm.list_backups()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/restore")
def restore_backup(req: RestoreRequest):
    """Restore from a backup archive."""
    try:
        bm = BackupManager(workspace_manager.workspace_path)
        success = bm.restore_backup(req.filename)
        if not success:
            raise HTTPException(status_code=404, detail="Backup file not found or invalid.")
        return {"status": "success", "message": f"Restored {req.filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rebuild-index")
def rebuild_index():
    """Rescan all workspace files directly."""
    try:
        info = workspace_manager.get_info()
        return {"status": "success", "workspace": info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

