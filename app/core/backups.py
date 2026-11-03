"""
Backup and Recovery Manager for PaperGraph Workspaces
"""
import os
import zipfile
import datetime
from pathlib import Path
from typing import List, Dict, Any

class BackupManager:
    def __init__(self, workspace_path: Path):
        self.workspace_path = Path(workspace_path)
        self.backups_dir = self.workspace_path / "backups"
        self.backups_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, label: str = "manual") -> Dict[str, Any]:
        """Create a zip snapshot of the research library and collections."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{label}_{timestamp}.zip"
        backup_path = self.backups_dir / backup_filename
        
        items_to_backup = [
            self.workspace_path / "workspace.json",
            self.workspace_path / "library",
            self.workspace_path / "collections"
        ]
        
        with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for item in items_to_backup:
                if not item.exists():
                    continue
                if item.is_file():
                    zf.write(item, arcname=item.name)
                elif item.is_dir():
                    for root, _, files in os.walk(item):
                        for file in files:
                            full_path = Path(root) / file
                            # skip temp files or logs
                            if full_path.suffix in [".tmp", ".log"]:
                                continue
                            rel_path = full_path.relative_to(self.workspace_path)
                            zf.write(full_path, arcname=str(rel_path))
                            
        stat = backup_path.stat()
        return {
            "filename": backup_filename,
            "path": str(backup_path),
            "size_bytes": stat.st_size,
            "created_at": datetime.datetime.now().isoformat()
        }

    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backup archives."""
        if not self.backups_dir.exists():
            return []
        
        backups = []
        for f in sorted(self.backups_dir.glob("backup_*.zip"), reverse=True):
            stat = f.stat()
            backups.append({
                "filename": f.name,
                "path": str(f),
                "size_bytes": stat.st_size,
                "created_at": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        return backups

    def restore_backup(self, backup_filename: str) -> bool:
        """Safely restore a backup into the workspace."""
        backup_path = self.backups_dir / backup_filename
        if not backup_path.exists() or not backup_path.is_file():
            return False
            
        with zipfile.ZipFile(backup_path, "r") as zf:
            zf.extractall(self.workspace_path)
        return True
