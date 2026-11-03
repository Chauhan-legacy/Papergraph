"""
OpenAlex Literature Provider Implementation
Provides robust search, cursor pagination, retries, exponential backoff, caching, and abstract reconstruction.
"""
import time
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests

from app.providers.provider_base import LiteratureProvider
from app.core.file_store import safe_read_json, atomic_write_json
from app.config import config

logger = logging.getLogger("papergraph.openalex")

def reconstruct_abstract(inverted_index: Optional[Dict[str, List[int]]]) -> str:
    """Reconstruct plain-text abstract from OpenAlex inverted index."""
    if not inverted_index or not isinstance(inverted_index, dict):
        return ""
    pos_map = {}
    for word, positions in inverted_index.items():
        if isinstance(positions, list):
            for pos in positions:
                pos_map[pos] = word
    if not pos_map:
        return ""
    sorted_positions = sorted(pos_map.keys())
    return " ".join(pos_map[p] for p in sorted_positions).strip()

class OpenAlexProvider(LiteratureProvider):
    BASE_URL = "https://api.openalex.org/works"
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "PaperGraph/4.0 (Research Platform; mailto:contact@papergraph.local)"
        })
        self.cache_dir = cache_dir

    @property
    def provider_name(self) -> str:
        return "openalex"

    def _get_cache_path(self, cache_key: str) -> Optional[Path]:
        if not self.cache_dir:
            ws_path = config.get_active_workspace()
            self.cache_dir = ws_path / "cache" / "openalex"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        h = hashlib.sha256(cache_key.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{h}.json"

    def _request_with_retry(self, url: str, params: Dict[str, Any], max_retries: int = 3) -> Dict[str, Any]:
        """Perform HTTP GET with exponential backoff and rate limit handling."""
        cache_key = f"{url}?{json.dumps(params, sort_keys=True)}"
        cache_file = self._get_cache_path(cache_key)
        
        if cache_file and cache_file.exists():
            cached = safe_read_json(cache_file)
            if cached:
                return cached

        delay = 1.0
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=12.0)
                if response.status_code == 200:
                    data = response.json()
                    if cache_file:
                        atomic_write_json(cache_file, data)
                    return data
                elif response.status_code == 429:
                    # Rate limited: back off longer
                    retry_after = float(response.headers.get("Retry-After", delay * 2))
                    time.sleep(retry_after)
                    delay *= 2
                elif 500 <= response.status_code < 600:
                    time.sleep(delay)
                    delay *= 2
                else:
                    logger.warning(f"OpenAlex returned HTTP {response.status_code}: {response.text[:200]}")
                    return {"results": [], "meta": {"count": 0, "page": 1, "per_page": params.get("per-page", 20)}}
            except (requests.exceptions.RequestException, Exception) as exc:
                logger.warning(f"Request error (attempt {attempt+1}/{max_retries}): {exc}")
                if attempt == max_retries - 1:
                    return {"results": [], "meta": {"count": 0, "page": 1, "per_page": params.get("per-page", 20)}, "error": str(exc)}
                time.sleep(delay)
                delay *= 2

        return {"results": [], "meta": {"count": 0}}

    def search(
        self,
        query: str,
        filter_type: str = "all",
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        page: int = 1,
        per_page: int = 20,
        sort: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search OpenAlex works API with filters."""
        params: Dict[str, Any] = {
            "per-page": min(max(1, per_page), 100),
            "page": max(1, page)
        }

        # Filter criteria
        filter_parts = []
        if year_min and year_max:
            filter_parts.append(f"publication_year:{year_min}-{year_max}")
        elif year_min:
            filter_parts.append(f"from_publication_date:{year_min}-01-01")
        elif year_max:
            filter_parts.append(f"to_publication_date:{year_max}-12-31")

        query_str = query.strip()
        if filter_type == "doi" or query_str.startswith("10.") or "doi.org" in query_str:
            doi = query_str.replace("https://doi.org/", "").replace("http://doi.org/", "").strip()
            filter_parts.append(f"doi:{doi}")
        elif filter_type == "author":
            filter_parts.append(f"raw_author_name.search:{query_str}")
        elif filter_type == "title":
            filter_parts.append(f"title.search:{query_str}")
        elif filter_type == "topic":
            filter_parts.append(f"default.search:{query_str}")
        else:
            if query_str:
                params["search"] = query_str

        if filter_parts:
            params["filter"] = ",".join(filter_parts)

        if sort:
            params["sort"] = sort
        else:
            params["sort"] = "relevance_score:desc"

        raw_data = self._request_with_retry(self.BASE_URL, params)
        return self._format_results(raw_data)

    def get_paper_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve single paper directly from OpenAlex by ID or DOI."""
        clean_id = paper_id.strip()
        if not clean_id.startswith("http") and not clean_id.startswith("W"):
            clean_id = f"https://openalex.org/{clean_id}"
            
        url = f"{self.BASE_URL}/{clean_id}"
        raw_data = self._request_with_retry(url, {})
        if raw_data and "id" in raw_data:
            return self._standardize_work(raw_data)
        return None

    def _format_results(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert OpenAlex API response into standardized PaperGraph items."""
        raw_results = raw_data.get("results", [])
        meta = raw_data.get("meta", {})
        
        standardized_papers = []
        for work in raw_results:
            paper = self._standardize_work(work)
            if paper:
                standardized_papers.append(paper)

        return {
            "total_count": meta.get("count", len(standardized_papers)),
            "page": meta.get("page", 1),
            "per_page": meta.get("per_page", len(standardized_papers)),
            "papers": standardized_papers
        }

    def _standardize_work(self, work: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize a single OpenAlex work record."""
        # Extract authors
        authors = []
        for authorship in work.get("authorships", []):
            author_obj = authorship.get("author", {})
            name = author_obj.get("display_name") or "Unknown Author"
            institutions = authorship.get("institutions", [])
            inst_name = institutions[0].get("display_name") if institutions else None
            orcid = author_obj.get("orcid")
            authors.append({
                "name": name,
                "institution": inst_name,
                "orcid": orcid
            })

        # Venue / journal
        venue = "Unknown Venue"
        primary_loc = work.get("primary_location") or {}
        source = primary_loc.get("source") or {}
        if source.get("display_name"):
            venue = source.get("display_name")
        elif work.get("host_venue", {}).get("display_name"):
            venue = work.get("host_venue", {}).get("display_name")

        # Abstract reconstruction
        inverted_index = work.get("abstract_inverted_index")
        abstract_text = reconstruct_abstract(inverted_index)

        # ID extraction
        raw_id = work.get("id", "")
        short_id = raw_id.split("/")[-1] if "/" in raw_id else raw_id
        if not short_id:
            short_id = f"work_{abs(hash(work.get('title', 'untitled')))}"

        landing_page = primary_loc.get("landing_page_url") or work.get("doi") or raw_id

        # Referenced works (OpenAlex work IDs)
        referenced_works = [r.split("/")[-1] for r in work.get("referenced_works", []) if r]

        return {
            "id": short_id,
            "openalex_id": raw_id,
            "doi": work.get("doi"),
            "title": work.get("title") or "Untitled Publication",
            "authors": authors,
            "publication_year": work.get("publication_year"),
            "publication_date": work.get("publication_date"),
            "venue": venue,
            "source_provider": "openalex",
            "source_url": landing_page,
            "citation_count": work.get("cited_by_count", 0),
            "referenced_works": referenced_works,
            "abstract": abstract_text,
            "abstract_available": bool(abstract_text.strip()),
            "processing_status": "Discovered"
        }

