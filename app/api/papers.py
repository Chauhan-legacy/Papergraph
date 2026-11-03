"""
Paper Library and Collection API Routes
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.core.workspace_manager import workspace_manager
from app.services.paper_service import paper_service
from app.services.folder_import_service import folder_import_service
from app.models.schemas import ImportRequest, Collection

router = APIRouter(prefix="/api", tags=["Papers & Collections"])

class NotesUpdateRequest(BaseModel):
    notes: str

class CollectionCreateRequest(BaseModel):
    id: Optional[str] = None
    name: str
    description: str = ""

class FolderScanRequest(BaseModel):
    folder_path: str

class FolderImportRequest(BaseModel):
    folder_path: str
    selected_filenames: Optional[List[str]] = None
    target_collection: Optional[str] = None

@router.get("/papers")
def list_papers(
    q: Optional[str] = None,
    year: Optional[int] = None,
    author: Optional[str] = None,
    topic: Optional[str] = None,
    collection_id: Optional[str] = None,
    sort_by: str = "retrieval_date",
    sort_desc: bool = True
):
    """Retrieve papers matching filter criteria."""
    try:
        papers = paper_service.list_papers(
            query=q,
            year=year,
            author=author,
            topic=topic,
            collection_id=collection_id,
            sort_by=sort_by,
            sort_desc=sort_desc
        )
        return {"total": len(papers), "papers": papers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/papers/{paper_id}")
def get_paper_detail(paper_id: str):
    """Retrieve full paper content, summary, analysis, and notes."""
    detail = workspace_manager.get_paper_detail(paper_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Paper not found.")
    return detail

@router.post("/papers/import")
def import_papers(req: ImportRequest):
    """Import selected papers into the local library."""
    imported = []
    errors = []
    for paper_meta in req.papers:
        try:
            res = paper_service.import_paper(paper_meta.model_dump(), target_collection=req.target_collection)
            imported.append(res)
        except Exception as e:
            errors.append({"paper": paper_meta.title, "error": str(e)})

    return {
        "status": "success",
        "imported_count": len(imported),
        "error_count": len(errors),
        "imported": imported,
        "errors": errors
    }

@router.post("/papers/scan-folder")
def scan_research_folder(req: FolderScanRequest):
    """Scan a local directory for research papers (PDF, TXT, MD, JSON)."""
    try:
        res = folder_import_service.scan_directory(req.folder_path)
        return res
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NotADirectoryError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to scan folder: {str(e)}")

@router.post("/papers/import-folder")
def import_research_folder(req: FolderImportRequest):
    """Import selected files from a local directory into workspace library."""
    try:
        res = folder_import_service.import_selected_files(
            folder_path_str=req.folder_path,
            selected_filenames=req.selected_filenames,
            target_collection=req.target_collection
        )
        return res
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import files: {str(e)}")

@router.put("/papers/{paper_id}/notes")
def update_notes(paper_id: str, req: NotesUpdateRequest):
    """Update user personal notes for a paper."""
    paper_dir = workspace_manager.get_paper_dir(paper_id)
    if not paper_dir.exists():
        raise HTTPException(status_code=404, detail="Paper not found.")
    workspace_manager.save_paper_notes(paper_id, req.notes)
    return {"status": "success", "message": "Notes saved successfully."}

@router.get("/collections")
def list_collections():
    """List all research collections."""
    try:
        return {"collections": workspace_manager.list_collections()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/collections")
def create_or_update_collection(req: CollectionCreateRequest):
    """Create or update a collection."""
    try:
        cid = req.id if req.id else req.name.lower().replace(" ", "_")
        col_data = {
            "id": cid,
            "name": req.name,
            "description": req.description,
            "paper_ids": []
        }
        res = workspace_manager.save_collection(col_data)
        return {"status": "success", "collection": res}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/collections/{collection_id}")
def delete_collection(collection_id: str):
    """Delete a research collection."""
    success = workspace_manager.delete_collection(collection_id)
    if not success:
        raise HTTPException(status_code=404, detail="Collection not found.")
    return {"status": "success", "message": "Collection deleted."}

@router.post("/collections/{collection_id}/papers")
def add_paper_to_collection(collection_id: str, payload: Dict[str, str]):
    """Add a paper to a collection."""
    paper_id = payload.get("paper_id")
    if not paper_id:
        raise HTTPException(status_code=400, detail="Missing paper_id.")
    ok = paper_service.add_paper_to_collection(paper_id, collection_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Paper or collection not found.")
    return {"status": "success"}

@router.delete("/collections/{collection_id}/papers/{paper_id}")
def remove_paper_from_collection(collection_id: str, paper_id: str):
    """Remove a paper from a collection."""
    ok = paper_service.remove_paper_from_collection(paper_id, collection_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Paper not found in collection.")
    return {"status": "success"}

