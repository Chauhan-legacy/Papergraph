"""
Autonomous Multi-Stage Paper Analyzer Pipeline
Implements Stages 2 through 8 with pause/resume/cancellation, error recovery, and atomic persistence.
"""
import time
import datetime
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.core.workspace_manager import workspace_manager
from app.core.progress_manager import progress_manager
from app.core.file_store import atomic_write_json, atomic_write_text
from app.services.abstract_service import AbstractService
from app.services.summary_service import SummaryService
from app.services.keyword_service import KeywordService
from app.services.embedding_service import embedding_service
from app.services.professor_analysis_service import ProfessorAnalysisService
from app.models.schemas import PaperAnalysis, KeywordItem

logger = logging.getLogger("papergraph.analyzer")

class AnalyzerPipeline:
    def __init__(self, ws_manager=None):
        self.ws = ws_manager or workspace_manager
        self.kw_service = KeywordService()

    def run_all(self, paper_ids: Optional[List[str]] = None, force_reanalyze: bool = False):
        """Execute full pipeline across target papers."""
        all_papers = self.ws.list_all_papers()
        if paper_ids:
            target_papers = [p for p in all_papers if p["id"] in paper_ids]
        else:
            # Pick papers that need processing
            if force_reanalyze:
                target_papers = all_papers
            else:
                target_papers = [p for p in all_papers if p.get("processing_status") not in ["Analysis Completed", "Graph Processed"]]

        if not target_papers:
            progress_manager.start(0)
            progress_manager.finish()
            return

        progress_manager.start(len(target_papers))

        for p_meta in target_papers:
            # Check pause
            while progress_manager.is_paused():
                time.sleep(0.5)

            # Check cancel
            if progress_manager.is_interrupted():
                logger.info("Analyzer pipeline was cancelled by user.")
                break

            paper_id = p_meta["id"]
            title = p_meta.get("title", "Untitled")

            try:
                self.process_single_paper(paper_id, force=force_reanalyze)
                progress_manager.record_success(paper_id, title)
            except Exception as e:
                logger.exception(f"Error processing paper {paper_id}: {e}")
                progress_manager.record_failure(paper_id, str(e))
                # Mark paper as Failed
                p_meta["processing_status"] = "Failed"
                p_meta["last_error"] = str(e)
                self.ws.save_paper_metadata(paper_id, p_meta)

        # After processing individual papers, update pairwise semantic & citation relationships across library
        if not progress_manager.is_interrupted():
            try:
                self.update_global_relationships()
            except Exception as e:
                logger.warning(f"Error updating global relationships: {e}")

        progress_manager.finish()

    def process_single_paper(self, paper_id: str, force: bool = False) -> Dict[str, Any]:
        """Run all stages for one paper with state checkpoints."""
        paper_dir = self.ws.get_paper_dir(paper_id)
        if not paper_dir.exists():
            raise FileNotFoundError(f"Paper directory for {paper_id} not found.")

        detail = self.ws.get_paper_detail(paper_id)
        if not detail or not detail.get("metadata"):
            raise ValueError(f"Paper metadata missing for {paper_id}")

        meta = detail["metadata"]
        title = meta.get("title", "Untitled")

        # Check pause & cancel
        if progress_manager.is_interrupted():
            return meta

        # -------------------------------------------------------------
        # Stage 3 — Abstract Processing
        # -------------------------------------------------------------
        progress_manager.update_paper(paper_id, title, "Abstract Processing")
        abstract_text = detail.get("abstract", "")
        if force or not abstract_text or "unavailable" in abstract_text:
            abstract_text = AbstractService.process_and_save_abstract(paper_dir, meta)
            meta["abstract_available"] = bool(abstract_text and "Abstract unavailable" not in abstract_text)
            meta["processing_status"] = "Abstract Processed"
            self.ws.save_paper_metadata(paper_id, meta)

        if progress_manager.is_interrupted():
            return meta

        # Check for full text extracted from local PDF or document
        full_text_path = paper_dir / "full_text.txt"
        full_text = full_text_path.read_text(encoding="utf-8", errors="replace") if full_text_path.exists() else None

        # -------------------------------------------------------------
        # Stage 5 — NLP Analysis (Keywords, Topics, Domains, Embedding)
        # -------------------------------------------------------------
        progress_manager.update_paper(paper_id, title, "NLP Analysis & Embeddings")
        analysis_data = detail.get("analysis", {})
        if force or not analysis_data or not analysis_data.get("keywords"):
            # Extract keywords from combined title, abstract, and full-text sample
            source_content = full_text[:4000] if full_text else abstract_text
            kw_items = self.kw_service.extract_keywords(title, source_content, top_n=8)
            kw_list = [k.keyword for k in kw_items]

            # Extract scientific domains & methods
            combined_text = f"{title}. {abstract_text}"
            if full_text:
                combined_text = f"{title}. {full_text[:3000]}"
            domains = self.kw_service.extract_domains(combined_text)
            methods = self.kw_service.extract_methods(combined_text)
            topics = self.kw_service.extract_topics(kw_items, domains)

            # Compute embedding
            emb_vector, model_name = embedding_service.compute_embedding(combined_text)

            analysis = PaperAnalysis(
                paper_id=paper_id,
                keywords=kw_items,
                topics=topics,
                methods=methods,
                scientific_domains=domains,
                concepts=kw_list[:5],
                embedding=emb_vector,
                embedding_dim=len(emb_vector),
                model_version=model_name,
                processing_timestamp=datetime.datetime.now().isoformat(),
                semantic_similarities=[]
            )
            analysis_dict = analysis.model_dump()
            atomic_write_json(paper_dir / "analysis.json", analysis_dict)
            meta["topics"] = topics
            meta["scientific_domains"] = domains
        else:
            kw_list = [k.get("keyword") if isinstance(k, dict) else str(k) for k in analysis_data.get("keywords", [])]

        if progress_manager.is_interrupted():
            return meta

        # -------------------------------------------------------------
        # Stage 4 — Structured Summary & Professor Analysis
        # -------------------------------------------------------------
        progress_manager.update_paper(paper_id, title, "Structured Summary & Deep Analysis")
        summary_text = detail.get("summary", "")
        if force or not summary_text:
            summary_obj = SummaryService.generate_structured_summary(meta, abstract_text, kw_list, full_text=full_text)
            SummaryService.save_summary(paper_dir, summary_obj, meta)
            meta["processing_status"] = "Summary Generated"
            self.ws.save_paper_metadata(paper_id, meta)

        # Generate / cache Professor Analysis
        try:
            prof_obj = ProfessorAnalysisService.analyze_paper(meta, abstract_text, kw_list, full_text=full_text)
            ProfessorAnalysisService.save_analysis(paper_dir, prof_obj, meta)
        except Exception as e:
            logger.warning(f"Could not generate professor analysis for {paper_id}: {e}")

        # -------------------------------------------------------------
        # Stage 8 — Completion
        # -------------------------------------------------------------
        meta["processing_status"] = "Analysis Completed"
        meta["last_processed_at"] = datetime.datetime.now().isoformat()
        self.ws.save_paper_metadata(paper_id, meta)

        return meta

    def update_global_relationships(self):
        """Update semantic and citation relationships across the entire library."""
        all_papers = self.ws.list_all_papers()
        papers_with_detail = []
        for p in all_papers:
            detail = self.ws.get_paper_detail(p["id"])
            if detail and detail.get("analysis"):
                papers_with_detail.append({
                    "id": p["id"],
                    "metadata": p,
                    "analysis": detail["analysis"]
                })

        # Pairwise semantic similarity edges
        semantic_edges = embedding_service.find_pairwise_similarities(papers_with_detail, threshold=0.35)

        # Map edges to papers
        sim_map: Dict[str, List[Dict[str, Any]]] = {p["id"]: [] for p in papers_with_detail}
        for edge in semantic_edges:
            src, tgt, score = edge["source"], edge["target"], edge["similarity_score"]
            sim_map[src].append({"target_paper_id": tgt, "similarity_score": score, "relationship_type": "semantic"})
            sim_map[tgt].append({"target_paper_id": src, "similarity_score": score, "relationship_type": "semantic"})

        for p_data in papers_with_detail:
            p_id = p_data["id"]
            analysis = p_data["analysis"]
            analysis["semantic_similarities"] = sorted(sim_map.get(p_id, []), key=lambda x: x["similarity_score"], reverse=True)
            p_dir = self.ws.get_paper_dir(p_id)
            atomic_write_json(p_dir / "analysis.json", analysis)

analyzer_pipeline = AnalyzerPipeline()

