"""
Paper Management and Library Service
Provides deduplication, library browsing, filtering, sorting, notes editing, and collection assignment.
"""
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.core.workspace_manager import workspace_manager
from app.core.file_store import atomic_write_json, sanitize_id
from app.core.validation import normalize_title, validate_paper_metadata
from app.models.schemas import PaperMetadata

class PaperService:
    def __init__(self, ws_manager=None):
        self.ws = ws_manager or workspace_manager

    def find_duplicate(self, paper_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect if paper already exists in library by DOI, OpenAlex ID, or Title."""
        existing_papers = self.ws.list_all_papers()
        incoming_id = paper_data.get("id")
        incoming_doi = (paper_data.get("doi") or "").lower().strip()
        incoming_oa = (paper_data.get("openalex_id") or "").lower().strip()
        incoming_title_norm = normalize_title(paper_data.get("title", ""))

        for p in existing_papers:
            # 1. Exact ID match
            if incoming_id and p.get("id") == incoming_id:
                return p
            # 2. DOI match
            p_doi = (p.get("doi") or "").lower().strip()
            if incoming_doi and p_doi and incoming_doi == p_doi:
                return p
            # 3. OpenAlex ID match
            p_oa = (p.get("openalex_id") or "").lower().strip()
            if incoming_oa and p_oa and incoming_oa == p_oa:
                return p
            # 4. Normalized title match
            p_title_norm = normalize_title(p.get("title", ""))
            if incoming_title_norm and p_title_norm and incoming_title_norm == p_title_norm:
                return p

        return None

    def import_paper(self, paper_data: Dict[str, Any], target_collection: Optional[str] = None) -> Dict[str, Any]:
        """Import a paper into workspace library, creating files and folders."""
        valid, err = validate_paper_metadata(paper_data)
        if not valid:
            raise ValueError(f"Invalid paper metadata: {err}")

        # Check duplicate
        existing = self.find_duplicate(paper_data)
        if existing:
            # If target_collection is specified, ensure it is added to existing paper
            if target_collection:
                self.add_paper_to_collection(existing["id"], target_collection)
            return existing

        paper_id = sanitize_id(paper_data["id"])
        paper_dir = self.ws.get_paper_dir(paper_id)
        paper_dir.mkdir(parents=True, exist_ok=True)

        now_str = datetime.datetime.now().isoformat()
        metadata = dict(paper_data)
        metadata["id"] = paper_id
        metadata["retrieval_date"] = now_str
        metadata["processing_status"] = "Imported"
        
        collections = metadata.get("collections", [])
        if target_collection and target_collection not in collections:
            collections.append(target_collection)
        metadata["collections"] = collections

        # Write paper.json
        self.ws.save_paper_metadata(paper_id, metadata)

        # Update collection file if applicable
        if target_collection:
            self._update_collection_membership(target_collection, paper_id, add=True)

        return metadata

    def list_papers(
        self,
        query: Optional[str] = None,
        year: Optional[int] = None,
        author: Optional[str] = None,
        topic: Optional[str] = None,
        collection_id: Optional[str] = None,
        sort_by: str = "retrieval_date",
        sort_desc: bool = True
    ) -> List[Dict[str, Any]]:
        """List and filter papers from the workspace library."""
        papers = self.ws.list_all_papers()
        results = []

        q_lower = query.lower().strip() if query else None
        auth_lower = author.lower().strip() if author else None
        topic_lower = topic.lower().strip() if topic else None

        for p in papers:
            # Collection filter
            if collection_id and collection_id not in p.get("collections", []):
                continue

            # Year filter
            if year is not None and p.get("publication_year") != year:
                continue

            # Query filter (title, venue, doi)
            if q_lower:
                title = p.get("title", "").lower()
                venue = p.get("venue", "").lower()
                doi = (p.get("doi") or "").lower()
                if q_lower not in title and q_lower not in venue and q_lower not in doi:
                    continue

            # Author filter
            if auth_lower:
                authors = p.get("authors", [])
                match = False
                for a in authors:
                    name = a.get("name", "") if isinstance(a, dict) else str(a)
                    if auth_lower in name.lower():
                        match = True
                        break
                if not match:
                    continue

            # Topic filter
            if topic_lower:
                p_topics = [t.lower() for t in p.get("topics", [])]
                if not any(topic_lower in t for t in p_topics):
                    continue

            results.append(p)

        # Sorting
        def sort_key(item):
            if sort_by == "title":
                return item.get("title", "").lower()
            elif sort_by == "year":
                return item.get("publication_year") or 0
            elif sort_by == "citations":
                return item.get("citation_count") or 0
            else:
                return item.get("retrieval_date") or ""

        results.sort(key=sort_key, reverse=sort_desc)
        return results

    def add_paper_to_collection(self, paper_id: str, collection_id: str) -> bool:
        """Add a paper to a collection."""
        paper_dir = self.ws.get_paper_dir(paper_id)
        if not paper_dir.exists():
            return False
            
        p = self.ws.get_paper_detail(paper_id)
        if not p or not p.get("metadata"):
            return False

        meta = p["metadata"]
        cols = meta.get("collections", [])
        if collection_id not in cols:
            cols.append(collection_id)
            meta["collections"] = cols
            self.ws.save_paper_metadata(paper_id, meta)

        self._update_collection_membership(collection_id, paper_id, add=True)
        return True

    def remove_paper_from_collection(self, paper_id: str, collection_id: str) -> bool:
        """Remove a paper from a collection."""
        p = self.ws.get_paper_detail(paper_id)
        if not p or not p.get("metadata"):
            return False

        meta = p["metadata"]
        cols = meta.get("collections", [])
        if collection_id in cols:
            cols.remove(collection_id)
            meta["collections"] = cols
            self.ws.save_paper_metadata(paper_id, meta)

        self._update_collection_membership(collection_id, paper_id, add=False)
        return True

    def _update_collection_membership(self, collection_id: str, paper_id: str, add: bool = True):
        """Update collection file with paper id."""
        cols = self.ws.list_collections()
        for col in cols:
            if col["id"] == collection_id:
                p_ids = set(col.get("paper_ids", []))
                if add:
                    p_ids.add(paper_id)
                else:
                    p_ids.discard(paper_id)
                col["paper_ids"] = list(p_ids)
                self.ws.save_collection(col)
                break

paper_service = PaperService()

