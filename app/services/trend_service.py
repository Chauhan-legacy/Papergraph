"""
Research Trend Analytics Service
Analyzes temporal trends, domain distributions, topic growth, and corpus metrics using Pandas.
"""
from typing import Dict, Any, List
import pandas as pd
from app.core.workspace_manager import workspace_manager

class TrendService:
    def __init__(self, ws_manager=None):
        self.ws = ws_manager or workspace_manager

    def compute_trends(self) -> Dict[str, Any]:
        """Aggregate temporal and thematic statistics across research workspace."""
        papers = self.ws.list_all_papers()
        total_count = len(papers)
        warnings = []

        if total_count == 0:
            return {
                "total_analyzed": 0,
                "publications_by_year": {},
                "top_topics": [],
                "top_keywords": [],
                "domain_distributions": [],
                "warnings": ["Research library is currently empty. Import papers to compute trends."]
            }

        if total_count < 5:
            warnings.append(f"Corpus size is limited ({total_count} papers). Statistical patterns are preliminary and may not reflect comprehensive scientific trends.")

        # Extract paper records
        records = []
        all_keywords = []
        all_topics = []
        all_domains = []

        for p in papers:
            year = p.get("publication_year")
            citations = p.get("citation_count", 0)
            records.append({
                "id": p["id"],
                "year": year if year and year > 1900 else None,
                "citations": citations,
                "venue": p.get("venue", "Unknown")
            })

            d = self.ws.get_paper_detail(p["id"])
            if d and d.get("analysis"):
                an = d["analysis"]
                for kw in an.get("keywords", []):
                    k_str = kw.get("keyword") if isinstance(kw, dict) else str(kw)
                    if k_str:
                        all_keywords.append({"keyword": k_str, "year": year})
                for top in an.get("topics", []):
                    if top:
                        all_topics.append({"topic": top, "year": year})
                for dom in an.get("scientific_domains", []):
                    if dom:
                        all_domains.append({"domain": dom, "year": year})

        df_papers = pd.DataFrame(records)

        # 1. Publications by year
        pub_by_year = {}
        if not df_papers.empty and "year" in df_papers.columns:
            valid_years = df_papers["year"].dropna().astype(int)
            if not valid_years.empty:
                year_counts = valid_years.value_counts().sort_index()
                pub_by_year = {str(k): int(v) for k, v in year_counts.items()}

        # 2. Top keywords
        top_kw_list = []
        if all_keywords:
            df_kw = pd.DataFrame(all_keywords)
            kw_counts = df_kw["keyword"].value_counts().head(12)
            top_kw_list = [{"keyword": str(k), "count": int(v)} for k, v in kw_counts.items()]

        # 3. Top topics
        top_topic_list = []
        if all_topics:
            df_top = pd.DataFrame(all_topics)
            top_counts = df_top["topic"].value_counts().head(10)
            top_topic_list = [{"topic": str(k), "count": int(v)} for k, v in top_counts.items()]

        # 4. Domain distribution
        domain_list = []
        if all_domains:
            df_dom = pd.DataFrame(all_domains)
            dom_counts = df_dom["domain"].value_counts().head(8)
            domain_list = [{"domain": str(k), "count": int(v)} for k, v in dom_counts.items()]

        return {
            "total_analyzed": total_count,
            "publications_by_year": pub_by_year,
            "top_topics": top_topic_list,
            "top_keywords": top_kw_list,
            "domain_distributions": domain_list,
            "warnings": warnings
        }

trend_service = TrendService()

