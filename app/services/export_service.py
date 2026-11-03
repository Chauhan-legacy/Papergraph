"""
Research Export Service
Exports library papers and syntheses to BibTeX, JSON, CSV, and Markdown reports.
"""
import csv
import json
import io
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.core.workspace_manager import workspace_manager
from app.core.file_store import atomic_write_text, sanitize_id

class ExportService:
    def __init__(self, ws_manager=None):
        self.ws = ws_manager or workspace_manager

    def export(
        self,
        format_type: str,
        paper_ids: Optional[List[str]] = None,
        collection_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate export data and persist file into exports/."""
        all_papers = self.ws.list_all_papers()
        if paper_ids:
            target_papers = [p for p in all_papers if p["id"] in paper_ids]
        elif collection_id:
            target_papers = [p for p in all_papers if collection_id in p.get("collections", [])]
        else:
            target_papers = all_papers

        format_type = format_type.lower().strip()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = self.ws.workspace_path / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)

        if format_type == "bibtex" or format_type == "bib":
            content = self._to_bibtex(target_papers)
            filename = f"export_{timestamp}.bib"
            mime = "application/x-bibtex"
        elif format_type == "csv":
            content = self._to_csv(target_papers)
            filename = f"export_{timestamp}.csv"
            mime = "text/csv"
        elif format_type == "markdown" or format_type == "md":
            content = self._to_markdown(target_papers)
            filename = f"export_{timestamp}.md"
            mime = "text/markdown"
        else:  # default json
            content = json.dumps(target_papers, indent=2, ensure_ascii=False)
            filename = f"export_{timestamp}.json"
            mime = "application/json"

        file_path = export_dir / filename
        atomic_write_text(file_path, content)

        return {
            "filename": filename,
            "filepath": str(file_path),
            "format": format_type,
            "paper_count": len(target_papers),
            "mime_type": mime,
            "content": content
        }

    def _to_bibtex(self, papers: List[Dict[str, Any]]) -> str:
        """Convert papers into standard BibTeX entries."""
        bib_entries = []
        for p in papers:
            p_id = sanitize_id(p.get("id", "entry"))
            title = p.get("title", "Untitled").replace("{", "").replace("}", "")
            year = p.get("publication_year") or "nodate"
            venue = p.get("venue") or "Journal of Academic Research"
            doi = p.get("doi") or ""
            
            # Authors format
            authors = p.get("authors", [])
            names = []
            for a in authors:
                if isinstance(a, dict):
                    names.append(a.get("name", "Unknown"))
                else:
                    names.append(str(a))
            author_str = " and ".join(names) if names else "Anonymous"

            entry = f"""@article{{{p_id},
  title = {{{title}}},
  author = {{{author_str}}},
  journal = {{{venue}}},
  year = {{{year}}},
  doi = {{{doi}}}
}}"""
            bib_entries.append(entry)

        return "\n\n".join(bib_entries)

    def _to_csv(self, papers: List[Dict[str, Any]]) -> str:
        """Convert papers into CSV format."""
        output = io.StringIO()
        fieldnames = ["id", "title", "authors", "year", "venue", "doi", "citations", "status", "url"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for p in papers:
            authors = p.get("authors", [])
            names = []
            for a in authors:
                if isinstance(a, dict):
                    names.append(a.get("name", "Unknown"))
                else:
                    names.append(str(a))
            writer.writerow({
                "id": p.get("id"),
                "title": p.get("title"),
                "authors": "; ".join(names),
                "year": p.get("publication_year"),
                "venue": p.get("venue"),
                "doi": p.get("doi"),
                "citations": p.get("citation_count", 0),
                "status": p.get("processing_status"),
                "url": p.get("source_url")
            })

        return output.getvalue()

    def _to_markdown(self, papers: List[Dict[str, Any]]) -> str:
        """Generate comprehensive Markdown research summary catalog."""
        lines = [
            f"# Research Literature Export",
            f"Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by PaperGraph",
            f"**Total Papers**: {len(papers)}\n",
            "---",
            ""
        ]

        for idx, p in enumerate(papers, 1):
            title = p.get("title", "Untitled")
            year = p.get("publication_year", "N/A")
            venue = p.get("venue", "Unknown Venue")
            doi = p.get("doi", "N/A")
            citations = p.get("citation_count", 0)
            status = p.get("processing_status", "Imported")
            
            authors = p.get("authors", [])
            names = [a.get("name") if isinstance(a, dict) else str(a) for a in authors]
            author_str = ", ".join(names[:5]) + (" et al." if len(names) > 5 else "")

            lines.append(f"### {idx}. {title}")
            lines.append(f"- **Authors**: {author_str}")
            lines.append(f"- **Publication**: {venue} ({year}) | **Citations**: {citations}")
            lines.append(f"- **DOI**: {doi} | **Status**: `{status}`")
            
            # Check if summary is available
            d = self.ws.get_paper_detail(p["id"])
            if d and d.get("summary"):
                lines.append(f"\n#### Structured Overview\n{d['summary'][:400]}...\n")
            lines.append("\n---\n")

        return "\n".join(lines)

export_service = ExportService()

