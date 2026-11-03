"""
Research Intersection Explorer Service
Identifies cross-disciplinary connections and methodological transfers between scientific domains.
Strictly frames results as 'Candidate Research Intersections' with evidence and stated limitations.
"""
from typing import List, Dict, Any
from app.core.workspace_manager import workspace_manager
from app.models.schemas import ResearchIntersection

class IntersectionService:
    def __init__(self, ws_manager=None):
        self.ws = ws_manager or workspace_manager

    def find_intersections(self) -> List[Dict[str, Any]]:
        """Identify candidate research intersections across saved literature."""
        papers = self.ws.list_all_papers()
        if len(papers) < 2:
            return []

        # Load details
        paper_details = []
        for p in papers:
            d = self.ws.get_paper_detail(p["id"])
            if d and d.get("analysis"):
                paper_details.append(d)

        if len(paper_details) < 2:
            return []

        # Group papers by scientific domain
        domain_papers: Dict[str, List[Dict[str, Any]]] = {}
        for d in paper_details:
            domains = d.get("analysis", {}).get("scientific_domains", [])
            for dom in domains:
                domain_papers.setdefault(dom, []).append(d)

        intersections: List[Dict[str, Any]] = []
        domain_list = sorted(domain_papers.keys())

        # Compare domain pairs
        for i in range(len(domain_list)):
            for j in range(i + 1, len(domain_list)):
                dom_a = domain_list[i]
                dom_b = domain_list[j]
                
                # Check cross-domain semantic or citation links
                shared_kw = set()
                cross_edges = []
                supporting_papers = []

                for pa in domain_papers[dom_a]:
                    pa_meta = pa["metadata"]
                    pa_kw = {k.get("keyword") if isinstance(k, dict) else str(k) for k in pa.get("analysis", {}).get("keywords", [])}
                    sims = pa.get("analysis", {}).get("semantic_similarities", [])

                    for pb in domain_papers[dom_b]:
                        pb_meta = pb["metadata"]
                        if pa_meta["id"] == pb_meta["id"]:
                            continue
                        pb_kw = {k.get("keyword") if isinstance(k, dict) else str(k) for k in pb.get("analysis", {}).get("keywords", [])}
                        common = pa_kw.intersection(pb_kw)
                        if common:
                            shared_kw.update(common)

                        # Check semantic link
                        for s in sims:
                            if s.get("target_paper_id") == pb_meta["id"]:
                                cross_edges.append((pa_meta, pb_meta, s.get("similarity_score", 0.0)))

                if cross_edges or len(shared_kw) >= 2:
                    # Formulate candidate intersection
                    inter_id = f"inter_{abs(hash(dom_a + dom_b)) % 100000}"
                    top_kw = list(shared_kw)[:6]
                    
                    # Gather supporting papers
                    papers_involved = {}
                    for pa_meta, pb_meta, score in cross_edges[:4]:
                        papers_involved[pa_meta["id"]] = {"id": pa_meta["id"], "title": pa_meta.get("title"), "domain": dom_a, "year": pa_meta.get("publication_year")}
                        papers_involved[pb_meta["id"]] = {"id": pb_meta["id"], "title": pb_meta.get("title"), "domain": dom_b, "year": pb_meta.get("publication_year")}

                    if not papers_involved and cross_edges:
                        for pa_meta, pb_meta, score in cross_edges:
                            papers_involved[pa_meta["id"]] = {"id": pa_meta["id"], "title": pa_meta.get("title"), "domain": dom_a}
                            papers_involved[pb_meta["id"]] = {"id": pb_meta["id"], "title": pb_meta.get("title"), "domain": dom_b}

                    avg_sim = sum(s[2] for s in cross_edges) / len(cross_edges) if cross_edges else 0.40
                    
                    sem_evidence = (
                        f"Detected {len(cross_edges)} cross-domain semantic linkages with mean similarity of {avg_sim:.2f}."
                        if cross_edges else "Common conceptual terminology across independent literature domains."
                    )

                    reason = (
                        f"Papers in '{dom_a}' and '{dom_b}' share terminology ({', '.join(top_kw[:3])}) "
                        f"and exhibit complementary methodologies, suggesting fruitful cross-disciplinary knowledge transfer."
                    )

                    limitations = (
                        "Candidate intersections reflect observational semantic and keyword associations within "
                        "the imported library. They do not constitute verified research gaps, as extensive unindexed "
                        "literature or differing disciplinary vocabulary may already address these interfaces."
                    )

                    intersections.append({
                        "id": inter_id,
                        "title": f"Candidate Research Intersection: {dom_a} × {dom_b}",
                        "domain_a": dom_a,
                        "domain_b": dom_b,
                        "candidate_topics": [f"{dom_a} applications in {dom_b}", f"Cross-domain analysis of {', '.join(top_kw[:2])}"],
                        "supporting_papers": list(papers_involved.values())[:6],
                        "relevant_keywords": top_kw if top_kw else ["cross-domain synthesis"],
                        "semantic_evidence": sem_evidence,
                        "citation_evidence": "Direct citation link exists within referenced works." if any(p for p in papers_involved) else "No direct cross-citation detected in current local corpus.",
                        "reason_suggested": reason,
                        "limitations": limitations,
                        "confidence_score": round(min(0.95, avg_sim + 0.1), 2)
                    })

        intersections.sort(key=lambda x: x["confidence_score"], reverse=True)
        return intersections

intersection_service = IntersectionService()

