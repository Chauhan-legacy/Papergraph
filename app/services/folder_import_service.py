"""
Folder Import Service for PaperGraph
Discovers, inspects, extracts, and imports research papers (PDF, TXT, MD, JSON)
from a user-specified local directory without modifying the original files.
"""
import os
import re
import shutil
import hashlib
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pypdf

from app.core.workspace_manager import workspace_manager
from app.core.file_store import sanitize_id, atomic_write_json, atomic_write_text
from app.core.validation import normalize_title
from app.models.schemas import PaperMetadata

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".json"}

class FolderImportService:
    def __init__(self, ws_manager=None):
        self.ws = ws_manager or workspace_manager

    @staticmethod
    def _compute_file_hash(file_path: Path) -> str:
        """Compute SHA-256 hash of a file for exact duplicate detection."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    @staticmethod
    def _extract_doi_from_text(text: str) -> Optional[str]:
        """Extract standard academic DOI pattern from text."""
        doi_regex = r"\b(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)\b"
        match = re.search(doi_regex, text)
        if match:
            clean = match.group(1).rstrip(".,;")
            return clean
        return None

    @staticmethod
    def _extract_year_from_text(text: str) -> Optional[int]:
        """Extract plausible 4-digit publication year (1950 - 2030) from text."""
        year_matches = re.findall(r"\b(19[5-9]\d|20[0-2]\d|2030)\b", text[:2000])
        if year_matches:
            try:
                return int(year_matches[0])
            except ValueError:
                pass
        return None

    def _extract_pdf_info(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata, text, and structure from a PDF file using pypdf."""
        title = ""
        authors = []
        year = None
        doi = None
        full_text = ""
        abstract = ""
        page_count = 0
        is_scanned = False

        try:
            reader = pypdf.PdfReader(str(file_path))
            page_count = len(reader.pages)

            # 1. Read document metadata
            doc_info = reader.metadata or {}
            meta_title = doc_info.get("/Title")
            meta_author = doc_info.get("/Author")
            meta_date = doc_info.get("/CreationDate")

            if meta_title and len(meta_title.strip()) > 4 and "untitled" not in meta_title.lower():
                title = meta_title.strip()

            if meta_author and len(meta_author.strip()) > 1:
                authors = [a.strip() for a in re.split(r"[,;]|\band\b", meta_author) if a.strip()]

            if meta_date:
                match = re.search(r"D:(\d{4})", str(meta_date))
                if match:
                    year = int(match.group(1))

            # 2. Extract text from pages (up to 50 pages for performance)
            extracted_pages = []
            for i, page in enumerate(reader.pages[:50]):
                page_text = page.extract_text() or ""
                extracted_pages.append(page_text)

            full_text = "\n\n".join(extracted_pages).strip()

            if not full_text or len(full_text) < 50:
                is_scanned = True
                full_text = "Text extraction yielded minimal content. This PDF may be a scanned image or contain non-standard fonts."
            else:
                first_page = extracted_pages[0] if extracted_pages else ""

                # Extract DOI from first page
                doi = self._extract_doi_from_text(first_page) or self._extract_doi_from_text(full_text[:3000])

                # Extract year if not already found in metadata
                if not year:
                    year = self._extract_year_from_text(first_page)

                # Title heuristic if metadata title missing
                if not title:
                    lines = [line.strip() for line in first_page.split("\n") if len(line.strip()) > 3]
                    # Filter out header garbage, page numbers, or URLs
                    candidate_lines = []
                    for line in lines[:10]:
                        if not re.match(r"^(http|doi|volume|issue|arxiv|issn|isbn|page|\d+)", line, re.I):
                            candidate_lines.append(line)
                    if candidate_lines:
                        # Join first 1-2 candidate lines
                        title = " ".join(candidate_lines[:2])
                        if len(title) > 180:
                            title = candidate_lines[0]

                # Abstract heuristic from first 2 pages
                first_pages_text = "\n".join(extracted_pages[:2])
                abstract_match = re.search(r"\babstract\b[:\s\n]*(.+?)(?=\b(introduction|1\.\s+introduction|keywords|index terms)\b|\n\n\n)", first_pages_text, re.I | re.S)
                if abstract_match:
                    abstract = abstract_match.group(1).strip()
                    # Clean up multiple whitespaces
                    abstract = re.sub(r"\s+", " ", abstract)
                    if len(abstract) > 3000:
                        abstract = abstract[:3000]

        except Exception as e:
            full_text = f"PDF extraction error: {str(e)}"
            is_scanned = True

        if not title:
            # Fallback to file stem
            title = file_path.stem.replace("_", " ").replace("-", " ").title()

        if not authors:
            authors = ["Unknown Author"]

        return {
            "title": title,
            "authors": authors,
            "publication_year": year,
            "doi": doi,
            "page_count": page_count,
            "is_scanned": is_scanned,
            "abstract": abstract,
            "full_text": full_text,
            "extraction_mode": "full_text" if not is_scanned and len(full_text) > 300 else "metadata_only"
        }

    def _extract_text_info(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata and text from a TXT or Markdown file."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace").strip()
        except Exception as e:
            content = f"Error reading text file: {e}"

        title = ""
        abstract = ""
        authors = ["Unknown Author"]
        doi = self._extract_doi_from_text(content[:2000])
        year = self._extract_year_from_text(content[:2000])

        lines = [line.strip() for line in content.split("\n") if line.strip()]
        if lines:
            # Check Markdown header
            first_line = lines[0].lstrip("#").strip()
            if first_line:
                title = first_line

        if not title:
            title = file_path.stem.replace("_", " ").replace("-", " ").title()

        # Look for abstract section
        abstract_match = re.search(r"\babstract\b[:\s\n]*(.+?)(?=\n#|\n\n\n|\bintroduction\b)", content, re.I | re.S)
        if abstract_match:
            abstract = re.sub(r"\s+", " ", abstract_match.group(1).strip())[:2500]
        else:
            # Use first paragraph as abstract candidate
            paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 40]
            if len(paragraphs) > 1:
                abstract = paragraphs[1][:1500]

        return {
            "title": title,
            "authors": authors,
            "publication_year": year,
            "doi": doi,
            "page_count": max(1, len(content) // 2500),
            "is_scanned": False,
            "abstract": abstract,
            "full_text": content,
            "extraction_mode": "full_text"
        }

    def _extract_json_info(self, file_path: Path) -> Dict[str, Any]:
        """Extract paper metadata from a JSON file."""
        import json
        try:
            data = json.loads(file_path.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            data = {}

        title = data.get("title") or file_path.stem.replace("_", " ").title()
        authors = data.get("authors", ["Unknown Author"])
        if isinstance(authors, str):
            authors = [authors]
        elif isinstance(authors, list):
            authors = [(a.get("name") if isinstance(a, dict) else str(a)) for a in authors]

        year = data.get("publication_year") or data.get("year")
        doi = data.get("doi")
        abstract = data.get("abstract", "")
        full_text = data.get("full_text", "") or abstract

        return {
            "title": title,
            "authors": authors,
            "publication_year": year,
            "doi": doi,
            "page_count": data.get("page_count", 1),
            "is_scanned": False,
            "abstract": abstract,
            "full_text": full_text,
            "extraction_mode": "metadata_only" if not full_text else "full_text"
        }

    def scan_directory(self, folder_path_str: str) -> Dict[str, Any]:
        """
        Scan a user-selected folder without modifying files.
        Returns discovered files with duplicate detection, metadata candidates, and format support.
        """
        folder_path = Path(folder_path_str).resolve()
        if not folder_path.exists():
            raise FileNotFoundError(f"Directory does not exist: {folder_path_str}")
        if not folder_path.is_dir():
            raise NotADirectoryError(f"Provided path is not a directory: {folder_path_str}")

        existing_papers = self.ws.list_all_papers()
        existing_hashes = set()
        existing_titles_norm = set()
        existing_dois = set()

        for p in existing_papers:
            if p.get("file_hash"):
                existing_hashes.add(p["file_hash"])
            if p.get("title"):
                existing_titles_norm.add(normalize_title(p["title"]))
            if p.get("doi"):
                existing_dois.add(p["doi"].lower().strip())

        discovered_papers = []
        unsupported_files = []
        already_imported_count = 0

        # Scan files in directory (top level and immediate subdirs)
        for root, dirs, files in os.walk(folder_path):
            # Limit depth to avoid scanning huge nested drives
            rel_depth = len(Path(root).relative_to(folder_path).parts)
            if rel_depth > 2:
                continue

            for fname in sorted(files):
                fpath = Path(root) / fname
                ext = fpath.suffix.lower()

                if ext not in SUPPORTED_EXTENSIONS:
                    # Ignore system/hidden files
                    if not fname.startswith(".") and not fname.startswith("~"):
                        unsupported_files.append({
                            "filename": fname,
                            "path": str(fpath),
                            "extension": ext or "none",
                            "reason": f"Unsupported file format '{ext}'. Supported: PDF, TXT, MD, JSON."
                        })
                    continue

                try:
                    fsize = fpath.stat().st_size
                except Exception:
                    fsize = 0

                # Fast preview extraction based on format
                if ext == ".pdf":
                    info = self._extract_pdf_info(fpath)
                elif ext in {".txt", ".md"}:
                    info = self._extract_text_info(fpath)
                elif ext == ".json":
                    info = self._extract_json_info(fpath)
                else:
                    continue

                # Check duplicate status
                is_duplicate = False
                dup_reason = ""

                norm_title = normalize_title(info["title"])
                if norm_title in existing_titles_norm:
                    is_duplicate = True
                    dup_reason = "Title matches an existing paper in library"

                if info.get("doi") and info["doi"].lower().strip() in existing_dois:
                    is_duplicate = True
                    dup_reason = "DOI matches an existing paper in library"

                if is_duplicate:
                    already_imported_count += 1

                discovered_papers.append({
                    "filename": fname,
                    "relative_path": str(fpath.relative_to(folder_path)),
                    "absolute_path": str(fpath),
                    "file_size": fsize,
                    "file_size_formatted": self._format_size(fsize),
                    "extension": ext,
                    "title": info["title"],
                    "authors": info["authors"],
                    "publication_year": info["publication_year"],
                    "doi": info["doi"],
                    "page_count": info["page_count"],
                    "has_abstract": bool(info.get("abstract")),
                    "extraction_mode": info["extraction_mode"],
                    "is_already_imported": is_duplicate,
                    "duplicate_reason": dup_reason
                })

        return {
            "folder_path": str(folder_path),
            "folder_name": folder_path.name,
            "total_files_scanned": len(discovered_papers) + len(unsupported_files),
            "supported_count": len(discovered_papers),
            "unsupported_count": len(unsupported_files),
            "already_imported_count": already_imported_count,
            "ready_to_import_count": len(discovered_papers) - already_imported_count,
            "discovered_papers": discovered_papers,
            "unsupported_files": unsupported_files[:50]  # Cap list to prevent giant payloads
        }

    def import_selected_files(
        self,
        folder_path_str: str,
        selected_filenames: Optional[List[str]] = None,
        target_collection: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Import selected files from user directory into the PaperGraph workspace.
        Original research files remain completely untouched.
        """
        folder_path = Path(folder_path_str).resolve()
        if not folder_path.exists():
            raise FileNotFoundError(f"Folder not found: {folder_path_str}")

        scan_result = self.scan_directory(folder_path_str)
        all_discovered = scan_result["discovered_papers"]

        # Filter by selected if specified
        if selected_filenames is not None:
            selected_set = set(selected_filenames)
            target_list = [p for p in all_discovered if p["filename"] in selected_set or p["relative_path"] in selected_set]
        else:
            # Default to all non-duplicate files
            target_list = [p for p in all_discovered if not p["is_already_imported"]]

        imported_papers = []
        skipped_count = 0
        error_list = []

        for p_info in target_list:
            fpath = Path(p_info["absolute_path"])
            if not fpath.exists():
                error_list.append(f"File not found: {p_info['filename']}")
                continue

            try:
                # Re-extract full content
                ext = p_info["extension"]
                if ext == ".pdf":
                    full_info = self._extract_pdf_info(fpath)
                elif ext in {".txt", ".md"}:
                    full_info = self._extract_text_info(fpath)
                elif ext == ".json":
                    full_info = self._extract_json_info(fpath)
                else:
                    continue

                # Generate clean ID
                base_id = full_info["doi"] or full_info["title"] or fpath.stem
                paper_id = sanitize_id(f"local_{base_id}")

                # Ensure uniqueness
                paper_dir = self.ws.get_paper_dir(paper_id)
                counter = 1
                orig_paper_id = paper_id
                while paper_dir.exists() and (paper_dir / "paper.json").exists():
                    paper_id = f"{orig_paper_id}_{counter}"
                    paper_dir = self.ws.get_paper_dir(paper_id)
                    counter += 1

                paper_dir.mkdir(parents=True, exist_ok=True)

                # Compute file hash
                fhash = self._compute_file_hash(fpath)

                # Safely copy source file to managed workspace (original remains untouched!)
                dest_source_path = paper_dir / f"source{ext}"
                shutil.copy2(fpath, dest_source_path)

                now_iso = datetime.datetime.now().isoformat()
                collections = ["general"]
                if target_collection and target_collection != "general":
                    collections.append(target_collection)

                # Write paper.json metadata
                metadata_dict = {
                    "id": paper_id,
                    "title": full_info["title"],
                    "authors": full_info["authors"],
                    "publication_year": full_info["publication_year"],
                    "publication_date": str(full_info["publication_year"]) if full_info["publication_year"] else None,
                    "venue": "Local Research Collection",
                    "doi": full_info["doi"],
                    "source_provider": "local_folder",
                    "original_file_path": str(fpath),
                    "file_type": ext,
                    "file_hash": fhash,
                    "has_full_text": bool(full_info.get("full_text") and len(full_info["full_text"]) > 200),
                    "text_extraction_mode": full_info["extraction_mode"],
                    "citation_count": 0,
                    "referenced_works": [],
                    "abstract_available": bool(full_info.get("abstract")),
                    "retrieval_date": now_iso,
                    "processing_status": "Imported",
                    "collections": collections,
                    "stage_history": [
                        {
                            "stage": "Discovery",
                            "status": "Success",
                            "timestamp": now_iso,
                            "details": f"Discovered in local folder: {fpath.name}"
                        },
                        {
                            "stage": "Import",
                            "status": "Success",
                            "timestamp": now_iso,
                            "details": f"Imported with mode: {full_info['extraction_mode']}"
                        }
                    ]
                }

                # Save metadata
                self.ws.save_paper_metadata(paper_id, metadata_dict)

                # Save abstract if available
                if full_info.get("abstract"):
                    atomic_write_text(paper_dir / "abstract.txt", full_info["abstract"])

                # Save full text if extracted
                if full_info.get("full_text"):
                    atomic_write_text(paper_dir / "full_text.txt", full_info["full_text"])

                # Assign collection in workspace manager
                if target_collection:
                    self.ws.add_paper_to_collection(target_collection, paper_id)

                imported_papers.append(metadata_dict)

            except Exception as e:
                error_list.append(f"Error importing {p_info['filename']}: {str(e)}")

        # Rescan workspace index
        self.ws.rebuild_workspace_index()

        return {
            "imported_count": len(imported_papers),
            "skipped_count": skipped_count,
            "errors": error_list,
            "imported_papers": imported_papers
        }

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format bytes into readable KB/MB."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"

folder_import_service = FolderImportService()
