"""
Tests for Backup and Recovery Manager
"""
import pytest
from pathlib import Path
from app.core.backups import BackupManager
from app.core.file_store import atomic_write_text

def test_backup_and_restore(temp_workspace):
    ws_path = temp_workspace.workspace_path
    bm = BackupManager(ws_path)

    # Add a dummy file in library
    test_file = ws_path / "library" / "W123" / "paper.json"
    atomic_write_text(test_file, '{"id": "W123", "title": "Test Paper"}')

    backup_info = bm.create_backup(label="unit_test")
    assert backup_info["filename"].startswith("backup_unit_test_")
    assert (ws_path / "backups" / backup_info["filename"]).exists()

    backups = bm.list_backups()
    assert len(backups) >= 1
    assert backups[0]["filename"] == backup_info["filename"]

    # Delete test file
    test_file.unlink()
    assert not test_file.exists()

    # Restore from backup
    restored = bm.restore_backup(backup_info["filename"])
    assert restored is True
    assert test_file.exists()

