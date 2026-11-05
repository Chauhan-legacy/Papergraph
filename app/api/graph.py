"""
Graph Exploration API Routes
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.services.graph_service import graph_service

router = APIRouter(prefix="/api/graph", tags=["Graph"])

@router.get("")
def get_knowledge_graph(
    collection_id: Optional[str] = None,
    citations: bool = True,
    semantics: bool = True,
    authors: bool = False,
    topics: bool = False,
    methods: bool = False,
    datasets: bool = False,
    min_similarity: float = 0.35,
    max_nodes: int = 300
):
    """Retrieve complete or filtered knowledge graph data for Cytoscape.js."""
    try:
        data = graph_service.build_graph(
            collection_id=collection_id,
            include_citations=citations,
            include_semantics=semantics,
            include_authors=authors,
            include_topics=topics,
            include_methods=methods,
            include_datasets=datasets,
            min_similarity=min_similarity,
            max_nodes=max_nodes
        )
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{paper_id}")
@router.get("/paper/{paper_id}")
def get_paper_ego_graph(paper_id: str, depth: int = 1):
    """Retrieve ego graph centered around a single paper."""
    try:
        return graph_service.get_ego_graph(paper_id=paper_id, depth=depth)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

