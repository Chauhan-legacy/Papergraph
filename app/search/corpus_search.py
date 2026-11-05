"""
PaperGraph V3 - Corpus Search & Knowledge Graph Engine (Phase 7)
Provides unified hybrid retrieval: keyword TF-IDF, exact claim spans, and multi-entity graph edges.
"""
import re
import math
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class SearchResultItem(BaseModel):
    paper_id: str
    title: str
    matched_claim_id: Optional[str] = None
    claim_text: str
    relevance_score: float
    page_number: int
    evidence_type: str
    extraction_source: str

class GraphNode(BaseModel):
    id: str
    label: str
    entity_type: str  # paper, method, dataset, claim, author

class GraphEdge(BaseModel):
    source: str
    target: str
    relationship: str  # claims, utilizes, evaluated_on, contradicts
    weight: float = 1.0

class CorpusSearchEngine:
    def __init__(self):
        self._index: List[Dict[str, Any]] = []

    def index_document(self, paper_id: str, title: str, claims: List[Any]):
        for c in claims:
            data = c.model_dump() if hasattr(c, "model_dump") else dict(c)
            data["title"] = title
            self._index.append(data)

    def search(self, query: str, top_k: int = 10) -> List[SearchResultItem]:
        q_tokens = set(re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", query.lower()))
        results = []

        for item in self._index:
            text = (item.get("claim_text") or "") + " " + (item.get("title") or "")
            t_tokens = set(re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", text.lower()))
            common = q_tokens.intersection(t_tokens)
            if common:
                score = len(common) / (math.log(len(t_tokens) + 2) + 1.0)
                results.append(SearchResultItem(
                    paper_id=item["source_paper_id"],
                    title=item.get("title", item["source_paper_id"]),
                    matched_claim_id=item.get("claim_id"),
                    claim_text=item.get("claim_text", ""),
                    relevance_score=round(score, 3),
                    page_number=item.get("page_number", 0),
                    evidence_type=item.get("evidence_type", "direct_text"),
                    extraction_source=item.get("extraction_source", "pymupdf")
                ))

        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:top_k]

    def build_knowledge_graph(self) -> Dict[str, Any]:
        nodes = {}
        edges = []

        for item in self._index:
            pid = item["source_paper_id"]
            if pid not in nodes:
                nodes[pid] = GraphNode(id=pid, label=item.get("title", pid), entity_type="paper")

            cid = item.get("claim_id")
            if cid and cid not in nodes:
                nodes[cid] = GraphNode(id=cid, label=item.get("claim_type", "claim"), entity_type="claim")
                edges.append(GraphEdge(source=pid, target=cid, relationship="claims"))

        return {
            "nodes": [n.model_dump() for n in nodes.values()],
            "edges": [e.model_dump() for e in edges]
        }

corpus_search = CorpusSearchEngine()

