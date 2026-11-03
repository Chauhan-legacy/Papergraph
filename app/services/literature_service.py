"""
Literature Discovery Service
Integrates OpenAlex with fallback handling, caching, and existing library cross-referencing.
"""
from typing import Dict, Any, List, Optional
from app.providers.openalex import OpenAlexProvider
from app.core.workspace_manager import workspace_manager
from app.models.schemas import SearchQuery

class LiteratureService:
    def __init__(self, provider=None, ws_manager=None):
        self.provider = provider or OpenAlexProvider()
        self.ws = ws_manager or workspace_manager

    def search_literature(self, query_model: SearchQuery) -> Dict[str, Any]:
        """Perform search and flag already imported papers."""
        raw_results = self.provider.search(
            query=query_model.query,
            filter_type=query_model.filter_type,
            year_min=query_model.year_min,
            year_max=query_model.year_max,
            page=query_model.page,
            per_page=query_model.per_page,
            sort=query_model.sort
        )

        existing_papers = self.ws.list_all_papers()
        existing_ids = {p["id"] for p in existing_papers}
        existing_dois = {(p.get("doi") or "").lower().strip() for p in existing_papers if p.get("doi")}
        existing_titles = {p.get("title", "").lower().strip() for p in existing_papers if p.get("title")}

        papers = raw_results.get("papers", [])
        for p in papers:
            p_id = p.get("id")
            p_doi = (p.get("doi") or "").lower().strip()
            p_title = (p.get("title") or "").lower().strip()

            is_imported = (
                p_id in existing_ids or
                (p_doi and p_doi in existing_dois) or
                (p_title and p_title in existing_titles)
            )
            p["already_in_library"] = is_imported

        return raw_results

literature_service = LiteratureService()

